import os

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from wallpaper_maker.modules.logger import logger


class EffectCreator:
    """Create individual effect temporaries for a wallpaper using a switch dispatch pattern."""

    walfile: str
    walname: str
    walsize: tuple[int, int]
    effect: str
    output_path: str

    switch = {
        "blurred": "create_blurred",
        "blurred_dark": "create_blurred_dark",
        "blurred_darker": "create_blurred_darker",
        "brightened": "create_brightened",
        "flipped": "create_flipped",
        "negated": "create_negated",
        "pixelated": "create_pixelated",
    }

    def __init__(self, walfile: str, walname: str, walsize: tuple[int, int], effect: str, tempdir: str):
        self.walfile = walfile
        self.walname = walname
        self.walsize = walsize
        self.effect = effect
        self.output_path = os.path.join(tempdir, f"{effect}_{walname}.jpg")

    def execute(self) -> tuple[str, str]:
        """Execute the effect creation and return the output path."""
        if os.path.exists(self.output_path):
            return self.output_path, self.effect

        # Get method name from switch dict
        method_name = self.switch.get(self.effect)
        if method_name:
            method = getattr(self, method_name)
            method()

        return self.output_path, self.effect

    def create_blurred(self):
        """Create Gaussian blurred version."""
        wal = Image.open(self.walfile)
        blurred = wal.filter(filter=ImageFilter.GaussianBlur(radius=20))
        blurred.save(self.output_path, format="JPEG", subsampling=0, quality=100)
        logger.info("created effect", extra={"wallpaper": self.walname, "effect": self.effect, "output": self.output_path})
        blurred.close()
        wal.close()

    def create_blurred_dark(self):
        """Create blurred + darkened (0.8) with downscale optimization."""
        wal = Image.open(self.walfile)
        small = wal.resize((wal.width // 4, wal.height // 4), Image.Resampling.LANCZOS)
        blurred_small = small.filter(filter=ImageFilter.GaussianBlur(radius=20))
        blurred_dark = blurred_small.resize(wal.size, Image.Resampling.LANCZOS)
        darkened80 = ImageEnhance.Brightness(blurred_dark)
        blurred_dark = darkened80.enhance(factor=0.8)
        blurred_dark.save(self.output_path, format="JPEG", subsampling=0, quality=100)
        logger.info("created effect", extra={"wallpaper": self.walname, "effect": self.effect, "output": self.output_path})
        blurred_dark.close()
        small.close()
        blurred_small.close()
        wal.close()

    def create_blurred_darker(self):
        """Create blurred + heavily darkened (0.4) with downscale optimization."""
        wal = Image.open(self.walfile)
        small = wal.resize((wal.width // 4, wal.height // 4), Image.Resampling.LANCZOS)
        blurred_small = small.filter(filter=ImageFilter.GaussianBlur(radius=20))
        blurred_darker = blurred_small.resize(wal.size, Image.Resampling.LANCZOS)
        darkened40 = ImageEnhance.Brightness(blurred_darker)
        blurred_darker = darkened40.enhance(factor=0.4)
        blurred_darker.save(self.output_path, format="JPEG", subsampling=0, quality=100)
        logger.info("created effect", extra={"wallpaper": self.walname, "effect": self.effect, "output": self.output_path})
        blurred_darker.close()
        small.close()
        blurred_small.close()
        wal.close()

    def create_brightened(self):
        """Create brightened version (1.1x)."""
        wal = Image.open(self.walfile)
        brightened = ImageEnhance.Brightness(wal)
        brightened = brightened.enhance(factor=1.1)
        brightened.save(self.output_path, format="JPEG", subsampling=0, quality=100)
        logger.info("created effect", extra={"wallpaper": self.walname, "effect": self.effect, "output": self.output_path})
        brightened.close()
        wal.close()

    def create_negated(self):
        """Create inverted/negated version."""
        wal = Image.open(self.walfile)
        negated = ImageOps.invert(wal)
        negated.save(self.output_path, format="JPEG", subsampling=0, quality=100)
        logger.info("created effect", extra={"wallpaper": self.walname, "effect": self.effect, "output": self.output_path})
        negated.close()
        wal.close()

    def create_flipped(self):
        """Create vertically flipped version."""
        wal = Image.open(self.walfile)
        flipped = wal.transpose(method=Image.Transpose.FLIP_TOP_BOTTOM)
        flipped.save(self.output_path, format="JPEG", subsampling=0, quality=100)
        logger.info("created effect", extra={"wallpaper": self.walname, "effect": self.effect, "output": self.output_path})
        flipped.close()
        wal.close()

    def create_pixelated(self):
        """Create pixelated version."""
        wal = Image.open(self.walfile)
        small = wal.resize((int(wal.width * 0.01), int(wal.height * 0.01)), Image.Resampling.BICUBIC)
        darkenedsmall = ImageEnhance.Brightness(small)
        darksmall = darkenedsmall.enhance(factor=0.8)
        pixelated = darksmall.resize(wal.size, Image.Resampling.NEAREST)
        pixelated.save(self.output_path, format="JPEG", subsampling=0, quality=100)
        logger.info("created effect", extra={"wallpaper": self.walname, "effect": self.effect, "output": self.output_path})
        small.close()
        darksmall.close()
        pixelated.close()
        wal.close()
