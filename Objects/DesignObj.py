from typing import Tuple, List, Union, Optional


class DesignObj:
    def __init__(self, *, pos: Tuple[int, int], max_height: int = None, max_width: int = None, layer: int, anchor: str,
                 roles: List[Union[str, int]] = None, group = None,
                 group_layer: Optional[int] = None):
        self.pos: Tuple[int, int] = pos
        self.layer: int = layer
        self.anchor: str = anchor
        self.roles: List[Union[str, int]] = roles
        self.max_height: int = max_height
        self.max_width: int = max_width
        self.group = group
        self.group_layer: Optional[int] = group_layer
