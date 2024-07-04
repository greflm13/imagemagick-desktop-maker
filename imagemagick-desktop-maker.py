#!/usr/bin/env python3
import os
import cairosvg
from multiprocessing import Pool, Queue
from io import BytesIO
from tqdm.auto import tqdm
from PIL import Image, ImageFile, ImageFilter, ImageChops, ImageEnhance, ImageOps

SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))
SVGDIR = os.path.join(SCRIPTDIR, "Svgs")
WALLPAPERDIR = os.path.join(SCRIPTDIR, "Wallpapers")
OUTDIR = os.path.join(SCRIPTDIR, "Render")
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


class TempImages:
    mask: ImageFile.ImageFile
    shadow: Image.Image
    blurred_dark: Image.Image
    blurred_darker: Image.Image
    brightened: Image.Image
    negated: Image.Image
    flipped: Image.Image
    pixelated: Image.Image


class TempInput:
    svg: str
    wal: Image.Image


templist: list[tuple[TempInput, str, str, str]] = []
# renderlist = Queue()
renderlist: list[tuple[Image.Image, TempImages, str, str, str]] = []


def through_black(wal: Image.Image, tempimages: TempImages, maskname: str, walname: str):
    out = os.path.join(OUTDIR, "ThroughBlack", maskname, walname + ".jpg")
    if not os.path.exists(out):
        thrubl_image = Image.new("RGB", (wal.width, wal.height))
        thrubl_image.paste(wal, mask=tempimages.mask)
        thrubl_image.save(out)


def blur(tempimages: TempImages, maskname: str, walname: str):
    out = os.path.join(OUTDIR, "Blur", maskname, walname + ".jpg")
    if not os.path.exists(out):
        blurred_image = ImageChops.multiply(tempimages.blurred_dark, tempimages.shadow)
        blurred_image.paste(tempimages.brightened, mask=tempimages.mask)
        blurred_image.save(out)


def inverse_blur(wal: Image.Image, tempimages: TempImages, maskname: str, walname: str):
    out = os.path.join(OUTDIR, "InverseBlur", maskname, walname + ".jpg")
    if not os.path.exists(out):
        invblur = ImageChops.multiply(wal, tempimages.shadow)
        invblur.paste(tempimages.blurred_dark, mask=tempimages.mask)
        invblur.save(out)


def inverse_blur_darker(wal: Image.Image, tempimages: TempImages, maskname: str, walname: str):
    out = os.path.join(OUTDIR, "InverseBlurDarker", maskname, walname + ".jpg")
    if not os.path.exists(out):
        inblda_image = ImageChops.multiply(wal, tempimages.shadow)
        inblda_image.paste(tempimages.blurred_darker, mask=tempimages.mask)
        inblda_image.save(out)


def negate(wal: Image.Image, tempimages: TempImages, maskname: str, walname: str):
    out = os.path.join(OUTDIR, "Negate", maskname, walname + ".jpg")
    if not os.path.exists(out):
        neg = wal.copy()
        neg.paste(tempimages.negated, mask=tempimages.mask)
        neg.save(out)


def inverse_negate(wal: Image.Image, tempimages: TempImages, maskname: str, walname: str):
    out = os.path.join(OUTDIR, "InverseNegate", maskname, walname + ".jpg")
    if not os.path.exists(out):
        invneg = tempimages.negated.copy()
        invneg.paste(wal, mask=tempimages.mask)
        invneg.save(out)


def flip(wal: Image.Image, tempimages: TempImages, maskname: str, walname: str):
    out = os.path.join(OUTDIR, "Flip", maskname, walname + ".jpg")
    if not os.path.exists(out):
        flip = ImageChops.multiply(wal, tempimages.shadow)
        flip.paste(tempimages.flipped, mask=tempimages.mask)
        flip.save(out)


def black_overlay(wal: Image.Image, tempimages: TempImages, maskname: str, walname: str):
    out = os.path.join(OUTDIR, "BlackOverlay", maskname, walname + ".jpg")
    if not os.path.exists(out):
        blover = ImageChops.multiply(wal, tempimages.shadow)
        blover.paste(Image.new("RGB", wal.size, (0, 0, 0)), mask=tempimages.mask)
        blover.save(out)


def white_overlay(wal: Image.Image, tempimages: TempImages, maskname: str, walname: str):
    out = os.path.join(OUTDIR, "WhiteOverlay", maskname, walname + ".jpg")
    if not os.path.exists(out):
        whover = ImageChops.multiply(wal, tempimages.shadow)
        whover.paste(Image.new("RGB", wal.size, (255, 255, 255)), mask=tempimages.mask)
        whover.save(out)


def pixelate(wal: Image.Image, tempimages: TempImages, maskname: str, walname: str):
    out = os.path.join(OUTDIR, "Pixelate", maskname, walname + ".jpg")
    if not os.path.exists(out):
        pix = tempimages.pixelated.copy()
        pix.paste(wal, mask=tempimages.mask)
        pix.save(out)


def render(arguments: tuple[Image.Image, TempImages, str, str, str]) -> None:
    wal, tempimages, maskname, walname, method = arguments
    switch = {
        "BlackOverlay": black_overlay(wal, tempimages, maskname, walname),
        "Blur": blur(tempimages, maskname, walname),
        "Flip": flip(wal, tempimages, maskname, walname),
        "InverseBlur": inverse_blur(wal, tempimages, maskname, walname),
        "InverseBlurDarker": inverse_blur_darker(wal, tempimages, maskname, walname),
        "InverseNegate": inverse_negate(wal, tempimages, maskname, walname),
        "Negate": negate(wal, tempimages, maskname, walname),
        "Pixelate": pixelate(wal, tempimages, maskname, walname),
        "ThroughBlack": through_black(wal, tempimages, maskname, walname),
        "WhiteOverlay": white_overlay(wal, tempimages, maskname, walname),
    }
    switch.get(method)


def create_temps(arguments: tuple[TempInput, str, str]) -> tuple[Image.Image, TempImages, str, str]:
    inputs, maskname, walname = arguments
    outputs = TempImages()
    tmpmask = BytesIO()

    cairosvg.svg2png(url=os.path.join(SVGDIR, inputs.svg), write_to=tmpmask, output_height=inputs.wal.height, output_width=inputs.wal.width, scale=1)
    outputs.mask = Image.open(tmpmask)

    blurred_mask = Image.new("RGB", (outputs.mask.width, outputs.mask.height), (255, 255, 255))
    blurred_mask.paste(outputs.mask, mask=outputs.mask)
    outputs.shadow = blurred_mask.filter(filter=ImageFilter.GaussianBlur(radius=100))

    blurred_dark = inputs.wal.filter(filter=ImageFilter.GaussianBlur(radius=80))
    darkened80 = ImageEnhance.Brightness(blurred_dark)
    outputs.blurred_dark = darkened80.enhance(factor=0.8)

    blurred_darker = inputs.wal.filter(filter=ImageFilter.GaussianBlur(radius=80))
    darkened40 = ImageEnhance.Brightness(blurred_darker)
    outputs.blurred_darker = darkened40.enhance(factor=0.4)

    brightened = ImageEnhance.Brightness(inputs.wal)
    outputs.brightened = brightened.enhance(factor=1.1)

    outputs.negated = ImageOps.invert(inputs.wal)

    outputs.flipped = inputs.wal.transpose(method=Image.Transpose.FLIP_TOP_BOTTOM)

    small = inputs.wal.resize((int(inputs.wal.width * 0.01), int(inputs.wal.height * 0.01)), Image.Resampling.BICUBIC)
    darkenedsmall = ImageEnhance.Brightness(small)
    darksmall = darkenedsmall.enhance(factor=0.8)
    outputs.pixelated = darksmall.resize((inputs.wal.width, inputs.wal.height), Image.Resampling.NEAREST)

    return inputs.wal, outputs, maskname, walname


def main():
    svgs: list[str] = []
    wallpapers: list[Image.Image] = []
    svgs = sorted(os.listdir(SVGDIR))
    for wallpaper in sorted(os.listdir(WALLPAPERDIR)):
        wal = Image.open(os.path.join(WALLPAPERDIR, wallpaper))
        wallpapers.append((wal.copy(), wal.filename))

    for wallpaper, filename in wallpapers:
        walname = os.path.splitext(os.path.basename(filename))[0]
        for svg in svgs:
            svgname = os.path.splitext(os.path.basename(svg))[0]
            for method in sorted(METHODS):
                if not os.path.exists(os.path.join(OUTDIR)):
                    os.mkdir(os.path.join(OUTDIR))
                if not os.path.exists(os.path.join(OUTDIR, method)):
                    os.mkdir(os.path.join(OUTDIR, method))
                if not os.path.exists(os.path.join(OUTDIR, method, svgname)):
                    os.mkdir(os.path.join(OUTDIR, method, svgname))
            tmpin = TempInput()
            tmpin.svg = svg
            tmpin.wal = wallpaper
            templist.append((tmpin, svgname, walname))

    with Pool(os.cpu_count() / 2) as pool:
        for result in tqdm(pool.imap_unordered(create_temps, templist), total=len(templist), desc="Creating temporaries", unit="image", ascii=True, dynamic_ncols=True):
            for method in sorted(METHODS):
                arguments: tuple[ImageFile.ImageFile, TempImages, str, str, str] = (result[0], result[1], result[2], result[3], method)
                renderlist.append(arguments)

    with Pool(os.cpu_count()) as pool:
        for _ in tqdm(pool.imap_unordered(render, renderlist), total=len(renderlist), desc="Rendering wallpapers", unit="image", ascii=True, dynamic_ncols=True):
            pass
    # for image in renderlist:
    #     render(image)


if __name__ == "__main__":
    main()
