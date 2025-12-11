# html-to-pptx-image

Utility script for rendering HTML source material into 16:9, presentation-ready PNG files. It uses Playwright for high-res screenshots and Pillow for final compositing into the target slide canvas.

## Prerequisites

- Python 3.9+ (matching your virtual environment)
- Packages: `pillow`, `playwright`
- One-time browser install for Playwright: `playwright install chromium`

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows PowerShell
pip install pillow playwright
playwright install chromium
```

## Command Overview

All functionality is exposed through `convert_html_to_images.py`.

```bash
python convert_html_to_images.py --help
```

### Positional Argument

- `html_path`: path to the HTML file to capture.

### Shared Options

| Flag | Description |
| --- | --- |
| `--width`, `--height` | Slide canvas in pixels (defaults to 3840x2160 / 4K). |
| `--overwrite` | Force regeneration even if `output/<stem>_slide.png` already exists. |

All renders land under `output/<source-stem>_slides/`, regardless of where the input file lives. The folder is regenerated on every run.

### HTML → Slide

```bash
python convert_html_to_images.py path/to/page.html \
  --wait 2 \
  --zoom 1.0 \
  --mode fill \
  --selector .container \
  --focus-y 0.15 \
  --device-scale-factor 3
```

**Example (Windows PowerShell):**

```powershell
python .\convert_html_to_images.py .\input\sample.html `
  --wait 2 `
  --zoom 1.0 `
  --selector .container `
  --mode fit `
  --device-scale-factor 3
```

Important flags:

| Flag | Description |
| --- | --- |
| `--wait` | Seconds to wait after initial load so fonts/assets settle. |
| `--zoom` | CSS zoom applied before screenshot; useful for tweaking layouts without changing viewport size. |
| `--mode` | `fit` to keep the full capture with potential letterboxing, `fill` to crop and cover the slide. |
| `--selector` | CSS selector for a specific element; omit to capture the full page. |
| `--focus-x`, `--focus-y` | Crop focal point (0–1) when using `fill`. |
| `--device-scale-factor` | Playwright pixel density multiplier (default 2.0). Raising this (2–4) yields sharper PNGs for PowerPoint. |
| `--overwrite` | Re-render even if the PNG already exists (otherwise the script skips existing outputs). |

The script launches Chromium at the requested slide size, captures the page or selector, then composites it on a slide background color (currently `#050508`).

## Tips for Crisp Slides

- Keep `--width/--height` at 4K when targeting 16×9 decks; PowerPoint downscales cleanly.
- For HTML, push `--device-scale-factor` to 3–4 if text still looks soft in presentation mode.
- Use `--mode fit` when you must preserve the entire capture; switch to `fill` plus focus controls when you prefer edge-to-edge coverage.

## Troubleshooting

- **Blurry output**: increase `--device-scale-factor` (HTML) and ensure the slide size stays at least 1920×1080.
- **Missing fonts/assets**: bump `--wait` to give the page more time or ensure static asset paths resolve via `file://`.
- **Selector not found**: verify the CSS selector exists once the page loads; consider using DevTools to inspect the DOM first.

## Directory Layout

```
html-to-slide-image/
├─ convert_html_to_images.py
├─ *.html
├─ output/
│  ├─ <source>_slides/
│  │  └─ *.png
│  └─ ...                 # one folder per source
└─ *.py / assets as needed
```

Run the script from the workspace root so relative HTML paths resolve correctly. Adjust flags to suit each source, and drop the resulting PNG straight into PowerPoint without further tweaks.
