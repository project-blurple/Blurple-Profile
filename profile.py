import io
from copy import copy
from datetime import datetime
from functools import partial
from statistics import mean
from typing import Any, Dict, Optional, List

import discord
from discord import *
from discord.ext.commands import *
from discord.app_commands import *
from discord.app_commands.tree import _log

from PIL import Image, ImageDraw

from Designs.key import ROLE_PERMS, MAIN_GUILD
from Objects.Design import load_design_from_json, Design
from Objects.DesignGroup import DesignGroup
from Objects.DesignImage import DesignImage
from Objects.DesignObj import DesignObj
from Objects.DesignText import DesignText
from config import DESIGNS, DEFAULT


def size_anchor(pos, size, anchor):
    px, py = pos
    sx, sy = size

    if "R" in anchor:
        px -= sx
    elif "L" not in anchor:
        px -= sx / 2

    if any(i in anchor for i in ["D", "B"]):
        py -= sy
    elif all(i not in anchor for i in ["T", "U"]):
        py -= sy / 2

    return round(px), round(py)


def text_anchor(anchor):
    parts = list(anchor)
    new = []

    if "L" in parts:
        new.append("l")
    elif "R" in parts:
        new.append("r")
    else:
        new.append("m")

    if any(i in parts for i in ["U", "T"]):
        new.append("a")
    elif any(i in parts for i in ["D", "B"]):
        new.append("d")
    else:
        new.append("m")

    return "".join(new)


class CardImage:
    def __init__(self, mem: Optional[Dict[str, Any]] = None):
        self.size = (1280, 833)
        self.bg = (0, 0, 0, 0)
        self.mem = mem

    def imager(self, design: Design, *, timer=False):
        if timer:
            start = datetime.now()

        card = Image.new('RGBA', self.size, self.bg)
        draw = ImageDraw.Draw(card)

        for i in design.items:
            if not self.perm_check(i):
                continue

            self.paste_object(card, draw, design, i)

        image_file_object = io.BytesIO()
        card.save(image_file_object, format='png')
        image_file_object.seek(0)

        if timer:
            print(f"{round((datetime.now() - start).total_seconds(), 2)}s")

        return image_file_object

    def perm_check(self, i: DesignObj):
        return not i.roles or all(self.role_perm_check(r) for r in i.roles)

    def role_perm_check(self, r: str):
        neg = r.startswith("~")
        r = r.lstrip("~")

        roles = ROLE_PERMS[r]
        if isinstance(roles, int):
            return roles in self.mem["ROLES"] != neg
        else:
            return any(rr in self.mem["ROLES"] for rr in roles) != neg

    def paste_object(self, card: Image, draw: ImageDraw, design: Design, i: DesignObj):
        if isinstance(i, DesignGroup):
            self.paste_group(card, draw, design, i)

        elif isinstance(i, DesignText):
            self.paste_text(draw, design, i)

        elif isinstance(i, DesignImage):
            self.paste_image(card, design, i)

    def paste_text(self, draw: ImageDraw, design: Design, i: DesignText):
        font = design.get_font(i.font, i.size)
        text = i.text.format(**self.mem)
        if i.max_width:
            length = font.getlength(text)
            if length > i.max_width:
                i.size = round(i.size * i.max_width / length)
                font = design.get_font(i.font, i.size)

        # xy = size_anchor(i.pos, ts, i.anchor)
        draw.text(xy=i.pos, anchor=text_anchor(i.anchor), text=text, font=font, fill=i.color)

    def paste_image(self, card: Image, design: Design, i: DesignImage):
        if i.image == "PFP":
            if not self.mem['AVATAR']:
                return
            image = Image.open(io.BytesIO(self.mem['AVATAR']))
            maxsize = max(m if m else 0 for m in [i.max_width, i.max_height])
            if image.size[0] < maxsize:
                image = image.resize((maxsize, maxsize))
        else:
            image = Image.open(design.path(i))

        image = image.convert("RGBA")

        size = copy(image.size)
        if i.max_width or i.max_height:
            if i.max_width and i.max_width < size[0]:
                size = (i.max_width, size[1] * i.max_width / size[0])
            if i.max_height and i.max_height < size[1]:
                size = (size[0] * i.max_height / size[1], i.max_height)
            size = (round(size[0]), round(size[1]))

            image = image.resize(size)

        if i.mask:
            mask = Image.open(design.path(i.mask)).convert("RGBA")
        else:
            mask = image

        xy = size_anchor(i.pos, size, i.anchor)
        card.paste(image.convert("RGB"), xy, mask)

    def paste_group(self, card: Image, draw: ImageDraw, design: Design, i: DesignGroup):
        queue = copy(i.queue)
        gx, gy = i.pos
        final = []

        contents = [c for c in i.contents if self.perm_check(c)]

        if contents:
            a = text_anchor(i.anchor)
            poss = queue[:len(contents)]
            span = [mean(i[0] for i in poss), mean(i[1] for i in poss)]
            if not any(i in a for i in ['l', 'r']):
                gx -= int(span[0])
            if not any(i in a for i in ['a', 'd']):
                gy -= int(span[1])

            for obj in contents:
                try:
                    xyz = queue.pop(0)
                    obj.pos = (gx + xyz[0], gy + xyz[1])
                    obj.layer = xyz[2] if len(xyz) == 3 else -1
                    obj.anchor = i.anchor
                except IndexError as e:
                    print("Not enough positions in the queue for all the group items")
                    raise e

                final.append(obj)

            final.sort(key=lambda x: x.layer)

            for obj in final:
                self.paste_object(card, draw, design, obj)


class ProfileCog(Cog, name="Profile"):
    """Profile commands"""

    def __init__(self, bot):
        self.bot: Bot = bot

        self.bot.tree.on_error = self.on_app_command_error

        self.bot.designs = {}
        self.load_designs()

    def load_designs(self):
        for d in DESIGNS:
            design = load_design_from_json(f"Designs/{d}.json", "Designs")
            self.bot.designs[design.folder_path] = design

    async def on_app_command_error(self, interaction: Interaction, error: AppCommandError):
        # if isinstance(error, app_commands.errors.CheckFailure):
        #     if await self.validguild(interaction):
        #         return await interaction.response.send_message(
        #             f"You need to be a <@&{(await self.fetchguildinfo(interaction.guild_id))['manager_role_id'][0]}> "
        #             f"to do that!",
        #             ephemeral=True)
        #     else:
        #         return await interaction.response.send_message(f"This command is not available here!", ephemeral=True)

        await interaction.followup.send("Something broke!")
        _log.error('Ignoring exception in command %r', interaction.command.name, exc_info=error)

    @app_commands.command(name="profile")
    @app_commands.describe(user="User to view profile")
    async def profile(self, interaction: discord.Interaction, user: discord.User = None):
        """Your Project Blurple profile card"""

        await interaction.response.defer()

        self.load_designs()

        user = interaction.user if user is None else user
        mem = self.bot.get_guild(MAIN_GUILD).get_member(user.id)

        if not mem:
            if user.id == interaction.user.id:
                await interaction.followup.send("You haven't joined the main server!", ephemeral=True)
            else:
                await interaction.followup.send(f"{user.name} hasn't joined the main server!", ephemeral=True)
            return

        # try:
        #     joined = mem.joined_at.strftime("%#d %B, %Y")
        # except ValueError:
        #     joined = mem.joined_at.strftime("%-d %B, %Y")
        joined = mem.joined_at

        info = {
            "USERNAME": mem.name,
            "DISCRIMINATOR": mem.discriminator,
            "NICKNAME": mem.nick if mem.nick else "",
            "AVATAR": await mem.display_avatar.read() if mem.display_avatar else None,
            "ROLES": [i.id for i in mem.roles],
            "JOINED": joined
        }

        fn = partial(CardImage(info).imager, self.bot.designs[DEFAULT])
        final_buffer = await self.bot.loop.run_in_executor(None, fn)

        f = discord.File(filename="Profile.png", fp=final_buffer)

        await interaction.followup.send(file=f)


async def setup(bot):
    await bot.add_cog(ProfileCog(bot))
