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
METHODS = [
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
    "Aquamarine": "#00F5D4",
    "Black": "#000000",
    "BrilliantRose": "#F15BB5",
    "CambridgeBlue": "#7DA27F",
    "CancomRed": "#DA002D",
    "DeepSkyBlue": "#00BBF9",
    "Lion": "#AD9667",
    "Maize": "#FEE440",
    "MidnightGreen": "#115E6B",
    "Sapphire": "#004EAA",
    "SelectiveYellow": "#FFB92A",
    "SovietRed": "#CC0000",
    "Tekhelet": "#592B8A",
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
    maskname: str
    negated: str
    pixelated: str
    shadow: str
    wal: str
    walname: str
    args: Args


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
    method: str
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

    def __init__(self, tempimages: TempImagePointers, method: str, color: str | None = None):
        self.tempimages = tempimages
        self.method = method
        self.color = color

        for col in COLORS.keys():
            self.switch[f"{col}Overlay"] = "color_overlay"
            self.switch[f"{col}OverlayBlur"] = "color_overlay_blur"
            self.switch[f"{col}Through"] = "color_through"

    def through_black(self):
        out = os.path.join(self.tempimages.args.outdir, self.method, self.tempimages.maskname, self.tempimages.walname + ".jpg")
        if not os.path.exists(out):
            mask = Image.open(self.tempimages.mask)
            wal = Image.open(self.tempimages.wal)
            thrubl_image = Image.new("RGB", (wal.width, wal.height))
            thrubl_image.paste(wal, mask=mask)
            thrubl_image.save(out)

    def blur(self):
        out = os.path.join(self.tempimages.args.outdir, self.method, self.tempimages.maskname, self.tempimages.walname + ".jpg")
        if not os.path.exists(out):
            mask = Image.open(self.tempimages.mask)
            shadow = Image.open(self.tempimages.shadow)
            blurred_dark = Image.open(self.tempimages.blurred_dark)
            brightened = Image.open(self.tempimages.brightened)
            blurred_image = ImageChops.multiply(blurred_dark, shadow)
            blurred_image.paste(brightened, mask=mask)
            blurred_image.save(out)

    def inverse_blur(self):
        out = os.path.join(self.tempimages.args.outdir, self.method, self.tempimages.maskname, self.tempimages.walname + ".jpg")
        if not os.path.exists(out):
            mask = Image.open(self.tempimages.mask)
            shadow = Image.open(self.tempimages.shadow)
            wal = Image.open(self.tempimages.wal)
            blurred_dark = Image.open(self.tempimages.blurred_dark)
            invblur = ImageChops.multiply(wal, shadow)
            invblur.paste(blurred_dark, mask=mask)
            invblur.save(out)

    def inverse_blur_darker(self):
        out = os.path.join(self.tempimages.args.outdir, self.method, self.tempimages.maskname, self.tempimages.walname + ".jpg")
        if not os.path.exists(out):
            mask = Image.open(self.tempimages.mask)
            shadow = Image.open(self.tempimages.shadow)
            wal = Image.open(self.tempimages.wal)
            blurred_darker = Image.open(self.tempimages.blurred_darker)
            inblda_image = ImageChops.multiply(wal, shadow)
            inblda_image.paste(blurred_darker, mask=mask)
            inblda_image.save(out)

    def negate(self):
        out = os.path.join(self.tempimages.args.outdir, self.method, self.tempimages.maskname, self.tempimages.walname + ".jpg")
        if not os.path.exists(out):
            mask = Image.open(self.tempimages.mask)
            negated = Image.open(self.tempimages.negated)
            neg = Image.open(self.tempimages.wal)
            neg.paste(negated, mask=mask)
            neg.save(out)

    def inverse_negate(self):
        out = os.path.join(self.tempimages.args.outdir, self.method, self.tempimages.maskname, self.tempimages.walname + ".jpg")
        if not os.path.exists(out):
            mask = Image.open(self.tempimages.mask)
            wal = Image.open(self.tempimages.wal)
            invneg = Image.open(self.tempimages.negated)
            invneg.paste(wal, mask=mask)
            invneg.save(out)

    def flip(self):
        out = os.path.join(self.tempimages.args.outdir, self.method, self.tempimages.maskname, self.tempimages.walname + ".jpg")
        if not os.path.exists(out):
            mask = Image.open(self.tempimages.mask)
            shadow = Image.open(self.tempimages.shadow)
            wal = Image.open(self.tempimages.wal)
            flipped = Image.open(self.tempimages.flipped)
            flipimg = ImageChops.multiply(wal, shadow)
            flipimg.paste(flipped, mask=mask)
            flipimg.save(out)

    def color_overlay(self):
        out = os.path.join(self.tempimages.args.outdir, self.method, self.tempimages.maskname, self.tempimages.walname + ".jpg")
        if not os.path.exists(out):
            mask = Image.open(self.tempimages.mask)
            shadow = Image.open(self.tempimages.shadow)
            wal = Image.open(self.tempimages.wal)
            cover = ImageChops.multiply(wal, shadow)
            cover.paste(Image.new("RGB", wal.size, self.color), mask=mask)
            cover.save(out)

    def color_overlay_blur(self):
        out = os.path.join(self.tempimages.args.outdir, self.method, self.tempimages.maskname, self.tempimages.walname + ".jpg")
        if not os.path.exists(out):
            mask = Image.open(self.tempimages.mask)
            shadow = Image.open(self.tempimages.shadow)
            wal = Image.open(self.tempimages.blurred)
            cover = ImageChops.multiply(wal, shadow)
            cover.paste(Image.new("RGB", wal.size, self.color), mask=mask)
            cover.save(out)

    def color_through(self):
        out = os.path.join(self.tempimages.args.outdir, self.method, self.tempimages.maskname, self.tempimages.walname + ".jpg")
        if not os.path.exists(out):
            mask = Image.open(self.tempimages.mask)
            wal = Image.open(self.tempimages.wal)
            trans = mask.convert("L")
            data = mask.getdata(3)
            trans.putdata([max(item, 127) for item in data])
            mask.putalpha(trans)
            cover = Image.composite(wal, Image.new("RGB", wal.size, self.color), mask)
            cover.save(out)

    def pixelate(self):
        out = os.path.join(self.tempimages.args.outdir, self.method, self.tempimages.maskname, self.tempimages.walname + ".jpg")
        if not os.path.exists(out):
            mask = Image.open(self.tempimages.mask)
            wal = Image.open(self.tempimages.wal)
            pix = Image.open(self.tempimages.pixelated)
            pix.paste(wal, mask=mask)
            pix.save(out)

    def inverse_pixelate(self):
        out = os.path.join(self.tempimages.args.outdir, self.method, self.tempimages.maskname, self.tempimages.walname + ".jpg")
        if not os.path.exists(out):
            mask = Image.open(self.tempimages.mask)
            wal = Image.open(self.tempimages.wal)
            pix = Image.open(self.tempimages.pixelated)
            wal.paste(pix, mask=mask)
            wal.save(out)

    def render(self):
        do = self.switch.get(self.method)
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


def render(arguments: tuple[TempImagePointers, str]) -> None:
    tempimages, method = arguments
    color = method.removesuffix("Overlay").removesuffix("OverlayBlur").removesuffix("Through")
    image = Render(tempimages, method, COLORS.get(color, None))
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
    svgs: list[str] = []
    effectlist: list[tuple[ImageFile.ImageFile, str, str, list[str]]] = []
    masklist: set[tuple[str, tuple[int, int]]] = set()
    need_wall_list: set[str] = set()
    need_svg_list: set[str] = set()
    need_method_list: set[str] = set()

    missing: dict[str, dict[str, list[str]]] = {}

    for color in COLORS.keys():
        METHODS.append(f"{color}Overlay")
        METHODS.append(f"{color}OverlayBlur")
        METHODS.append(f"{color}Through")

    args = parse_arguments()

    try:
        svgs = sorted(os.listdir(args.svgdir))
        wallpaprs = sorted(os.listdir(args.wallpaperdir))
        methods = sorted(METHODS)
        for wallpaper in tqdm(wallpaprs, desc="Checking for existing Wallpapers", unit="files", dynamic_ncols=True, ascii=True):
            walname = os.path.splitext(os.path.basename(wallpaper))[0]
            for svg in tqdm(svgs, desc=f"Checking for existing SVGs - {walname}", unit="files", dynamic_ncols=True, ascii=True):
                svgname = os.path.splitext(os.path.basename(svg))[0]
                for method in methods:
                    if not os.path.exists(os.path.join(args.outdir, method, svgname, walname + ".jpg")):
                        if not missing.get(wallpaper, False):
                            missing[wallpaper] = {}
                        if not missing[wallpaper].get(svg, False):
                            missing[wallpaper][svg] = []
                        if not method in missing[wallpaper][svg]:
                            missing[wallpaper][svg].append(method)
                        need_method_list.add(method)
                        need_wall_list.add(wallpaper)
                        need_svg_list.add(svg)

        need_method_list = sorted(need_method_list)
        need_wall_list = sorted(need_wall_list)
        need_svg_list = sorted(need_svg_list)

        print(f"Temp Masks to be created: {len(need_svg_list)}")
        print(", ".join(need_svg_list))
        print(f"Wallpapers needed: {len(need_wall_list)}")
        print(", ".join(need_wall_list))
        print(f"Effects to be made: {len(need_method_list)}")
        print(", ".join(need_method_list))

        for wallpaper, v in missing.items():
            wal = Image.open(os.path.join(args.wallpaperdir, wallpaper))
            walname = os.path.splitext(os.path.basename(wallpaper))[0]
            need_med = set()
            for svg, v2 in v.items():
                svgname = os.path.splitext(os.path.basename(svg))[0]
                masklist.add((svg, wal.size))
                for method in v2:
                    os.makedirs(os.path.join(args.outdir, method, svgname), exist_ok=True)
                    need_med.add(method)
            effectlist.append((wal, os.path.join(args.wallpaperdir, wallpaper), walname, sorted(need_med)))

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
        #     for svg in missing[result.walfile].keys():
        #         maskname = os.path.splitext(os.path.basename(svg))[0]
        #         width, height = result.size
        #         tmpname = f"{maskname}_{width}x{height}.png"
        #         pointers = TempImagePointers()
        #         pointers.blurred = result.blurred
        #         pointers.blurred_dark = result.blurred_dark
        #         pointers.blurred_darker = result.blurred_darker
        #         pointers.brightened = result.brightened
        #         pointers.flipped = result.flipped
        #         pointers.mask = os.path.join(TEMPDIR, f"mask_{tmpname}")
        #         pointers.maskname = maskname
        #         pointers.negated = result.negated
        #         pointers.pixelated = result.pixelated
        #         pointers.shadow = os.path.join(TEMPDIR, f"shadow_{tmpname}")
        #         pointers.wal = result.wal
        #         pointers.walname = result.walname
        #         pointers.args = args
        #         for method in missing[result.walfile][svg]:
        #             renderlist.append((pointers, method))

        # PRODUCTION
        with Pool(os.cpu_count()) as pool:
            for result in tqdm(
                pool.imap_unordered(create_effect_temps, effectlist), total=len(effectlist), desc="Creating effect temporaries", unit="image", ascii=True, dynamic_ncols=True
            ):
                for svg in missing[result.walfile].keys():
                    maskname = os.path.splitext(os.path.basename(svg))[0]
                    width, height = result.size
                    tmpname = f"{maskname}_{width}x{height}.png"
                    pointers = TempImagePointers()
                    pointers.blurred = result.blurred
                    pointers.blurred_dark = result.blurred_dark
                    pointers.blurred_darker = result.blurred_darker
                    pointers.brightened = result.brightened
                    pointers.flipped = result.flipped
                    pointers.mask = os.path.join(TEMPDIR, f"mask_{tmpname}")
                    pointers.maskname = maskname
                    pointers.negated = result.negated
                    pointers.pixelated = result.pixelated
                    pointers.shadow = os.path.join(TEMPDIR, f"shadow_{tmpname}")
                    pointers.wal = result.wal
                    pointers.walname = result.walname
                    pointers.args = args
                    for method in missing[result.walfile][svg]:
                        renderlist.append((pointers, method))

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
