import argparse
import os

from rich_argparse import HelpPreviewAction, RichHelpFormatter

from wallpaper_maker.modules.util import ALL_COLORS_DICT

CWD = os.getcwd()
SVGDIR = os.path.join(CWD, "Svgs")
WALLPAPERDIR = os.path.join(CWD, "Wallpapers")
OUTDIR = os.path.join(CWD, "Render")


class Args:
    svgdir: str
    wallpaperdir: str
    outdir: str
    sync_wallpapers: bool
    effects: list[str]
    colors: list[str]


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
    parser.add_argument(
        "-i",
        "--images",
        help="input images path",
        default=WALLPAPERDIR,
        type=str,
        dest="wallpaperdir",
        metavar="FOLDER",
    )
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
