import sys
import traceback
from typing import *

import discord
from discord.ext import commands
from discord.ext.commands import *
from discord.client import _log


class OwnerCog(commands.Cog, name="Owner"):
    """Owner commands"""

    def __init__(self, bot):
        self.bot = bot
        self.bot.recentcog = None

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.command()
    async def shutdown(self, ctx):
        """Shuts down the bot"""
        try:
            await ctx.reply("Shutting down...")
        except discord.Forbidden:
            await ctx.author.send("Shutting down...")

        print(f"Shutting down...")
        print(discord.utils.utcnow().strftime("%d/%m/%Y %I:%M:%S:%f"))

        await self.bot.close()

    @commands.group(name="cogs", aliases=["cog"])
    async def cogs(self, ctx):
        """Cog management"""
        return

    @cogs.command(name='load')
    async def load_cog(self, ctx, *, cog: str):
        """Loads cog. Remember to use dot path. e.g: cogs.owner"""
        try:
            await self.bot.load_extension(cog)
        except Exception as e:
            return await ctx.send(f'**ERROR:** {type(e).__name__} - {e}')
        else:
            await ctx.send(f'Successfully loaded `{cog}`.')
        print('---')
        print(f'{cog} was loaded.')
        print('---')

    @cogs.command(name='unload')
    async def unload_cog(self, ctx, *, cog: str):
        """Unloads cog. Remember to use dot path. e.g: cogs.owner"""
        try:
            await self.cancel_tasks(cog)
            await self.bot.unload_extension(cog)
        except Exception as e:
            return await ctx.send(f'**ERROR:** {type(e).__name__} - {e}')
        else:
            await ctx.send(f'Successfully unloaded `{cog}`.')
        print('---')
        print(f'{cog} was unloaded.')
        print('---')

    @cogs.command(name='reload')
    async def reload_cog(self, ctx, *, cog: str):
        """Reloads cog. Remember to use dot path. e.g: cogs.owner"""
        try:
            await self.cancel_tasks(cog)
            await self.bot.reload_extension(cog)
        except Exception as e:
            return await ctx.send(f'**ERROR:** {type(e).__name__} - {e}')
        else:
            await ctx.send(f'Successfully reloaded `{cog}`.')
        self.bot.recentcog = cog
        print('---')
        print(f'{cog} was reloaded.')
        print('---')

    @commands.command(hidden=True, aliases=['crr'])
    async def recent_cog_reload(self, ctx):
        """Reloads most recent reloaded cog"""
        if not self.bot.recentcog: return await ctx.send("You haven't recently reloaded any cogs.")

        return await ctx.invoke(self.reload_cog, cog=self.bot.recentcog)

    @commands.command()
    @commands.guild_only()
    async def sync(self, ctx: Context, guilds: Greedy[discord.Object],
                   spec: Optional[Literal["~", "*", "^"]] = None) -> None:
        """
        Works like:
        !sync -> global sync
        !sync ~ -> sync current guild
        !sync * -> copies all global app commands to current guild and syncs
        !sync ^ -> clears all commands from the current guild target and syncs (removes guild commands)
        !sync id_1 id_2 -> syncs guilds with id 1 and 2
        """
        if not guilds:
            try:
                if spec == "~":
                    synced = await ctx.bot.tree.sync(guild=ctx.guild)
                elif spec == "*":
                    ctx.bot.tree.copy_global_to(guild=ctx.guild)
                    synced = await ctx.bot.tree.sync(guild=ctx.guild)
                elif spec == "^":
                    ctx.bot.tree.clear_commands(guild=ctx.guild)
                    await ctx.bot.tree.sync(guild=ctx.guild)
                    synced = []
                else:
                    synced = await ctx.bot.tree.sync()

                await ctx.send(
                    f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
                )
                return
            except Exception as e:
                traceback.print_exc()
                await ctx.send("Something went wrong!")

        ret = 0
        for guild in guilds:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

        await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")

    async def cancel_tasks(self, name):
        async def canceller(self, x):
            try:
                self.bot.tasks[x].cancel()
            except Exception:
                pass

        if name == 'cogs.comics':
            await canceller(self, 'releases')

        if name == 'cogs.polls':
            for x in ['starts', 'ends']:
                for k, v in self.bot.tasks['poll_schedules'][x].items():
                    try:
                        v.cancel()
                    except Exception:
                        pass

        if name == 'funcs.postgresql':
            try:
                await self.bot.db.close()
            except Exception:
                print("Couldn't close PostgreSQL connection")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        ignored = (commands.CommandNotFound, commands.UserInputError)
        if isinstance(error, ignored):
            return

        traceback.print_exception(
            type(error), error, error.__traceback__, file=sys.stderr)
        _log.error('Ignoring exception in command %r', error.command.name, exc_info=error)


async def setup(bot):
    await bot.add_cog(OwnerCog(bot))
