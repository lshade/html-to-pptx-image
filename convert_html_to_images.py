from __future__ import annotations

import argparse
import io
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image
from playwright.sync_api import sync_playwright

SLIDE_SIZE = (3840, 2160)
OUTPUT_ROOT = Path(__file__).resolve().parent / "output"


def compose_slide(
    image: Image.Image,
    slide_size: Tuple[int, int],
    mode: str,
    focus_x: float = 0.5,
    focus_y: float = 0.5,
    background_color: Tuple[int, int, int] = (255, 255, 255),
) -> Image.Image:
    target_w, target_h = slide_size
    focus_x = min(max(focus_x, 0.0), 1.0)
    focus_y = min(max(focus_y, 0.0), 1.0)
    if mode == "fill":
        scale = max(target_w / image.width, target_h / image.height)
    else:
        scale = min(target_w / image.width, target_h / image.height)

    new_size = (int(image.width * scale), int(image.height * scale))
    resized = image.resize(new_size, Image.LANCZOS)

    if mode == "fill":
        max_x = max(new_size[0] - target_w, 0)
        max_y = max(new_size[1] - target_h, 0)
        left = int(max_x * focus_x)
        top = int(max_y * focus_y)
        right = left + target_w
        bottom = top + target_h
        cropped = resized.crop((left, top, right, bottom))
        return cropped

    canvas = Image.new("RGB", slide_size, color=background_color)
    offset = ((target_w - new_size[0]) // 2, (target_h - new_size[1]) // 2)
    canvas.paste(resized, offset)
    return canvas


def html_to_slide_image(
    html_path: Path,
    slide_size: Tuple[int, int],
    wait_time: float,
    zoom: float,
    mode: str,
    focus_x: float,
    focus_y: float,
    selector: Optional[str],
    device_scale_factor: float,
    overwrite: bool,
) -> None:
    html_path = html_path.expanduser().resolve()
    if not html_path.is_file():
        raise FileNotFoundError(f"HTML file not found: {html_path}")

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    output_dir = OUTPUT_ROOT / f"{html_path.stem}_slides"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{html_path.stem}_slide.png"

    if output_path.exists() and not overwrite:
        print(f"Skipping {output_path} (already exists, use --overwrite to regenerate)")
        return

    scale_factor = max(1.0, device_scale_factor)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(
            viewport={"width": slide_size[0], "height": slide_size[1]},
            device_scale_factor=scale_factor,
        )
        page.goto(html_path.as_uri(), wait_until="load")
        page.wait_for_timeout(wait_time * 1000)
        if zoom != 1.0:
            page.evaluate(
                "(value) => { document.body.style.transformOrigin = 'top left'; document.body.style.zoom = value; }",
                zoom,
            )
        if selector:
            page.wait_for_selector(selector)
            screenshot_bytes = page.locator(selector).screenshot(type="png")
        else:
            screenshot_bytes = page.screenshot(full_page=True)
        browser.close()

    image = Image.open(io.BytesIO(screenshot_bytes))
    slide_image = compose_slide(
        image,
        slide_size,
        mode=mode,
        focus_x=focus_x,
        focus_y=focus_y,
        background_color=(5, 5, 8),
    )
    slide_image.save(output_path, format="PNG")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create 16x9 slide-ready images from HTML inputs.")
    parser.add_argument("html_path", type=Path, help="Path to the HTML file to capture")
    parser.add_argument("--width", type=int, default=SLIDE_SIZE[0], help="Slide width in pixels (default: 3840)")
    parser.add_argument("--height", type=int, default=SLIDE_SIZE[1], help="Slide height in pixels (default: 2160)")
    parser.add_argument("--wait", type=float, default=1.0, help="Seconds to wait after load for assets (default: 1.0)")
    parser.add_argument(
        "--zoom",
        type=float,
        default=1.0,
        help="CSS zoom factor applied before screenshot (default: 1.0)",
    )
    parser.add_argument(
        "--mode",
        choices=("fit", "fill"),
        default="fit",
        help="Fit keeps full content with letterbox, fill crops to cover the slide (default: fit)",
    )
    parser.add_argument(
        "--selector",
        type=str,
        default=None,
        help="Optional CSS selector to screenshot instead of the full page",
    )
    parser.add_argument(
        "--focus-x",
        type=float,
        default=0.5,
        help="Horizontal crop focus 0-1 when using fill (default: 0.5 center)",
    )
    parser.add_argument(
        "--focus-y",
        type=float,
        default=0.5,
        help="Vertical crop focus 0-1 when using fill (default: 0.5 center)",
    )
    parser.add_argument(
        "--device-scale-factor",
        type=float,
        default=2.0,
        help="Playwright device scale factor for crisper screenshots (default: 2.0)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Regenerate the PNG even if it already exists",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    slide_size = (args.width, args.height)

    html_to_slide_image(
        args.html_path,
        slide_size=slide_size,
        wait_time=args.wait,
        zoom=args.zoom,
        mode=args.mode,
        focus_x=args.focus_x,
        focus_y=args.focus_y,
        selector=args.selector,
        device_scale_factor=args.device_scale_factor,
        overwrite=args.overwrite,
    )


if __name__ == "__main__":
    main()
