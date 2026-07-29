import argparse
import os
import sys
import glob
from typing import List, Tuple, Union, Optional
from PIL import ImageColor

from .config import GeneratorConfig
from .mask import BoundaryMask
from .placer import ImagePlacer
from .renderer import Renderer

def parse_color(color_str: str) -> Optional[Union[str, Tuple[int, ...]]]:
    """Parses background color option into a format PIL understands."""
    if not color_str or color_str.lower() == 'transparent':
        return None
        
    # Check if comma separated integers
    if ',' in color_str:
        try:
            parts = tuple(int(x.strip()) for x in color_str.split(','))
            if len(parts) in (3, 4):
                return parts
        except ValueError:
            pass
            
    # Try parsing as standard color name/hex code
    try:
        ImageColor.getrgb(color_str)
        return color_str
    except ValueError:
        print(f"Warning: Could not parse color '{color_str}', defaulting to transparent.")
        return None

def find_images(source_path: str) -> List[str]:
    """Finds image files given a file path or directory."""
    if os.path.isfile(source_path):
        return [source_path]
        
    if os.path.isdir(source_path):
        patterns = ['*.png', '*.PNG', '*.jpg', '*.JPG', '*.jpeg', '*.JPEG', '*.webp', '*.WEBP']
        found = []
        for pattern in patterns:
            found.extend(glob.glob(os.path.join(source_path, pattern)))
        return sorted(found)
        
    return []

def main():
    parser = argparse.ArgumentParser(
        description="Generate profile pictures by randomly placing overlay images within a boundary mask."
    )
    parser.add_argument("mask_path", help="Path to the black-and-white boundary mask image.")
    parser.add_argument("overlays_path", help="Path to a directory of transparent overlays or a single overlay file.")
    parser.add_argument("output_path", help="Path where the generated output image will be saved.")
    
    parser.add_argument("--error-margin", type=float, default=0.0,
                        help="Maximum percentage (0.0 to 1.0) of overlay pixels allowed outside the mask boundary (default: 0.0).")
    parser.add_argument("--overlap", type=float, default=0.0,
                        help="Maximum percentage (0.0 to 1.0) of overlay pixels allowed to overlap existing placements (default: 0.0).")
    parser.add_argument("--num-placements", type=int, default=50,
                        help="Number of images to place (default: 50).")
    parser.add_argument("--max-attempts", type=int, default=1000,
                        help="Max total simulation placement attempts before giving up (default: 1000).")
    parser.add_argument("--scale-min", type=float, default=0.5,
                        help="Minimum scaling factor (default: 0.5).")
    parser.add_argument("--scale-max", type=float, default=1.2,
                        help="Maximum scaling factor (default: 1.2).")
    parser.add_argument("--rotation-min", type=float, default=0.0,
                        help="Minimum rotation in degrees (default: 0.0).")
    parser.add_argument("--rotation-max", type=float, default=0.0,
                        help="Maximum rotation in degrees (default: 0.0).")
    parser.add_argument("--random-tint", type=float, default=0.0,
                        help="Maximum random tint strength (0.0 to 1.0) applied per placed image; darkens toward black or lightens toward white (default: 0.0).")
    parser.add_argument("--bg-color", default="transparent",
                        help="Background color. Can be 'transparent', color name (e.g. 'white'), hex (e.g. '#ffffff'), or R,G,B (default: transparent).")
    parser.add_argument("--clip-to-mask", action="store_true",
                        help="Clip the final output composite to the boundary mask.")
    parser.add_argument("--invert-mask", action="store_true",
                        help="Invert the source mask (treat black as placement area, white as forbidden).")

    args = parser.parse_args()

    if not (0.0 <= args.random_tint <= 1.0):
        print("Error: --random-tint must be between 0.0 and 1.0.", file=sys.stderr)
        sys.exit(1)

    # Verify input paths
    if not os.path.exists(args.mask_path):
        print(f"Error: Mask file not found: {args.mask_path}", file=sys.stderr)
        sys.exit(1)
        
    overlay_images = find_images(args.overlays_path)
    if not overlay_images:
        print(f"Error: No overlay images found at: {args.overlays_path}", file=sys.stderr)
        sys.exit(1)

    # Build Configuration
    config = GeneratorConfig(
        allowed_error_margin=args.error_margin,
        overlap_allowed=args.overlap,
        num_placements=args.num_placements,
        max_attempts=args.max_attempts,
        scale_min=args.scale_min,
        scale_max=args.scale_max,
        rotation_min=args.rotation_min,
        rotation_max=args.rotation_max,
        random_tint=args.random_tint,
        bg_color=parse_color(args.bg_color),
        clip_to_mask=args.clip_to_mask,
        invert_mask=args.invert_mask
    )

    print(f"Loading boundary mask from {args.mask_path}...")
    try:
        mask = BoundaryMask.load(args.mask_path, invert=config.invert_mask)
    except Exception as e:
        print(f"Error: Failed to load mask: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(overlay_images)} overlay images.")
    print("Running simulation placement engine...")
    
    placer = ImagePlacer(mask, config)
    placements = placer.place_all(overlay_images)
    
    print(f"Successfully placed {len(placements)} images out of {config.num_placements} target placements.")

    print("Compositing and rendering...")
    renderer = Renderer(mask, config)
    output_image = renderer.render(placements)

    # Ensure output directory exists
    out_dir = os.path.dirname(args.output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    print(f"Saving generated image to {args.output_path}...")
    try:
        output_image.save(args.output_path)
        print("Success!")
    except Exception as e:
        print(f"Error: Failed to save output image: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
