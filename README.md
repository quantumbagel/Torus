# Torus PFP generator

A modular Python command-line tool to generate custom collages or profile pictures (PFPs) by randomly placing overlay images inside the active area of a black-and-white boundary mask.

## Installation

1. Clone or download this project.
2. Initialize a virtual environment (optional but recommended):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On macOS/Linux
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Quick Start

### Example
To verify the system with simple shapes:
1. Run the test asset generator script to prepare temporary images:
   ```bash
   python3 -m pytest tests/test_generator.py
   ```
2. Generate a collage using the command-line utility:
   ```bash
   python3 main.py donut_mask.png teto_images teto_donut_pfp.png \
     --num-placements 120 \
     --overlap 0.6 \
     --error-margin 0.15 \
     --scale-min 0.05 \
     --scale-max 0.25 \
     --rotation-min -180 \
     --rotation-max 180 \
     --random-tint 0.2 \
     --clip-to-mask
   ```

## CLI Reference

```bash
python3 main.py <mask_path> <overlays_path> <output_path> [options]
```

### Positional Arguments
- `mask_path`: Path to the black-and-white boundary mask image.
- `overlays_path`: Path to a directory containing transparent PNG overlays, or a single overlay file.
- `output_path`: Filename or path where the generated image will be saved.

### Optional Arguments
- `--error-margin <float>`: Maximum percentage (`0.0` to `1.0`) of overlay pixels allowed to fall outside the allowed mask area (default: `0.0`).
- `--overlap <float>`: Maximum percentage (`0.0` to `1.0`) of overlay pixels allowed to overlap with previously placed items (default: `0.0`).
- `--num-placements <int>`: Total number of overlays to attempt to place (default: `50`).
- `--max-attempts <int>`: Search budget limit for placement iterations before stopping (default: `1000`).
- `--scale-min <float>`: Minimum scaling factor of the overlay (default: `0.5`).
- `--scale-max <float>`: Maximum scaling factor of the overlay (default: `1.2`).
- `--rotation-min <float>`: Minimum rotation angle in degrees (default: `0.0`).
- `--rotation-max <float>`: Maximum rotation angle in degrees (default: `0.0`).
- `--random-tint <float>`: Maximum random tint strength (`0.0` to `1.0`) applied per placement, darkening toward black or lightening toward white. At `1.0`, placements can reach full black/white extremes (default: `0.0`).
- `--bg-color <str>`: Background canvas color. Can be `transparent` (default), a standard name (e.g. `white`, `red`), hex (e.g. `#ffffff`), or R,G,B integers (e.g. `255,255,255`).
- `--clip-to-mask`: Clips any parts of the overlays that extend outside the boundary mask at rendering time.
- `--invert-mask`: Inverts the boundary mask (treats black pixels as the allowed placement area and white as forbidden).