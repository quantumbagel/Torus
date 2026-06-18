from typing import List
import numpy as np
from PIL import Image
from .config import GeneratorConfig
from .mask import BoundaryMask
from .placer import Placement

class Renderer:
    """Handles rendering the placed images on the final canvas with the specified background."""

    def __init__(self, mask: BoundaryMask, config: GeneratorConfig):
        self.mask = mask
        self.config = config

    def render(self, placements: List[Placement]) -> Image.Image:
        """Composites the placements onto a canvas and returns the PIL Image."""
        # Setup background color
        if self.config.bg_color is None:
            bg = (0, 0, 0, 0)  # Transparent
        else:
            bg = self.config.bg_color

        # Always start with RGBA to handle transparency correctly
        canvas = Image.new("RGBA", (self.mask.width, self.mask.height), bg)

        # Composite placements in the order they were placed (chronological layering)
        for placement in placements:
            # paste(image, box, mask) where mask uses alpha channel for transparency
            canvas.paste(
                placement.rotated_image, 
                (placement.x, placement.y), 
                placement.rotated_image
            )

        # Apply clipping to boundary mask if configured
        if self.config.clip_to_mask:
            canvas_arr = np.array(canvas)
            # Mask is True where allowed, False where forbidden.
            # Wherever mask is False (outside boundary), set alpha (channel 3) to 0.
            # (Works because we ensure canvas is in RGBA mode)
            canvas_arr[~self.mask.array, 3] = 0
            canvas = Image.fromarray(canvas_arr)

        return canvas
