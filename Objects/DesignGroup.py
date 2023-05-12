from typing import List, Tuple

from Objects.DesignObj import DesignObj


class DesignGroup(DesignObj):
    def __init__(self, *, name: str, queue: List[Tuple[int, int]], **kwargs):
        super().__init__(**kwargs)
        self.name: str = name
        self.queue: List[Tuple[int, int]] = queue
        self.contents: List[DesignObj] = []

    def add_item(self, item: DesignObj):
        self.contents.append(item)

    def sort(self):
        self.contents.sort(key=lambda x: x.group_layer if x.group_layer else -1)
