from Objects.DesignObj import DesignObj


class DesignImage(DesignObj):
    def __init__(self, *, image: str, mask:str = None, **kwargs):
        super().__init__(**kwargs)
        self.image: str = image
        self.mask: str = mask
