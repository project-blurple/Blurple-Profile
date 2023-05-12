import json
from typing import Tuple, List, Union, Optional, Dict

from PIL.ImageFont import truetype

from Objects.DesignGroup import DesignGroup
from Objects.DesignImage import DesignImage
from Objects.DesignObj import DesignObj
from Objects.DesignText import DesignText


def load_design_from_json(file_path, trail=None):
    with open(file_path) as f:
        data = json.load(f)

    if trail:
        data['info']['folder_path'] = f"{trail}/{data['info']['folder_path']}"
    d = Design(**data['info'])

    d.font_paths = data['fonts']
    d.fonts = {k: {} for k in data['fonts']}

    groupsdata = data['objects']['groups']
    groups = {}
    while True:
        if not groupsdata:
            break
        g = next(i for i in groupsdata if 'group' not in i or i['group'] in groups)
        groupsdata.remove(g)
        gr = d.add_group(**g)
        groups[gr.name] = gr
    d.groups = groups

    for t in data['objects']['text']:
        if isinstance(t['color'], str):
            t['color'] = data['colors'][t['color']]
        d.add_text(**t)

    for t in data['objects']['images']:
        d.add_image(**t)

    d.sort_items()
    for g in d.groups.values():
        g.sort()

    return d


class Design:
    def __init__(self, *, name: str, default_layer: int = 10, folder_path: str):
        self.name: str = name
        self.default_layer: int = default_layer
        self.folder_path: str = folder_path

        self.default_pos = (0, 0)
        self.default_anchor = ""

        self.fonts = {}
        self.font_paths = {}
        self.groups: Dict[str, DesignGroup] = {}
        self.items: List[DesignObj] = []

    def defaults(self, pos, layer, anchor):
        if anchor is None:
            if pos is not None:
                anchor = self.default_anchor
            else:
                anchor = "UL"
        if pos is None:
            pos = self.default_pos
        if layer is None:
            layer = self.default_layer
        return pos, layer, anchor

    def sort_items(self):
        self.items.sort(key=lambda x: x.layer)

    def path(self, obj: Union[DesignObj, str]):
        if isinstance(obj, str):
            p = obj
        elif isinstance(obj, DesignImage):
            p = obj.image
        return f"{self.folder_path}/{p}"

    def get_font(self, name: str, size: int):
        if size not in self.fonts[name]:
            self.fonts[name][size] = truetype(self.path(self.font_paths[name]), size)
        return self.fonts[name][size]

    def add_text(self, *, text: str, font: str, size: int, max_height: int = None, max_width: int = None,
                 color: List[float], pos: Tuple[int, int] = None, anchor: str = None, layer: int = None,
                 roles: List[Union[str, int]] = None, group: Optional[str] = None, group_layer: Optional[int] = None):
        pos, layer, anchor = self.defaults(pos, layer, anchor)

        color = tuple[float, float, float, float](color)

        if group:
            group = self.groups[group]

        new_text = DesignText(text=text, font=font, size=size, max_height=max_height, max_width=max_width, color=color,
                              pos=pos, anchor=anchor, layer=layer, roles=roles, group=group, group_layer=group_layer)

        if not group:
            self.items.append(new_text)
        else:
            group.add_item(new_text)

        return new_text

    def add_image(self, *, image: str, max_height: int = None, max_width: int = None, pos: Tuple[int, int] = None,
                  anchor: str = None, layer: int = None, roles: List[Union[str, int]] = None,
                  group: Optional[str] = None, group_layer: Optional[int] = None, mask: str = None):
        pos, layer, anchor = self.defaults(pos, layer, anchor)

        if group:
            group = self.groups[group]

        new_image = DesignImage(image=image, max_height=max_height, max_width=max_width, pos=pos, anchor=anchor,
                                layer=layer, roles=roles, group=group, group_layer=group_layer, mask=mask)

        if not group:
            self.items.append(new_image)
        else:
            group.add_item(new_image)

        return new_image

    def add_group(self, *, name: str, queue: List[Tuple[int, int]], max_height: int = None, max_width: int = None,
                  pos: Tuple[int, int] = None, anchor: str = None, layer: int = None,
                  roles: List[Union[str, int]] = None, group: Optional[str] = None, group_layer: Optional[int] = None):
        pos, layer, anchor = self.defaults(pos, layer, anchor)

        if group:
            group = self.groups[group]

        new_group = DesignGroup(name=name, queue=queue, max_height=max_height, max_width=max_width, pos=pos,
                                anchor=anchor, layer=layer, roles=roles, group=group, group_layer=group_layer)
        self.items.append(new_group)
        return new_group
