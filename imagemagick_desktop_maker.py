#!/usr/bin/env python3
import os
import shutil
import argparse
from multiprocessing import Pool
import tempfile
from io import BytesIO
import cairosvg
from tqdm.auto import tqdm
from PIL import Image, ImageFile, ImageFilter, ImageChops, ImageEnhance, ImageOps
from rich_argparse import RichHelpFormatter, HelpPreviewAction

SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))
SVGDIR = os.path.join(SCRIPTDIR, "Svgs")
WALLPAPERDIR = os.path.join(SCRIPTDIR, "Wallpapers")
OUTDIR = os.path.join(SCRIPTDIR, "Render")
TEMPDIR = tempfile.mkdtemp()
STYLES = [
    "Blur",
    "Flip",
    "InverseBlur",
    "InverseBlurDarker",
    "InverseNegate",
    "InversePixelate",
    "Negate",
    "Pixelate",
    "ThroughBlack",
]

NEED_BLUR = "OverlayBlur"
NEED_BLUR_DARK = set(["Blur", "InverseBlur"])
NEED_BLUR_DARKER = set(["InverseBlurDarker"])
NEED_BRIGHTENED = set(["Blur"])
NEED_FLIP = set(["Flip"])
NEED_NEGATE = set(["InverseNegate", "Negate"])
NEED_PIXELATE = set(["InversePixelate", "Pixelate"])

COLORS = {
    "AerospaceOrange": "#FD5000",
    "AmaranthPurple": "#AC1361",
    "Amethyst": "#9B5DE5",
    "AnexiaBlue": "#003CA6",
    "Aquamarine": "#00F5D4",
    "ArchBlue": "#0F94D2",
    "Black": "#000000",
    "BrilliantRose": "#F15BB5",
    "CambridgeBlue": "#7DA27F",
    "DebianRed": "#A80030",
    "DeepSkyBlue": "#00BBF9",
    "EndeavourPurple": "#7E3EBE",
    "FedoraBlue": "#51A2DA",
    "Lion": "#AD9667",
    "Maize": "#FEE440",
    "ManjaroGreen": "#35BFA4",
    "MidnightGreen": "#115E6B",
    "MintGreen": "#69B53F",
    "Sapphire": "#004EAA",
    "SelectiveYellow": "#FFB92A",
    "SovietRed": "#CC0000",
    "SuseGreen": "#30BA78",
    "Tekhelet": "#592B8A",
    "UbuntuOrange": "#E95420",
    "White": "#FFFFFF",
}


class Args:
    svgdir: str
    wallpaperdir: str
    outdir: str


class TempImagePointers:
    blurred: str
    blurred_dark: str
    blurred_darker: str
    brightened: str
    flipped: str
    mask: str
    negated: str
    pixelated: str
    shadow: str
    wal: str


class TempMaskPointers:
    mask: str
    maskname: str
    shadow: str
    size: tuple[int, int]


class TempEffectPointers:
    blurred: str
    blurred_dark: str
    blurred_darker: str
    brightened: str
    flipped: str
    negated: str
    pixelated: str
    wal: str
    walfile: str
    walname: str
    size: tuple[int, int]


class Render:
    tempimages: TempImagePointers
    style: str
    out: str
    color: str

    switch = {
        "Blur": "blur",
        "Flip": "flip",
        "InverseBlur": "inverse_blur",
        "InverseBlurDarker": "inverse_blur_darker",
        "InverseNegate": "inverse_negate",
        "InversePixelate": "inverse_pixelate",
        "Negate": "negate",
        "Pixelate": "pixelate",
        "ThroughBlack": "through_black",
    }

    def __init__(self, tempimages: TempImagePointers, style: str, out: str, color: str | None = None):
        self.tempimages = tempimages
        self.style = style
        self.out = out
        self.color = color

        for col in COLORS.keys():
            self.switch[f"ColorOverlay/{col}"] = "color_overlay"
            self.switch[f"ColorOverlayBlur/{col}"] = "color_overlay_blur"
            self.switch[f"ColorThrough/{col}"] = "color_through"

    def through_black(self):
        if not os.path.exists(self.out):
            mask = Image.open(self.tempimages.mask)
            wal = Image.open(self.tempimages.wal)
            thrubl_image = Image.new("RGB", (wal.width, wal.height))
            thrubl_image.paste(wal, mask=mask)
            thrubl_image.save(self.out, format="JPEG", subsampling=0, quality=100)

    def blur(self):
        if not os.path.exists(self.out):
            mask = Image.open(self.tempimages.mask)
            shadow = Image.open(self.tempimages.shadow)
            blurred_dark = Image.open(self.tempimages.blurred_dark)
            brightened = Image.open(self.tempimages.brightened)
            blurred_image = ImageChops.multiply(blurred_dark, shadow)
            blurred_image.paste(brightened, mask=mask)
            blurred_image.save(self.out, format="JPEG", subsampling=0, quality=100)

    def inverse_blur(self):
        if not os.path.exists(self.out):
            mask = Image.open(self.tempimages.mask)
            shadow = Image.open(self.tempimages.shadow)
            wal = Image.open(self.tempimages.wal)
            blurred_dark = Image.open(self.tempimages.blurred_dark)
            invblur = ImageChops.multiply(wal, shadow)
            invblur.paste(blurred_dark, mask=mask)
            invblur.save(self.out, format="JPEG", subsampling=0, quality=100)

    def inverse_blur_darker(self):
        if not os.path.exists(self.out):
            mask = Image.open(self.tempimages.mask)
            shadow = Image.open(self.tempimages.shadow)
            wal = Image.open(self.tempimages.wal)
            blurred_darker = Image.open(self.tempimages.blurred_darker)
            inblda_image = ImageChops.multiply(wal, shadow)
            inblda_image.paste(blurred_darker, mask=mask)
            inblda_image.save(self.out, format="JPEG", subsampling=0, quality=100)

    def negate(self):
        if not os.path.exists(self.out):
            mask = Image.open(self.tempimages.mask)
            negated = Image.open(self.tempimages.negated)
            neg = Image.open(self.tempimages.wal)
            neg.paste(negated, mask=mask)
            neg.save(self.out, format="JPEG", subsampling=0, quality=100)

    def inverse_negate(self):
        if not os.path.exists(self.out):
            mask = Image.open(self.tempimages.mask)
            wal = Image.open(self.tempimages.wal)
            invneg = Image.open(self.tempimages.negated)
            invneg.paste(wal, mask=mask)
            invneg.save(self.out, format="JPEG", subsampling=0, quality=100)

    def flip(self):
        if not os.path.exists(self.out):
            mask = Image.open(self.tempimages.mask)
            shadow = Image.open(self.tempimages.shadow)
            wal = Image.open(self.tempimages.wal)
            flipped = Image.open(self.tempimages.flipped)
            flipimg = ImageChops.multiply(wal, shadow)
            flipimg.paste(flipped, mask=mask)
            flipimg.save(self.out, format="JPEG", subsampling=0, quality=100)

    def color_overlay(self):
        if not os.path.exists(self.out):
            mask = Image.open(self.tempimages.mask)
            shadow = Image.open(self.tempimages.shadow)
            wal = Image.open(self.tempimages.wal)
            cover = ImageChops.multiply(wal, shadow)
            cover.paste(Image.new("RGB", wal.size, self.color), mask=mask)
            cover.save(self.out, format="JPEG", subsampling=0, quality=100)

    def color_overlay_blur(self):
        if not os.path.exists(self.out):
            mask = Image.open(self.tempimages.mask)
            shadow = Image.open(self.tempimages.shadow)
            wal = Image.open(self.tempimages.blurred)
            cover = ImageChops.multiply(wal, shadow)
            cover.paste(Image.new("RGB", wal.size, self.color), mask=mask)
            cover.save(self.out, format="JPEG", subsampling=0, quality=100)

    def color_through(self):
        if not os.path.exists(self.out):
            mask = Image.open(self.tempimages.mask)
            wal = Image.open(self.tempimages.wal)
            trans = mask.convert("L")
            data = mask.getdata(3)
            trans.putdata([max(item, 127) for item in data])
            mask.putalpha(trans)
            cover = Image.composite(wal, Image.new("RGB", wal.size, self.color), mask)
            cover.save(self.out, format="JPEG", subsampling=0, quality=100)

    def pixelate(self):
        if not os.path.exists(self.out):
            mask = Image.open(self.tempimages.mask)
            wal = Image.open(self.tempimages.wal)
            pix = Image.open(self.tempimages.pixelated)
            pix.paste(wal, mask=mask)
            pix.save(self.out, format="JPEG", subsampling=0, quality=100)

    def inverse_pixelate(self):
        if not os.path.exists(self.out):
            mask = Image.open(self.tempimages.mask)
            wal = Image.open(self.tempimages.wal)
            pix = Image.open(self.tempimages.pixelated)
            wal.paste(pix, mask=mask)
            wal.save(self.out, format="JPEG", subsampling=0, quality=100)

    def render(self):
        do = self.switch.get(self.style)
        if hasattr(self, do) and callable(func := getattr(self, do)):
            func()


templist: list[TempMaskPointers] = []
renderlist: list[tuple[TempImagePointers, str]] = []


def parse_arguments() -> Args:
    parser = argparse.ArgumentParser(description="Generate HTML files for a static image hosting website.", formatter_class=RichHelpFormatter)
    parser.add_argument("-m", "--masks", help="svg masks path", default=SVGDIR, type=str, dest="svgdir", metavar="FOLDER")
    parser.add_argument("-i", "--images", help="input images path", default=WALLPAPERDIR, type=str, dest="wallpaperdir", metavar="FOLDER")
    parser.add_argument("-o", "--out", help="output folder path", default=OUTDIR, type=str, dest="outdir", metavar="FOLDER")
    parser.add_argument("--generate-help-preview", action=HelpPreviewAction, path="help.svg")
    parsed_args = parser.parse_args()
    _args = Args()
    _args.svgdir = os.path.join(os.getcwd(), parsed_args.svgdir)
    _args.wallpaperdir = os.path.join(os.getcwd(), parsed_args.wallpaperdir)
    _args.outdir = os.path.join(os.getcwd(), parsed_args.outdir)
    return _args


def render(arguments: tuple[TempImagePointers, str, str]) -> None:
    tempimages, style, out = arguments
    color = style.removeprefix("ColorOverlay/").removeprefix("ColorOverlayBlur/").removeprefix("ColorThrough/")
    image = Render(tempimages, style, out, COLORS.get(color, None))
    image.render()


def create_mask_temps(arguments: tuple[str, tuple[int, int]]) -> TempMaskPointers:
    svg, size = arguments
    pointers = TempMaskPointers()
    tmpmask = BytesIO()

    width, height = size

    pointers.maskname = os.path.splitext(os.path.basename(svg))[0]
    pointers.size = size

    tmpname = f"{pointers.maskname}_{width}x{height}.png"

    if not os.path.exists(os.path.join(TEMPDIR, f"mask_{tmpname}")):
        cairosvg.svg2png(url=os.path.join(SVGDIR, svg), write_to=tmpmask, output_height=height, output_width=width, scale=1)
        mask = Image.open(tmpmask)
        mask.save(os.path.join(TEMPDIR, f"mask_{tmpname}"))

        blurred_mask = Image.new("RGB", size, (255, 255, 255))
        blurred_mask.paste(mask, mask=mask)
        shadow = blurred_mask.filter(filter=ImageFilter.GaussianBlur(radius=100))
        shadow.save(os.path.join(TEMPDIR, f"shadow_{tmpname}"))

        mask.close()
        blurred_mask.close()
        shadow.close()

    pointers.mask = os.path.join(TEMPDIR, f"mask_{tmpname}")
    pointers.shadow = os.path.join(TEMPDIR, f"shadow_{tmpname}")

    return pointers


def create_effect_temps(arguments: tuple[ImageFile.ImageFile, str, str, list[str]]) -> TempEffectPointers:
    wal, walfile, walname, need_effects = arguments
    pointers = TempEffectPointers()

    pointers.wal = walfile
    pointers.walname = walname
    pointers.size = wal.size
    pointers.walfile = os.path.basename(walfile)

    if NEED_BLUR in "\t".join(need_effects):
        if not os.path.exists(os.path.join(TEMPDIR, f"blurred_{walname}.jpg")):
            blurred = wal.filter(filter=ImageFilter.GaussianBlur(radius=20))
            blurred.save(os.path.join(TEMPDIR, f"blurred_{walname}.jpg"))
            blurred.close()
        pointers.blurred = os.path.join(TEMPDIR, f"blurred_{walname}.jpg")
    else:
        pointers.blurred = ""

    if len(NEED_BLUR_DARK.intersection(need_effects)) > 0:
        if not os.path.exists(os.path.join(TEMPDIR, f"blurred_dark_{walname}.jpg")):
            blurred_dark = wal.filter(filter=ImageFilter.GaussianBlur(radius=80))
            darkened80 = ImageEnhance.Brightness(blurred_dark)
            blurred_dark = darkened80.enhance(factor=0.8)
            blurred_dark.save(os.path.join(TEMPDIR, f"blurred_dark_{walname}.jpg"))
            blurred_dark.close()
        pointers.blurred_dark = os.path.join(TEMPDIR, f"blurred_dark_{walname}.jpg")
    else:
        pointers.blurred_dark = ""

    if len(NEED_BLUR_DARKER.intersection(need_effects)) > 0:
        if not os.path.exists(os.path.join(TEMPDIR, f"blurred_darker_{walname}.jpg")):
            blurred_darker = wal.filter(filter=ImageFilter.GaussianBlur(radius=80))
            darkened40 = ImageEnhance.Brightness(blurred_darker)
            blurred_darker = darkened40.enhance(factor=0.4)
            blurred_darker.save(os.path.join(TEMPDIR, f"blurred_darker_{walname}.jpg"))
            blurred_darker.close()
        pointers.blurred_darker = os.path.join(TEMPDIR, f"blurred_darker_{walname}.jpg")
    else:
        pointers.blurred_darker = ""

    if len(NEED_BRIGHTENED.intersection(need_effects)) > 0:
        if not os.path.exists(os.path.join(TEMPDIR, f"brightened_{walname}.jpg")):
            brightened = ImageEnhance.Brightness(wal)
            brightened = brightened.enhance(factor=1.1)
            brightened.save(os.path.join(TEMPDIR, f"brightened_{walname}.jpg"))
            brightened.close()
        pointers.brightened = os.path.join(TEMPDIR, f"brightened_{walname}.jpg")
    else:
        pointers.brightened = ""

    if len(NEED_NEGATE.intersection(need_effects)) > 0:
        if not os.path.exists(os.path.join(TEMPDIR, f"negated_{walname}.jpg")):
            negated = ImageOps.invert(wal)
            negated.save(os.path.join(TEMPDIR, f"negated_{walname}.jpg"))
            negated.close()
        pointers.negated = os.path.join(TEMPDIR, f"negated_{walname}.jpg")
    else:
        pointers.negated = ""

    if len(NEED_FLIP.intersection(need_effects)) > 0:
        if not os.path.exists(os.path.join(TEMPDIR, f"flipped_{walname}.jpg")):
            flipped = wal.transpose(method=Image.Transpose.FLIP_TOP_BOTTOM)
            flipped.save(os.path.join(TEMPDIR, f"flipped_{walname}.jpg"))
            flipped.close()
        pointers.flipped = os.path.join(TEMPDIR, f"flipped_{walname}.jpg")
    else:
        pointers.flipped = ""

    if len(NEED_PIXELATE.intersection(need_effects)) > 0:
        if not os.path.exists(os.path.join(TEMPDIR, f"pixelated_{walname}.jpg")):
            small = wal.resize((int(wal.width * 0.01), int(wal.height * 0.01)), Image.Resampling.BICUBIC)
            darkenedsmall = ImageEnhance.Brightness(small)
            darksmall = darkenedsmall.enhance(factor=0.8)
            pixelated = darksmall.resize(wal.size, Image.Resampling.NEAREST)
            pixelated.save(os.path.join(TEMPDIR, f"pixelated_{walname}.jpg"))
            small.close()
            darksmall.close()
            pixelated.close()
        pointers.pixelated = os.path.join(TEMPDIR, f"pixelated_{walname}.jpg")
    else:
        pointers.pixelated = ""

    return pointers


def main():
    motives: list[str] = []
    effectlist: list[tuple[ImageFile.ImageFile, str, str, list[str]]] = []
    masklist: set[tuple[str, tuple[int, int]]] = set()
    need_img_list: set[str] = set()
    need_motive_list: set[str] = set()
    need_style_list: set[str] = set()

    missing: dict[str, dict[str, list[str]]] = {}

    for color in COLORS.keys():
        STYLES.append(f"ColorOverlay/{color}")
        STYLES.append(f"ColorOverlayBlur/{color}")
        STYLES.append(f"ColorThrough/{color}")

    args = parse_arguments()

    try:
        motives = sorted(os.listdir(args.svgdir))
        imgs = sorted(os.listdir(args.wallpaperdir))
        styles = sorted(STYLES)
        for imgfilename in tqdm(imgs, desc="Checking for existing Wallpapers", unit="files", dynamic_ncols=True, ascii=True):
            imgname = os.path.splitext(os.path.basename(imgfilename))[0]
            for motivefile in tqdm(motives, desc=f"Checking for existing SVGs - {imgname}", unit="files", dynamic_ncols=True, ascii=True):
                motive = os.path.splitext(os.path.basename(motivefile))[0]
                for style in styles:
                    if "/" in style:
                        parts = style.split("/")
                        out = os.path.join(args.outdir, motive, imgname, parts[1] + parts[0].removeprefix("Color") + ".jpg")
                    else:
                        out = os.path.join(args.outdir, motive, imgname, style + ".jpg")
                    if not os.path.exists(out):
                        if not missing.get(imgfilename, False):
                            missing[imgfilename] = {}
                        if not missing[imgfilename].get(motivefile, False):
                            missing[imgfilename][motivefile] = []
                        if style not in missing[imgfilename][motivefile]:
                            missing[imgfilename][motivefile].append(style)
                        need_style_list.add(style)
                        need_img_list.add(imgfilename)
                        need_motive_list.add(motivefile)

        need_style_list = sorted(need_style_list)
        need_img_list = sorted(need_img_list)
        need_motive_list = sorted(need_motive_list)

        print(f"Temp Masks to be created: {len(need_motive_list)}")
        print(", ".join(need_motive_list))
        print(f"Wallpapers needed: {len(need_img_list)}")
        print(", ".join(need_img_list))
        print(f"Styles to be made: {len(need_style_list)}")
        print(", ".join(need_style_list))

        for imgfilename, v in missing.items():
            shutil.copyfile(os.path.join(args.wallpaperdir, imgfilename), os.path.join(TEMPDIR, imgfilename))
            img = Image.open(os.path.join(TEMPDIR, imgfilename))
            imgname = os.path.splitext(os.path.basename(imgfilename))[0]
            need_style = set()
            for motivefile, v2 in v.items():
                motive = os.path.splitext(os.path.basename(motivefile))[0]
                masklist.add((motivefile, img.size))
                for style in v2:
                    os.makedirs(os.path.join(args.outdir, motive, imgname), exist_ok=True)
                    need_style.add(style)
            effectlist.append((img, os.path.join(TEMPDIR, imgfilename), imgname, sorted(need_style)))

        # DEBUG
        # for mask in tqdm(masklist, total=len(masklist), desc="Creating mask temporaries", unit="image", ascii=True, dynamic_ncols=True):
        #     result = create_mask_temps(mask)
        #     templist.append(result)

        # PRODUCTION
        with Pool(os.cpu_count()) as pool:
            for result in tqdm(
                pool.imap_unordered(create_mask_temps, masklist), total=len(masklist), desc="Creating mask temporaries", unit="image", ascii=True, dynamic_ncols=True
            ):
                templist.append(result)

        # DEBUG
        # for effects in tqdm(effectlist, total=len(effectlist), desc="Creating effect temporaries", unit="image", ascii=True, dynamic_ncols=True):
        #     result = create_effect_temps(effects)
        #     for motivefile in missing[result.walfile].keys():
        #         motive = os.path.splitext(os.path.basename(motivefile))[0]
        #         width, height = result.size
        #         tmpname = f"{motive}_{width}x{height}.png"
        #         pointers = TempImagePointers()
        #         pointers.blurred = result.blurred
        #         pointers.blurred_dark = result.blurred_dark
        #         pointers.blurred_darker = result.blurred_darker
        #         pointers.brightened = result.brightened
        #         pointers.flipped = result.flipped
        #         pointers.mask = os.path.join(TEMPDIR, f"mask_{tmpname}")
        #         pointers.negated = result.negated
        #         pointers.pixelated = result.pixelated
        #         pointers.shadow = os.path.join(TEMPDIR, f"shadow_{tmpname}")
        #         pointers.wal = result.wal
        #         for style in missing[result.walfile][motivefile]:
        #             if "/" in style:
        #                 parts = style.split("/")
        #                 out = os.path.join(args.outdir, motive, result.walname, parts[1] + parts[0].removeprefix("Color") + ".jpg")
        #             else:
        #                 out = os.path.join(args.outdir, motive, result.walname, style + ".jpg")
        #             renderlist.append((pointers, style, out))

        # PRODUCTION
        with Pool(os.cpu_count()) as pool:
            for result in tqdm(
                pool.imap_unordered(create_effect_temps, effectlist), total=len(effectlist), desc="Creating effect temporaries", unit="image", ascii=True, dynamic_ncols=True
            ):
                for motivefile in missing[result.walfile].keys():
                    motive = os.path.splitext(os.path.basename(motivefile))[0]
                    width, height = result.size
                    tmpname = f"{motive}_{width}x{height}.png"
                    pointers = TempImagePointers()
                    pointers.blurred = result.blurred
                    pointers.blurred_dark = result.blurred_dark
                    pointers.blurred_darker = result.blurred_darker
                    pointers.brightened = result.brightened
                    pointers.flipped = result.flipped
                    pointers.mask = os.path.join(TEMPDIR, f"mask_{tmpname}")
                    pointers.negated = result.negated
                    pointers.pixelated = result.pixelated
                    pointers.shadow = os.path.join(TEMPDIR, f"shadow_{tmpname}")
                    pointers.wal = result.wal
                    for style in missing[result.walfile][motivefile]:
                        if "/" in style:
                            parts = style.split("/")
                            out = os.path.join(args.outdir, motive, result.walname, parts[1] + parts[0].removeprefix("Color") + ".jpg")
                        else:
                            out = os.path.join(args.outdir, motive, result.walname, style + ".jpg")
                        renderlist.append((pointers, style, out))

        # DEBUG
        # for renderi in tqdm(renderlist, total=len(renderlist), desc="Rendering wallpapers", unit="image", ascii=True, dynamic_ncols=True):
        #     render(renderi)

        # PRODUCTION
        with Pool(os.cpu_count()) as pool:
            for _ in tqdm(pool.imap_unordered(render, renderlist), total=len(renderlist), desc="Rendering wallpapers", unit="image", ascii=True, dynamic_ncols=True):
                pass

    finally:
        shutil.rmtree(TEMPDIR)


if __name__ == "__main__":
    main()
