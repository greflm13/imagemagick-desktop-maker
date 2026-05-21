import os

from PIL import Image, ImageChops, ImageFile

from wallpaper_maker.modules.logger import logger
from wallpaper_maker.modules.util import TempImagePointers


class Render:
    tempimages: TempImagePointers
    style: str
    out: str
    color: str | None = None
    img: Image.Image | ImageFile.ImageFile | None = None

    switch = {
        "Blur": "blur",
        "Flip": "flip",
        "InverseBlur": "inverse_blur",
        "InverseBlurDarker": "inverse_blur_darker",
        "InverseNegate": "inverse_negate",
        "InversePixelate": "inverse_pixelate",
        "LogoColors": "logo_colors",
        "Negate": "negate",
        "Pixelate": "pixelate",
        "ThroughBlack": "through_black",
    }

    def __init__(self, tempimages: TempImagePointers, style: str, out: str, color: str, selected_colors: dict[str, str]):
        self.tempimages = tempimages
        self.style = style
        self.out = out
        self.color = selected_colors.get(color, None)

        for col in selected_colors.keys():
            self.switch[f"ColorOverlay/{col}"] = "color_overlay"
            self.switch[f"ColorOverlayBlur/{col}"] = "color_overlay_blur"
            self.switch[f"ColorThrough/{col}"] = "color_through"

    def through_black(self):
        mask = Image.open(self.tempimages.mask)
        wal = Image.open(self.tempimages.wal)
        thrubl_image = Image.new("RGB", (wal.width, wal.height))
        thrubl_image.paste(wal, mask=mask)
        self.img = thrubl_image
        logger.info("rendered image", extra={"style": self.style, "mask": self.tempimages.mask})

    def blur(self):
        mask = Image.open(self.tempimages.mask)
        shadow = Image.open(self.tempimages.shadow)
        blurred_dark = Image.open(self.tempimages.blurred_dark)
        brightened = Image.open(self.tempimages.brightened)
        blurred_image = ImageChops.multiply(blurred_dark, shadow)
        blurred_image.paste(brightened, mask=mask)
        self.img = blurred_image
        logger.info("rendered image", extra={"style": self.style, "mask": self.tempimages.mask})

    def inverse_blur(self):
        mask = Image.open(self.tempimages.mask)
        shadow = Image.open(self.tempimages.shadow)
        wal = Image.open(self.tempimages.wal)
        blurred_dark = Image.open(self.tempimages.blurred_dark)
        invblur = ImageChops.multiply(wal, shadow)
        invblur.paste(blurred_dark, mask=mask)
        self.img = invblur
        logger.info("rendered image", extra={"style": self.style, "mask": self.tempimages.mask})

    def inverse_blur_darker(self):
        mask = Image.open(self.tempimages.mask)
        shadow = Image.open(self.tempimages.shadow)
        wal = Image.open(self.tempimages.wal)
        blurred_darker = Image.open(self.tempimages.blurred_darker)
        inblda_image = ImageChops.multiply(wal, shadow)
        inblda_image.paste(blurred_darker, mask=mask)
        self.img = inblda_image
        logger.info("rendered image", extra={"style": self.style, "mask": self.tempimages.mask})

    def negate(self):
        mask = Image.open(self.tempimages.mask)
        negated = Image.open(self.tempimages.negated)
        neg = Image.open(self.tempimages.wal)
        neg.paste(negated, mask=mask)
        self.img = neg
        logger.info("rendered image", extra={"style": self.style, "mask": self.tempimages.mask})

    def inverse_negate(self):
        mask = Image.open(self.tempimages.mask)
        wal = Image.open(self.tempimages.wal)
        invneg = Image.open(self.tempimages.negated)
        invneg.paste(wal, mask=mask)
        self.img = invneg
        logger.info("rendered image", extra={"style": self.style, "mask": self.tempimages.mask})

    def flip(self):
        mask = Image.open(self.tempimages.mask)
        shadow = Image.open(self.tempimages.shadow)
        wal = Image.open(self.tempimages.wal)
        flipped = Image.open(self.tempimages.flipped)
        flipimg = ImageChops.multiply(wal, shadow)
        flipimg.paste(flipped, mask=mask)
        self.img = flipimg
        logger.info("rendered image", extra={"style": self.style, "mask": self.tempimages.mask})

    def color_overlay(self):
        mask = Image.open(self.tempimages.mask)
        shadow = Image.open(self.tempimages.shadow)
        wal = Image.open(self.tempimages.wal)
        cover = ImageChops.multiply(wal, shadow)
        cover.paste(Image.new("RGB", wal.size, self.color), mask=mask)
        self.img = cover
        logger.info("rendered image", extra={"style": self.style, "mask": self.tempimages.mask})

    def color_overlay_blur(self):
        mask = Image.open(self.tempimages.mask)
        shadow = Image.open(self.tempimages.shadow)
        wal = Image.open(self.tempimages.blurred)
        cover = ImageChops.multiply(wal, shadow)
        cover.paste(Image.new("RGB", wal.size, self.color), mask=mask)
        self.img = cover
        logger.info("rendered image", extra={"style": self.style, "mask": self.tempimages.mask})

    def color_through(self):
        mask = Image.open(self.tempimages.mask)
        wal = Image.open(self.tempimages.wal)
        trans = mask.convert("L")
        data = mask.getdata(3)
        trans.putdata([max(item, 127) for item in data])
        mask.putalpha(trans)
        cover = Image.composite(wal, Image.new("RGB", wal.size, self.color), mask)
        self.img = cover
        logger.info("rendered image", extra={"style": self.style, "mask": self.tempimages.mask})

    def pixelate(self):
        mask = Image.open(self.tempimages.mask)
        wal = Image.open(self.tempimages.wal)
        pix = Image.open(self.tempimages.pixelated)
        pix.paste(wal, mask=mask)
        self.img = pix
        logger.info("rendered image", extra={"style": self.style, "mask": self.tempimages.mask})

    def inverse_pixelate(self):
        mask = Image.open(self.tempimages.mask)
        wal = Image.open(self.tempimages.wal)
        pix = Image.open(self.tempimages.pixelated)
        wal.paste(pix, mask=mask)
        self.img = wal
        logger.info("rendered image", extra={"style": self.style, "mask": self.tempimages.mask})

    def logo_colors(self):
        logocolored = Image.open(self.tempimages.logocolored)
        mask = Image.open(self.tempimages.mask)
        wal = Image.open(self.tempimages.wal)
        wal.paste(logocolored, mask=mask)
        self.img = wal
        logger.info("rendered image", extra={"style": self.style, "mask": self.tempimages.mask})

    def render(self):
        if not os.path.exists(self.out):
            do = self.switch.get(self.style, "")
            if hasattr(self, do) and callable(func := getattr(self, do)):
                func()
                if isinstance(self.img, Image.Image) or isinstance(self.img, ImageFile.ImageFile):
                    self.img.save(self.out, format="JPEG", subsampling=2, quality=95, optimize=True)
                    logger.info("saved rendered image", extra={"style": self.style, "out": self.out})
