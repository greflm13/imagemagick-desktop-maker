#!/usr/bin/env python3
import os
import json
import gzip
import shutil
import logging
import argparse
from datetime import datetime
from multiprocessing import Pool
import tempfile
import subprocess
from io import BytesIO
import cairosvg
from tqdm.auto import tqdm
from PIL import Image, ImageFilter, ImageChops, ImageEnhance, ImageOps
from rich_argparse import RichHelpFormatter, HelpPreviewAction
from pythonjsonlogger import jsonlogger

SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))
SVGDIR = os.path.join(SCRIPTDIR, "Svgs")
WALLPAPERDIR = os.path.join(SCRIPTDIR, "Wallpapers")
OUTDIR = os.path.join(SCRIPTDIR, "Render")
LOG_DIR = os.path.join(SCRIPTDIR, "logs")
LATEST_LOG_FILE = os.path.join(LOG_DIR, "latest.jsonl")
TEMPDIR = tempfile.mkdtemp()
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "imagemagick-desktop-maker")
os.makedirs(CACHE_DIR, exist_ok=True)
STYLES = [
    "Blur",
    "Flip",
    "InverseBlur",
    "InverseBlurDarker",
    "InverseNegate",
    "InversePixelate",
    "LogoColors",
    "Negate",
    "Pixelate",
    "ThroughBlack",
]

NEED_BLUR = "OverlayBlur"
NEED_BLUR_DARK = set(["Blur", "InverseBlur"])
NEED_BLUR_DARKER = set(["InverseBlurDarker"])
NEED_BRIGHTENED = set(["Blur"])
NEED_FLIP = set(["Flip"])
NEED_LOGOCOLORS = set(["LogoColors"])
NEED_NEGATE = set(["InverseNegate", "Negate"])
NEED_PIXELATE = set(["InversePixelate", "Pixelate"])

ALL_COLORS_DICT = {
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
    "KnappBlue": "#029AA9",
    "Lion": "#AD9667",
    "Maize": "#FEE440",
    "ManjaroGreen": "#35BFA4",
    "MidnightGreen": "#115E6B",
    "MintGreen": "#69B53F",
    "Nachtblau": "#222D5A",
    "Sapphire": "#004EAA",
    "SelectiveYellow": "#FFB92A",
    "SovietRed": "#CC0000",
    "SuseGreen": "#30BA78",
    "Tannengrün": "#27352A",
    "Tekhelet": "#592B8A",
    "UbuntuOrange": "#E95420",
    "Verkehrsrot": "#BB1F11",
    "White": "#FFFFFF",
}


class Args:
    svgdir: str
    wallpaperdir: str
    outdir: str
    sync_wallpapers: bool
    effects: list[str]
    colors: list[str]


class TempImagePointers:
    blurred_dark: str
    blurred_darker: str
    blurred: str
    brightened: str
    flipped: str
    logocolored: str
    mask: str
    negated: str
    pixelated: str
    shadow: str
    wal: str


class TempMaskPointers:
    logocolor: str
    mask: str
    maskname: str
    shadow: str
    size: tuple[int, int]


class TempEffectPointers:
    blurred_dark: str
    blurred_darker: str
    blurred: str
    brightened: str
    flipped: str
    negated: str
    pixelated: str
    size: tuple[int, int]
    wal: str
    walfile: str
    walname: str


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

    def __init__(self, walfile: str, walname: str, walsize: tuple[int, int], effect: str):
        self.walfile = walfile
        self.walname = walname
        self.walsize = walsize
        self.effect = effect
        self.output_path = os.path.join(TEMPDIR, f"{effect}_{walname}.jpg")

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
        brightened.close()
        wal.close()

    def create_negated(self):
        """Create inverted/negated version."""
        wal = Image.open(self.walfile)
        negated = ImageOps.invert(wal)
        negated.save(self.output_path, format="JPEG", subsampling=0, quality=100)
        negated.close()
        wal.close()

    def create_flipped(self):
        """Create vertically flipped version."""
        wal = Image.open(self.walfile)
        flipped = wal.transpose(method=Image.Transpose.FLIP_TOP_BOTTOM)
        flipped.save(self.output_path, format="JPEG", subsampling=0, quality=100)
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
        small.close()
        darksmall.close()
        pixelated.close()
        wal.close()


class Render:
    tempimages: TempImagePointers
    style: str
    out: str
    color: str | None = None
    img: Image.Image | None = None

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

    def __init__(self, tempimages: TempImagePointers, style: str, out: str, color: str | None = None):
        self.tempimages = tempimages
        self.style = style
        self.out = out
        self.color = color

        for col in SELECTED_COLORS.keys():
            self.switch[f"ColorOverlay/{col}"] = "color_overlay"
            self.switch[f"ColorOverlayBlur/{col}"] = "color_overlay_blur"
            self.switch[f"ColorThrough/{col}"] = "color_through"

    def through_black(self):
        mask = Image.open(self.tempimages.mask)
        wal = Image.open(self.tempimages.wal)
        thrubl_image = Image.new("RGB", (wal.width, wal.height))
        thrubl_image.paste(wal, mask=mask)
        self.img = thrubl_image

    def blur(self):
        mask = Image.open(self.tempimages.mask)
        shadow = Image.open(self.tempimages.shadow)
        blurred_dark = Image.open(self.tempimages.blurred_dark)
        brightened = Image.open(self.tempimages.brightened)
        blurred_image = ImageChops.multiply(blurred_dark, shadow)
        blurred_image.paste(brightened, mask=mask)
        self.img = blurred_image

    def inverse_blur(self):
        mask = Image.open(self.tempimages.mask)
        shadow = Image.open(self.tempimages.shadow)
        wal = Image.open(self.tempimages.wal)
        blurred_dark = Image.open(self.tempimages.blurred_dark)
        invblur = ImageChops.multiply(wal, shadow)
        invblur.paste(blurred_dark, mask=mask)
        self.img = invblur

    def inverse_blur_darker(self):
        mask = Image.open(self.tempimages.mask)
        shadow = Image.open(self.tempimages.shadow)
        wal = Image.open(self.tempimages.wal)
        blurred_darker = Image.open(self.tempimages.blurred_darker)
        inblda_image = ImageChops.multiply(wal, shadow)
        inblda_image.paste(blurred_darker, mask=mask)
        self.img = inblda_image

    def negate(self):
        mask = Image.open(self.tempimages.mask)
        negated = Image.open(self.tempimages.negated)
        neg = Image.open(self.tempimages.wal)
        neg.paste(negated, mask=mask)
        self.img = neg

    def inverse_negate(self):
        mask = Image.open(self.tempimages.mask)
        wal = Image.open(self.tempimages.wal)
        invneg = Image.open(self.tempimages.negated)
        invneg.paste(wal, mask=mask)
        self.img = invneg

    def flip(self):
        mask = Image.open(self.tempimages.mask)
        shadow = Image.open(self.tempimages.shadow)
        wal = Image.open(self.tempimages.wal)
        flipped = Image.open(self.tempimages.flipped)
        flipimg = ImageChops.multiply(wal, shadow)
        flipimg.paste(flipped, mask=mask)
        self.img = flipimg

    def color_overlay(self):
        mask = Image.open(self.tempimages.mask)
        shadow = Image.open(self.tempimages.shadow)
        wal = Image.open(self.tempimages.wal)
        cover = ImageChops.multiply(wal, shadow)
        cover.paste(Image.new("RGB", wal.size, self.color), mask=mask)
        self.img = cover

    def color_overlay_blur(self):
        mask = Image.open(self.tempimages.mask)
        shadow = Image.open(self.tempimages.shadow)
        wal = Image.open(self.tempimages.blurred)
        cover = ImageChops.multiply(wal, shadow)
        cover.paste(Image.new("RGB", wal.size, self.color), mask=mask)
        self.img = cover

    def color_through(self):
        mask = Image.open(self.tempimages.mask)
        wal = Image.open(self.tempimages.wal)
        trans = mask.convert("L")
        data = mask.getdata(3)
        trans.putdata([max(item, 127) for item in data])
        mask.putalpha(trans)
        cover = Image.composite(wal, Image.new("RGB", wal.size, self.color), mask)
        self.img = cover

    def pixelate(self):
        mask = Image.open(self.tempimages.mask)
        wal = Image.open(self.tempimages.wal)
        pix = Image.open(self.tempimages.pixelated)
        pix.paste(wal, mask=mask)
        self.img = pix

    def inverse_pixelate(self):
        mask = Image.open(self.tempimages.mask)
        wal = Image.open(self.tempimages.wal)
        pix = Image.open(self.tempimages.pixelated)
        wal.paste(pix, mask=mask)
        self.img = wal

    def logo_colors(self):
        logocolored = Image.open(self.tempimages.logocolored)
        mask = Image.open(self.tempimages.mask)
        wal = Image.open(self.tempimages.wal)
        wal.paste(logocolored, mask=mask)
        self.img = wal

    def render(self):
        if not os.path.exists(self.out):
            do = self.switch.get(self.style, "")
            if hasattr(self, do) and callable(func := getattr(self, do)):
                func()
                if isinstance(self.img, Image.Image):
                    self.img.save(self.out, format="JPEG", subsampling=2, quality=95, optimize=True)


templist: list[TempMaskPointers] = []
renderlist: list[tuple[TempImagePointers, str, str]] = []
# Global for selected colors (set by main() for render() to use)
SELECTED_COLORS: dict[str, str] = {}

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)


def log_format(keys):
    """
    Generates a list of format strings based on the given keys.

    Args:
        keys (list): A list of string keys that represent the log attributes (e.g., 'asctime', 'levelname').

    Returns:
        list: A list of formatted strings for each key, in the format "%(key)s".
    """
    return [f"%({i})s" for i in keys]


def rotate_log_file(compress=False):
    """
    Truncates the 'latest.jsonl' file after optionally compressing its contents to a timestamped file.
    The 'latest.jsonl' file is not deleted or moved, just emptied.

    Args:
        compress (bool): If True, compress the old log file using gzip.
    """
    if os.path.exists(LATEST_LOG_FILE):
        with open(LATEST_LOG_FILE, "r+", encoding="utf-8") as f:
            first_line = f.readline()
            try:
                first_log = json.loads(first_line)
                first_timestamp = first_log.get("asctime")
                first_timestamp = first_timestamp.split(",")[0]
            except (json.JSONDecodeError, KeyError):
                first_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            safe_timestamp = first_timestamp.replace(":", "-").replace(" ", "_")
            old_log_filename = os.path.join(LOG_DIR, f"{safe_timestamp}.jsonl")

            # Write contents to the new file
            with open(old_log_filename, "w", encoding="utf-8") as old_log_file:
                f.seek(0)  # Go back to the beginning of the file
                shutil.copyfileobj(f, old_log_file)

            if compress:
                with open(old_log_filename, "rb") as f_in:
                    with gzip.open(f"{old_log_filename}.gz", "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(old_log_filename)

            # Truncate the original file
            f.seek(0)
            f.truncate()


def setup_logger(level=logging.INFO):
    """
    Configures the logging system with a custom format and outputs logs in JSON format.

    The logger will write to the 'logs/latest.jsonl' file, and it will include
    multiple attributes such as the time of logging, the filename, function name, log level, etc.

    Returns:
        logging.Logger: A configured logger instance that can be used to log messages.
    """
    _logger = logging.getLogger(name="defaultlogger")

    supported_keys = [
        "asctime",
        "created",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "thread",
        "threadName",
        "taskName",
    ]

    custom_format = " ".join(log_format(supported_keys))
    formatter = jsonlogger.JsonFormatter(custom_format)

    log_handler = logging.FileHandler(LATEST_LOG_FILE)
    log_handler.setFormatter(formatter)

    _logger.addHandler(log_handler)
    _logger.setLevel(level=level)

    return _logger


def setup_consolelogger(level=logging.INFO):
    """
    Configures the logging system to output logs in console and JSON format.

    The logger will write to the 'logs/latest.jsonl' file, and it will include
    multiple attributes such as the time of logging, the filename, function name, log level, etc.

    Returns:
        logging.Logger: A configured logger instance that can be used to log messages.
    """
    _logger = logging.getLogger(name="consolelogger")

    supported_keys = [
        "asctime",
        "created",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "thread",
        "threadName",
        "taskName",
    ]

    custom_format = " ".join(log_format(supported_keys))
    formatter = jsonlogger.JsonFormatter(custom_format)

    log_handler = logging.FileHandler(LATEST_LOG_FILE)
    log_handler.setFormatter(formatter)

    _logger.addHandler(log_handler)
    _logger.addHandler(logging.StreamHandler())
    _logger.setLevel(level=level)
    return _logger


rotate_log_file(compress=True)
logger = setup_logger()


def parse_arguments() -> Args:
    # Define all available effects (used effects enabled by default)
    all_effects = [
        "Blur",
        "ColorOverlay",
        "ColorOverlayBlur",
        "ColorThrough",
        "Flip",
        "InverseBlur",
        "InverseBlurDarker",
        "InverseNegate",
        "InversePixelate",
        "LogoColors",
        "Negate",
        "Pixelate",
        "ThroughBlack",
    ]
    # Default: original 10 + ColorOverlay; ColorOverlayBlur and ColorThrough are optional
    default_effects = [
        "Blur",
        "ColorOverlay",
        "Flip",
        "InverseBlur",
        "InverseBlurDarker",
        "InverseNegate",
        "InversePixelate",
        "LogoColors",
        "Negate",
        "Pixelate",
        "ThroughBlack",
    ]

    # Define all available colors (currently enabled ones + commented optional ones)
    default_colors = ["Black", "White"]  # Default: currently enabled colors

    parser = argparse.ArgumentParser(
        description="Generate styled desktop wallpaper images from SVG masks and source wallpapers.",
        formatter_class=RichHelpFormatter,
    )
    parser.add_argument("-m", "--masks", help="svg masks path", default=SVGDIR, type=str, dest="svgdir", metavar="FOLDER")
    parser.add_argument("-i", "--images", help="input images path", default=WALLPAPERDIR, type=str, dest="wallpaperdir", metavar="FOLDER")
    parser.add_argument("-o", "--out", help="output folder path", default=OUTDIR, type=str, dest="outdir", metavar="FOLDER")
    parser.add_argument(
        "--sync-wallpapers",
        help="pre-sync wallpapers into local cache (uses rsync if available)",
        action="store_true",
        dest="sync_wallpapers",
    )
    parser.add_argument(
        "--effects",
        help=f"space-separated list of effects to generate (default: {' '.join(default_effects)})",
        default=default_effects,
        nargs="+",
        type=str,
        dest="effects",
        choices=all_effects,
        metavar="EFFECT",
    )
    parser.add_argument(
        "--colors",
        help=f"space-separated list of overlay colors (default: {' '.join(default_colors)})",
        default=default_colors,
        nargs="+",
        type=str,
        dest="colors",
        choices=list(ALL_COLORS_DICT.keys()),
        metavar="COLOR",
    )
    parser.add_argument("--generate-help-preview", action=HelpPreviewAction, path="help.svg")
    parsed_args = parser.parse_args()

    _args = Args()
    _args.svgdir = os.path.join(os.getcwd(), parsed_args.svgdir)
    _args.wallpaperdir = os.path.join(os.getcwd(), parsed_args.wallpaperdir)
    _args.outdir = os.path.join(os.getcwd(), parsed_args.outdir)
    _args.sync_wallpapers = getattr(parsed_args, "sync_wallpapers", False)
    _args.effects = parsed_args.effects
    _args.colors = parsed_args.colors

    return _args


def render(arguments: tuple[TempImagePointers, str, str]) -> None:
    """Compose and save a final image for one render task.

    `arguments` is a tuple (tempimages, style, outpath).
    This wrapper exists so the function can be called directly by worker
    processes (via `imap_unordered`).
    """
    tempimages, style, out = arguments
    color = style.removeprefix("ColorOverlay/").removeprefix("ColorOverlayBlur/").removeprefix("ColorThrough/")
    image = Render(tempimages, style, out, SELECTED_COLORS.get(color, None))
    image.render()


def create_mask_temps(arguments: tuple[str, tuple[int, int]]) -> TempMaskPointers:
    """Create and cache rasterized mask, shadow and logocolor files for a given SVG.

    Arguments: (svg_filename_relative, (width, height)). Returns a
    `TempMaskPointers` object with paths to created temp files.
    """
    svg, size = arguments
    pointers = TempMaskPointers()
    tmpmask = BytesIO()

    width, height = size

    pointers.maskname = os.path.splitext(os.path.basename(svg))[0]
    pointers.size = size

    tmpname = f"{pointers.maskname}_{width}x{height}.png"

    if not os.path.exists(os.path.join(TEMPDIR, f"mask_{tmpname}")):
        logger.info("creating mask temp", extra={"mask": svg})
        cairosvg.svg2png(url=os.path.join(SVGDIR, svg), write_to=tmpmask, output_height=height, output_width=width, scale=1)
        colored = Image.open(tmpmask)
        black = ImageEnhance.Brightness(colored)
        mask = black.enhance(factor=0.0)
        mask.save(os.path.join(TEMPDIR, f"mask_{tmpname}"))
        colored.save(os.path.join(TEMPDIR, f"logocolor_{tmpname}"))

        blurred_mask = Image.new("RGB", size, (255, 255, 255))
        blurred_mask.paste(mask, mask=mask)
        shadow = blurred_mask.filter(filter=ImageFilter.GaussianBlur(radius=100))
        shadow.save(os.path.join(TEMPDIR, f"shadow_{tmpname}"))

        mask.close()
        blurred_mask.close()
        shadow.close()

    pointers.mask = os.path.join(TEMPDIR, f"mask_{tmpname}")
    pointers.shadow = os.path.join(TEMPDIR, f"shadow_{tmpname}")
    pointers.logocolor = os.path.join(TEMPDIR, f"logocolor_{tmpname}")

    return pointers


def create_single_effect(arguments: tuple[str, str, tuple[int, int], str]) -> tuple[str, str]:
    """
    Worker function for creating a single effect temporary.
    Arguments: (walfile_path, walname, walsize, effect_name)
    Returns the path to the created effect temporary.
    """
    walfile, walname, walsize, effect = arguments
    creator = EffectCreator(walfile, walname, walsize, effect)
    return creator.execute()


def get_cached_wallpaper(src_path: str) -> str:
    """
    Copy wallpaper from network storage into a persistent local cache directory.
    The cache key is based on the source file's mtime and size so we only recopy
    when the source changes.

    Returns the path to the cached copy.
    """
    # Use a stable cache filename (basename) and let rsync update it when source changes.
    name = os.path.basename(src_path)
    cache_path = os.path.join(CACHE_DIR, name)

    # If cached file exists and matches size+mtime, return it.
    if os.path.exists(cache_path):
        try:
            s_src = os.stat(src_path)
            s_cache = os.stat(cache_path)
            if s_src.st_size == s_cache.st_size and int(s_src.st_mtime) == int(s_cache.st_mtime):
                return cache_path
        except FileNotFoundError:
            pass

    # Prefer rsync for large datasets / network storage
    rsync = shutil.which("rsync")
    if rsync:
        try:
            # Copy into cache directory (rsync will place file with same basename)
            subprocess.run([rsync, "-a", "--update", src_path, CACHE_DIR], check=True)
            # ensure mtime preserved by rsync -a
            return cache_path
        except Exception:
            # fallback to copy2
            pass

    # Fallback: copy file into cache
    shutil.copy2(src_path, cache_path)
    try:
        os.utime(cache_path, (os.path.getatime(src_path), os.path.getmtime(src_path)))
    except Exception:
        pass
    return cache_path


def sync_wallpapers(src_dir: str) -> None:
    """
    Bulk-sync wallpapers directory into the persistent cache directory.
    Uses rsync when available for efficiency; otherwise falls back to per-file copy.
    """
    rsync = shutil.which("rsync")
    if rsync:
        try:
            # ensure trailing slash to copy contents into CACHE_DIR
            src_with_slash = os.path.join(src_dir, "")
            subprocess.run([rsync, "-a", "--update", src_with_slash, CACHE_DIR], check=True)
            return
        except Exception:
            # fall back to manual copy below
            pass

    # Fallback: iterate files and copy individually into cache
    for root, _, files in os.walk(src_dir):
        for f in tqdm(files, desc="[Sync] Copying wallpapers to cache", unit="file", dynamic_ncols=True, ascii=True):
            src = os.path.join(root, f)
            try:
                # reuse existing helper which avoids recopying unchanged files
                get_cached_wallpaper(src)
            except Exception:
                # ignore single-file failures during bulk sync
                logger.warning("failed to sync wallpaper", extra={"file": src})


def compute_chunksize(n_tasks: int, n_workers: int) -> int:
    """Compute a reasonable chunksize for imap_unordered.

    Strategy: give each worker several tasks to reduce IPC overhead. Default
    divisor of 4 balances latency and throughput for medium-sized task lists.
    """
    try:
        n_workers = int(n_workers) if n_workers else 1
    except Exception:
        n_workers = 1
    if n_tasks <= 0:
        return 1
    denom = max(1, n_workers * 4)
    return max(1, n_tasks // denom)


def set_perf_cores_only():
    """
    On Intel hybrid CPUs, restrict to performance cores (P-cores) only.
    P-cores are typically the first N cores (0 to N-1), E-cores are N to total.
    Detection: /proc/cpuinfo lists CPU types (Performance vs Efficiency).
    """
    try:
        import os

        # Try reading /proc/cpuinfo for CPU type info (Linux only)
        if not os.path.exists("/proc/cpuinfo"):
            return  # Not on Linux or hybrid CPU info not available

        with open("/proc/cpuinfo", "r") as f:
            content = f.read()

        # Count P-core vs E-core counts
        p_cores = content.count("cpu family\t: Performance")
        e_cores = content.count("cpu family\t: Efficiency")

        if p_cores == 0 or e_cores == 0:
            # Fallback: assume first half are P-cores (common on 12-core hybrid)
            import multiprocessing

            total = multiprocessing.cpu_count()
            p_cores = total // 2

        if p_cores > 0:
            # Set CPU affinity to P-cores only
            try:
                os.sched_setaffinity(0, set(range(p_cores)))
                logger.info(f"Restricted to P-cores only: cores 0-{p_cores - 1}")
            except AttributeError:
                # sched_setaffinity not available (macOS, Windows)
                logger.warning("CPU affinity not available on this platform")
    except Exception as e:
        logger.warning(f"Failed to set P-core affinity: {e}")


def main():
    motives: list[str] = []
    effectlist: dict[str, list[tuple[str, str, list[str]]]] = {}
    masklist: set[tuple[str, tuple[int, int]]] = set()
    need_img_list = set()
    need_motive_list = set()
    need_style_list = set()
    delete_temps = set()

    missing: dict[str, dict[str, list[str]]] = {}

    args = parse_arguments()

    set_perf_cores_only()

    # Build dynamic STYLES and COLORS from CLI arguments
    selected_effects = args.effects
    selected_colors = args.colors

    # Build STYLES: base effects + color-based variants for each selected color
    dynamic_styles = [e for e in selected_effects if e not in ["ColorOverlay", "ColorOverlayBlur", "ColorThrough"]]
    for color in selected_colors:
        if "ColorOverlay" in selected_effects:
            dynamic_styles.append(f"ColorOverlay/{color}")
        if "ColorOverlayBlur" in selected_effects:
            dynamic_styles.append(f"ColorOverlayBlur/{color}")
        if "ColorThrough" in selected_effects:
            dynamic_styles.append(f"ColorThrough/{color}")

    # Build COLORS dict from selected colors and set global for workers
    global SELECTED_COLORS
    SELECTED_COLORS = {c: ALL_COLORS_DICT[c] for c in selected_colors}

    # If requested, sync the entire wallpapers directory into the persistent cache first.
    if args.sync_wallpapers:
        logger.info("syncing wallpapers into cache", extra={"wallpapers": args.wallpaperdir, "cache": CACHE_DIR})
        try:
            sync_wallpapers(args.wallpaperdir)
        except Exception:
            logger.exception("sync_wallpapers failed")

    try:
        motives = sorted(os.listdir(args.svgdir))
        imgs = sorted(os.listdir(args.wallpaperdir))
        styles = sorted(dynamic_styles)
        for imgfilename in tqdm(imgs, desc="[Check] Scanning wallpapers for missing renders", unit="file", dynamic_ncols=True, ascii=True):
            imgname, ext = os.path.splitext(os.path.basename(imgfilename))
            if ext not in [".jpg", ".jpeg", ".png"]:
                logger.warning("skipping unsupported image file", extra={"file": imgfilename})
                continue
            for motivefile in tqdm(motives, desc=f"[Check] Scanning SVG masks for {imgname}", unit="mask", dynamic_ncols=True, ascii=True, leave=False):
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

        # Reuse a single process pool for all CPU-bound stages
        pool = None

        for imgfilename, v in tqdm(missing.items(), desc="[Cache] Copying wallpapers to temp directory", unit="file", dynamic_ncols=True, ascii=True):
            src = os.path.join(args.wallpaperdir, imgfilename)
            # copy to persistent cache (uses rsync when available)
            walpath = get_cached_wallpaper(src)
            # open briefly to read size and then close to avoid pickling large Image objects
            with Image.open(walpath) as img:
                imgname = os.path.splitext(os.path.basename(imgfilename))[0]
                need_style = set()
                for motivefile, v2 in v.items():
                    motive = os.path.splitext(os.path.basename(motivefile))[0]
                    masklist.add((motivefile, img.size))
                    for style in v2:
                        os.makedirs(os.path.join(args.outdir, motive, imgname), exist_ok=True)
                        need_style.add(style)
            # Only pass file path and metadata to workers (avoid pickling Image objects)
            effectlist[imgfilename] = [(walpath, imgname, sorted(need_style))]

        # create a single pool for mask creation, effect creation and rendering
        cpu = os.cpu_count() or 1
        workers = max(1, cpu - 1)
        pool = Pool(processes=workers)
        mask_tasks = len(masklist)
        mask_chunksize = compute_chunksize(mask_tasks, workers)
        for result in tqdm(
            pool.imap_unordered(create_mask_temps, masklist, chunksize=mask_chunksize),
            total=len(masklist),
            desc="[Process] Creating SVG mask temporaries",
            unit="mask",
            ascii=True,
            dynamic_ncols=True,
        ):
            templist.append(result)

        for wal in effectlist:
            renderlist = []
            # For this wallpaper, create individual effect tasks
            wal_tasks = effectlist[wal]  # List of (walpath, imgname, styles_list) tuples

            for walpath, imgname, styles_list in wal_tasks:
                # Read wallpaper size once
                with Image.open(walpath) as img:
                    walsize = img.size

                # Build individual effect tasks: (walfile, walname, walsize, effect_name)
                # Map styles to the effects they need
                effect_set = set()
                for style in styles_list:
                    if style.startswith("ColorOverlayBlur"):
                        effect_set.add("blurred")
                    elif style == "Blur":
                        effect_set.add("blurred_dark")
                        effect_set.add("brightened")
                    elif style == "InverseBlur":
                        effect_set.add("blurred_dark")
                    elif style == "InverseBlurDarker":
                        effect_set.add("blurred_darker")
                    elif style == "Flip":
                        effect_set.add("flipped")
                    elif style == "Negate":
                        effect_set.add("negated")
                    elif style == "InverseNegate":
                        effect_set.add("negated")
                    elif style == "Pixelate":
                        effect_set.add("pixelated")
                    elif style == "InversePixelate":
                        effect_set.add("pixelated")

                # Create individual tasks for each effect
                effect_tasks_list = []
                for effect in effect_set:
                    effect_tasks_list.append((walpath, imgname, walsize, effect))

                effect_tasks_count = len(effect_tasks_list)
                effect_chunksize = compute_chunksize(effect_tasks_count, workers)

                # Execute effect creation tasks in parallel
                effect_paths = {}
                for effect_path, effect_name in tqdm(
                    pool.imap_unordered(create_single_effect, effect_tasks_list, chunksize=effect_chunksize),
                    total=len(effect_tasks_list),
                    desc=f"[Process] Creating effects for {wal} ({effect_tasks_count} effects)",
                    unit="effect",
                    ascii=True,
                    dynamic_ncols=True,
                ):
                    # Extract effect name from path
                    effect_paths[effect_name] = effect_path

                # Build renderlist using the created effect paths
                for style in styles_list:
                    if "/" in style:
                        parts = style.split("/")
                        out = os.path.join(args.outdir, motive, imgname, parts[1] + parts[0].removeprefix("Color") + ".jpg")
                    else:
                        out = os.path.join(args.outdir, motive, imgname, style + ".jpg")

                    width, height = walsize
                    tmpname = f"{motive}_{width}x{height}.png"
                    pointers = TempImagePointers()
                    pointers.wal = walpath
                    pointers.blurred = effect_paths.get("blurred", "")
                    pointers.blurred_dark = effect_paths.get("blurred_dark", "")
                    pointers.blurred_darker = effect_paths.get("blurred_darker", "")
                    pointers.brightened = effect_paths.get("brightened", "")
                    pointers.flipped = effect_paths.get("flipped", "")
                    pointers.negated = effect_paths.get("negated", "")
                    pointers.pixelated = effect_paths.get("pixelated", "")
                    pointers.mask = os.path.join(TEMPDIR, f"mask_{tmpname}")
                    pointers.shadow = os.path.join(TEMPDIR, f"shadow_{tmpname}")
                    pointers.logocolored = os.path.join(TEMPDIR, f"logocolor_{tmpname}")

                    renderlist.append((pointers, style, out))
                    delete_temps.update(effect_paths.values())

            render_tasks = len(renderlist)
            render_chunksize = compute_chunksize(render_tasks, workers)
            for _ in tqdm(
                pool.imap_unordered(render, renderlist, chunksize=render_chunksize),
                total=len(renderlist),
                desc=f"[Render] Composing final wallpapers for {wal}",
                unit="image",
                ascii=True,
                dynamic_ncols=True,
            ):
                pass

            for tmpfile in delete_temps:
                if os.path.exists(tmpfile):
                    os.remove(tmpfile)
            delete_temps = set()

    finally:
        # ensure pool is closed before removing temp dir
        try:
            if pool is not None:
                pool.close()
                pool.join()
        except Exception:
            pass
        shutil.rmtree(TEMPDIR)


if __name__ == "__main__":
    main()
