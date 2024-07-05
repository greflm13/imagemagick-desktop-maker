#!/usr/bin/env python3
import os
import shutil
import cairosvg
from multiprocessing import Pool
import tempfile
from io import BytesIO
from tqdm.auto import tqdm
from PIL import Image, ImageFile, ImageFilter, ImageChops, ImageEnhance, ImageOps

SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))
SVGDIR = os.path.join(SCRIPTDIR, "Svgs")
WALLPAPERDIR = os.path.join(SCRIPTDIR, "Wallpapers")
OUTDIR = os.path.join(SCRIPTDIR, "Render")
TEMPDIR = tempfile.mkdtemp()
METHODS = [
    "BlackOverlay",
    "Blur",
    "Flip",
    "InverseBlur",
    "InverseBlurDarker",
    "InverseNegate",
    "Negate",
    "Pixelate",
    "ThroughBlack",
    "WhiteOverlay",
]


class TempImagePointers:
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


class TempMaskPointers:
    mask: str
    maskname: str
    shadow: str


class TempEffectPointers:
    blurred_dark: str
    blurred_darker: str
    brightened: str
    flipped: str
    negated: str
    pixelated: str
    wal: str
    walname: str


templist: list[TempEffectPointers] = []
renderlist: list[tuple[TempImagePointers, str]] = []


def through_black(tempimages: TempImagePointers):
    out = os.path.join(OUTDIR, "ThroughBlack", tempimages.maskname, tempimages.walname + ".jpg")
    if not os.path.exists(out):
        mask = Image.open(tempimages.mask)
        wal = Image.open(tempimages.wal)
        thrubl_image = Image.new("RGB", (wal.width, wal.height))
        thrubl_image.paste(wal, mask=mask)
        thrubl_image.save(out)


def blur(tempimages: TempImagePointers):
    out = os.path.join(OUTDIR, "Blur", tempimages.maskname, tempimages.walname + ".jpg")
    if not os.path.exists(out):
        mask = Image.open(tempimages.mask)
        shadow = Image.open(tempimages.shadow)
        blurred_dark = Image.open(tempimages.blurred_dark)
        brightened = Image.open(tempimages.brightened)
        blurred_image = ImageChops.multiply(blurred_dark, shadow)
        blurred_image.paste(brightened, mask=mask)
        blurred_image.save(out)


def inverse_blur(tempimages: TempImagePointers):
    out = os.path.join(OUTDIR, "InverseBlur", tempimages.maskname, tempimages.walname + ".jpg")
    if not os.path.exists(out):
        mask = Image.open(tempimages.mask)
        shadow = Image.open(tempimages.shadow)
        wal = Image.open(tempimages.wal)
        blurred_dark = Image.open(tempimages.blurred_dark)
        invblur = ImageChops.multiply(wal, shadow)
        invblur.paste(blurred_dark, mask=mask)
        invblur.save(out)


def inverse_blur_darker(tempimages: TempImagePointers):
    out = os.path.join(OUTDIR, "InverseBlurDarker", tempimages.maskname, tempimages.walname + ".jpg")
    if not os.path.exists(out):
        mask = Image.open(tempimages.mask)
        shadow = Image.open(tempimages.shadow)
        wal = Image.open(tempimages.wal)
        blurred_darker = Image.open(tempimages.blurred_darker)
        inblda_image = ImageChops.multiply(wal, shadow)
        inblda_image.paste(blurred_darker, mask=mask)
        inblda_image.save(out)


def negate(tempimages: TempImagePointers):
    out = os.path.join(OUTDIR, "Negate", tempimages.maskname, tempimages.walname + ".jpg")
    if not os.path.exists(out):
        mask = Image.open(tempimages.mask)
        negated = Image.open(tempimages.negated)
        neg = Image.open(tempimages.wal)
        neg.paste(negated, mask=mask)
        neg.save(out)


def inverse_negate(tempimages: TempImagePointers):
    out = os.path.join(OUTDIR, "InverseNegate", tempimages.maskname, tempimages.walname + ".jpg")
    if not os.path.exists(out):
        mask = Image.open(tempimages.mask)
        wal = Image.open(tempimages.wal)
        invneg = Image.open(tempimages.negated)
        invneg.paste(wal, mask=mask)
        invneg.save(out)


def flip(tempimages: TempImagePointers):
    out = os.path.join(OUTDIR, "Flip", tempimages.maskname, tempimages.walname + ".jpg")
    if not os.path.exists(out):
        mask = Image.open(tempimages.mask)
        shadow = Image.open(tempimages.shadow)
        wal = Image.open(tempimages.wal)
        flipped = Image.open(tempimages.flipped)
        flip = ImageChops.multiply(wal, shadow)
        flip.paste(flipped, mask=mask)
        flip.save(out)


def black_overlay(tempimages: TempImagePointers):
    out = os.path.join(OUTDIR, "BlackOverlay", tempimages.maskname, tempimages.walname + ".jpg")
    if not os.path.exists(out):
        mask = Image.open(tempimages.mask)
        shadow = Image.open(tempimages.shadow)
        wal = Image.open(tempimages.wal)
        blover = ImageChops.multiply(wal, shadow)
        blover.paste(Image.new("RGB", wal.size, (0, 0, 0)), mask=mask)
        blover.save(out)


def white_overlay(tempimages: TempImagePointers):
    out = os.path.join(OUTDIR, "WhiteOverlay", tempimages.maskname, tempimages.walname + ".jpg")
    if not os.path.exists(out):
        mask = Image.open(tempimages.mask)
        shadow = Image.open(tempimages.shadow)
        wal = Image.open(tempimages.wal)
        whover = ImageChops.multiply(wal, shadow)
        whover.paste(Image.new("RGB", wal.size, (255, 255, 255)), mask=mask)
        whover.save(out)


def pixelate(tempimages: TempImagePointers):
    out = os.path.join(OUTDIR, "Pixelate", tempimages.maskname, tempimages.walname + ".jpg")
    if not os.path.exists(out):
        mask = Image.open(tempimages.mask)
        wal = Image.open(tempimages.wal)
        pix = Image.open(tempimages.pixelated)
        pix.paste(wal, mask=mask)
        pix.save(out)


def render(arguments: tuple[TempImagePointers, str]) -> None:
    tempimages, method = arguments
    switch = {
        "BlackOverlay": black_overlay(tempimages),
        "Blur": blur(tempimages),
        "Flip": flip(tempimages),
        "InverseBlur": inverse_blur(tempimages),
        "InverseBlurDarker": inverse_blur_darker(tempimages),
        "InverseNegate": inverse_negate(tempimages),
        "Negate": negate(tempimages),
        "Pixelate": pixelate(tempimages),
        "ThroughBlack": through_black(tempimages),
        "WhiteOverlay": white_overlay(tempimages),
    }
    switch.get(method)


def create_mask_temps(arguments: tuple[str, ImageFile.ImageFile, str]) -> TempMaskPointers:
    svg, wal, walname = arguments
    pointers = TempMaskPointers()
    tmpmask = BytesIO()

    pointers.maskname = os.path.splitext(os.path.basename(svg))[0]

    cairosvg.svg2png(url=os.path.join(SVGDIR, svg), write_to=tmpmask, output_height=wal.height, output_width=wal.width, scale=1)
    mask = Image.open(tmpmask)
    mask.save(os.path.join(TEMPDIR, "mask_" + pointers.maskname + "_" + walname + ".png"))
    pointers.mask = os.path.join(TEMPDIR, "mask_" + pointers.maskname + "_" + walname + ".png")

    blurred_mask = Image.new("RGB", (mask.width, mask.height), (255, 255, 255))
    blurred_mask.paste(mask, mask=mask)
    shadow = blurred_mask.filter(filter=ImageFilter.GaussianBlur(radius=100))
    shadow.save(os.path.join(TEMPDIR, "shadow_" + pointers.maskname + "_" + walname + ".jpg"))
    pointers.shadow = os.path.join(TEMPDIR, "shadow_" + pointers.maskname + "_" + walname + ".jpg")

    mask.close()
    blurred_mask.close()
    shadow.close()

    return pointers


def create_effect_temps(arguments: tuple[ImageFile.ImageFile, str, str]) -> TempEffectPointers:
    wal, walfile, walname = arguments
    pointers = TempEffectPointers()

    pointers.wal = walfile
    pointers.walname = walname

    if not os.path.exists(os.path.join(TEMPDIR, "blurred_dark_" + walname + ".jpg")):
        blurred_dark = wal.filter(filter=ImageFilter.GaussianBlur(radius=80))
        darkened80 = ImageEnhance.Brightness(blurred_dark)
        blurred_dark = darkened80.enhance(factor=0.8)
        blurred_dark.save(os.path.join(TEMPDIR, "blurred_dark_" + walname + ".jpg"))
        blurred_dark.close()
    pointers.blurred_dark = os.path.join(TEMPDIR, "blurred_dark_" + walname + ".jpg")

    if not os.path.exists(os.path.join(TEMPDIR, "blurred_darker_" + walname + ".jpg")):
        blurred_darker = wal.filter(filter=ImageFilter.GaussianBlur(radius=80))
        darkened40 = ImageEnhance.Brightness(blurred_darker)
        blurred_darker = darkened40.enhance(factor=0.4)
        blurred_darker.save(os.path.join(TEMPDIR, "blurred_darker_" + walname + ".jpg"))
        blurred_darker.close()
    pointers.blurred_darker = os.path.join(TEMPDIR, "blurred_darker_" + walname + ".jpg")

    if not os.path.exists(os.path.join(TEMPDIR, "brightened_" + walname + ".jpg")):
        brightened = ImageEnhance.Brightness(wal)
        brightened = brightened.enhance(factor=1.1)
        brightened.save(os.path.join(TEMPDIR, "brightened_" + walname + ".jpg"))
        brightened.close()
    pointers.brightened = os.path.join(TEMPDIR, "brightened_" + walname + ".jpg")

    if not os.path.exists(os.path.join(TEMPDIR, "negated_" + walname + ".jpg")):
        negated = ImageOps.invert(wal)
        negated.save(os.path.join(TEMPDIR, "negated_" + walname + ".jpg"))
        negated.close()
    pointers.negated = os.path.join(TEMPDIR, "negated_" + walname + ".jpg")

    if not os.path.exists(os.path.join(TEMPDIR, "flipped_" + walname + ".jpg")):
        flipped = wal.transpose(method=Image.Transpose.FLIP_TOP_BOTTOM)
        flipped.save(os.path.join(TEMPDIR, "flipped_" + walname + ".jpg"))
        flipped.close()
    pointers.flipped = os.path.join(TEMPDIR, "flipped_" + walname + ".jpg")

    if not os.path.exists(os.path.join(TEMPDIR, "pixelated_" + walname + ".jpg")):
        small = wal.resize((int(wal.width * 0.01), int(wal.height * 0.01)), Image.Resampling.BICUBIC)
        darkenedsmall = ImageEnhance.Brightness(small)
        darksmall = darkenedsmall.enhance(factor=0.8)
        pixelated = darksmall.resize((wal.width, wal.height), Image.Resampling.NEAREST)
        pixelated.save(os.path.join(TEMPDIR, "pixelated_" + walname + ".jpg"))
        small.close()
        darksmall.close()
        pixelated.close()
    pointers.pixelated = os.path.join(TEMPDIR, "pixelated_" + walname + ".jpg")

    return pointers


def main():
    svgs: list[str] = []
    wallpapers: list[ImageFile.ImageFile] = []
    effectlist: list[tuple[ImageFile.ImageFile, str, str]] = []
    masklist: list[tuple[str, ImageFile.ImageFile, str]] = []
    svgs = sorted(os.listdir(SVGDIR))
    for wallpaper in sorted(os.listdir(WALLPAPERDIR)):
        wal = Image.open(os.path.join(WALLPAPERDIR, wallpaper))
        wallpapers.append(wal)

    for wallpaper in wallpapers:
        walname = os.path.splitext(os.path.basename(wallpaper.filename))[0]
        effectlist.append((wallpaper, wallpaper.filename, walname))
        for svg in svgs:
            svgname = os.path.splitext(os.path.basename(svg))[0]
            for method in sorted(METHODS):
                if not os.path.exists(os.path.join(OUTDIR)):
                    os.mkdir(os.path.join(OUTDIR))
                if not os.path.exists(os.path.join(OUTDIR, method)):
                    os.mkdir(os.path.join(OUTDIR, method))
                if not os.path.exists(os.path.join(OUTDIR, method, svgname)):
                    os.mkdir(os.path.join(OUTDIR, method, svgname))
            masklist.append((svg, wallpaper, walname))

    with Pool(os.cpu_count()) as pool:
        for result in tqdm(pool.imap_unordered(create_effect_temps, effectlist), total=len(effectlist), desc="Creating effect temporaries", unit="image", ascii=True, dynamic_ncols=True):
            templist.append(result)

    with Pool(os.cpu_count()) as pool:
        for result in tqdm(pool.imap_unordered(create_mask_temps, masklist), total=len(masklist), desc="Creating mask temporaries", unit="image", ascii=True, dynamic_ncols=True):
            for wallpaper in templist:
                pointers = TempImagePointers()
                pointers.blurred_dark = wallpaper.blurred_dark
                pointers.blurred_darker = wallpaper.blurred_darker
                pointers.brightened = wallpaper.brightened
                pointers.flipped = wallpaper.flipped
                pointers.mask = result.mask
                pointers.maskname = result.maskname
                pointers.negated = wallpaper.negated
                pointers.pixelated = wallpaper.pixelated
                pointers.shadow = result.shadow
                pointers.wal = wallpaper.wal
                pointers.walname = wallpaper.walname
                for method in sorted(METHODS):
                    arguments: tuple[TempImagePointers, str] = (pointers, method)
                    renderlist.append(arguments)

    with Pool(os.cpu_count()) as pool:
        for _ in tqdm(pool.imap_unordered(render, renderlist), total=len(renderlist), desc="Rendering wallpapers", unit="image", ascii=True, dynamic_ncols=True):
            pass
    # for image in renderlist:
    #     render(image)

    shutil.rmtree(TEMPDIR)


if __name__ == "__main__":
    main()
