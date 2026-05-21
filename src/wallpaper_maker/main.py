#!/usr/bin/env python3
import math
import os
import platform
import shutil
import subprocess
import tempfile
from io import BytesIO
from multiprocessing import Pool
from pathlib import Path

import cairosvg
from PIL import Image, ImageEnhance, ImageFilter
from tqdm.auto import tqdm

from wallpaper_maker.modules.argumentparser import parse_arguments
from wallpaper_maker.modules.effect_creator import EffectCreator
from wallpaper_maker.modules.logger import logger
from wallpaper_maker.modules.render import Render
from wallpaper_maker.modules.util import ALL_COLORS_DICT, TempImagePointers, TempMaskPointers

CWD = os.getcwd()
TEMPDIR = tempfile.mkdtemp()

if platform.system() != "Windows":
    base = Path(os.getenv("XDG_CACHE_HOME", Path.home() / ".cache"))
    CACHE_DIR = base / "wallpaper-maker"
else:
    CACHE_DIR = Path(os.getenv("LOCALAPPDATA", Path.home())) / "wallpaper-maker" / "cache"

CACHE_DIR.mkdir(parents=True, exist_ok=True)


templist: list[TempMaskPointers] = []
renderlist: list[tuple[TempImagePointers, str, str]] = []
# Global for selected colors (set by main() for render() to use)
SELECTED_COLORS: dict[str, str] = {}


def render(arguments: tuple[TempImagePointers, str, str]) -> None:
    """Compose and save a final image for one render task.

    `arguments` is a tuple (tempimages, style, outpath).
    This wrapper exists so the function can be called directly by worker
    processes (via `imap_unordered`).
    """
    tempimages, style, out = arguments
    color = style.removeprefix("ColorOverlay/").removeprefix("ColorOverlayBlur/").removeprefix("ColorThrough/")
    image = Render(tempimages, style, out, color, SELECTED_COLORS)
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
        logger.info("creating mask temp", extra={"mask": svg, "size": size})
        cairosvg.svg2png(url=svg, write_to=tmpmask, output_height=height, output_width=width, scale=1)
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
    creator = EffectCreator(walfile, walname, walsize, effect, TEMPDIR)
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
    return max(1, math.ceil(n_tasks // denom))


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

        with open("/proc/cpuinfo") as f:
            content = f.read()

        # Count P-core vs E-core counts
        p_cores = content.count("cpu family\t: Performance")
        e_cores = content.count("cpu family\t: Efficiency")

        if p_cores == 0 or e_cores == 0:
            # Fallback: assume no P-cores
            import multiprocessing

            total = multiprocessing.cpu_count()
            p_cores = total

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
    pool = None
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
        motives = sorted([os.path.join(args.svgdir, file) for file in os.listdir(args.svgdir)])
        imgs = sorted(os.listdir(args.wallpaperdir))
        styles = sorted(dynamic_styles)
        for imgfilename in tqdm(imgs, desc="[Check] Scanning wallpapers for missing renders", unit="file", dynamic_ncols=True, ascii=True):
            imgname, ext = os.path.splitext(os.path.basename(imgfilename))
            if ext not in [".jpg", ".jpeg", ".png"]:
                logger.warning("skipping unsupported image file", extra={"file": imgfilename})
                continue
            for motivefile in tqdm(
                motives,
                desc=f"[Check] Scanning SVG masks for {imgname}",
                unit="mask",
                dynamic_ncols=True,
                ascii=True,
                leave=False,
            ):
                motive = os.path.splitext(os.path.basename(motivefile))[0]
                for style in styles:
                    if "/" in style:
                        parts = style.split("/")
                        out = os.path.join(args.outdir, motive, imgname, parts[1] + parts[0].removeprefix("Color") + ".jpg")
                    else:
                        out = os.path.join(args.outdir, motive, imgname, style + ".jpg")
                    if not os.path.exists(out):
                        logger.info("missing render detected", extra={"file": out})
                        if not missing.get(imgfilename, False):
                            missing[imgfilename] = {}
                        if not missing[imgfilename].get(motivefile, False):
                            missing[imgfilename][motivefile] = []
                        if style not in missing[imgfilename][motivefile]:
                            missing[imgfilename][motivefile].append(style)
                        need_style_list.add(style)
                        need_img_list.add(imgfilename)
                        need_motive_list.add(motive)

        need_style_list = sorted(need_style_list)
        need_img_list = sorted(need_img_list)
        need_motive_list = sorted(need_motive_list)

        print(f"Temp Masks to be created: {len(need_motive_list)}")
        print(", ".join(need_motive_list))
        print(f"Wallpapers needed: {len(need_img_list)}")
        print(", ".join(need_img_list))
        print(f"Styles to be made: {len(need_style_list)}")
        print(", ".join(need_style_list))

        for imgfilename, v in tqdm(
            missing.items(),
            desc="[Cache] Copying wallpapers to temp directory",
            unit="file",
            dynamic_ncols=True,
            ascii=True,
        ):
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
        workers = max(1, cpu)
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
                for motivefile, _ in masklist:
                    motive = os.path.splitext(os.path.basename(motivefile))[0]
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

    except Exception as e:
        logger.error(e)

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
