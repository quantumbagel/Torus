import random
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
from PIL import Image
from .config import GeneratorConfig
from .mask import BoundaryMask

class Placement:
    """Stores metadata of a successfully placed image."""
    def __init__(
        self,
        image_path: str,
        x: int,  # top-left x in canvas coordinates
        y: int,  # top-left y in canvas coordinates
        scale: float,
        rotation: float,
        rotated_image: Image.Image
    ):
        self.image_path = image_path
        self.x = x
        self.y = y
        self.scale = scale
        self.rotation = rotation
        self.rotated_image = rotated_image


class ImagePlacer:
    """Core placement logic matching constraints against boundary mask and existing placements."""
    
    def __init__(self, mask: BoundaryMask, config: GeneratorConfig):
        self.mask = mask
        self.config = config
        # Tracks accumulated mask of already placed objects (True where placed)
        self.placed_mask = np.zeros((mask.height, mask.width), dtype=bool)
        self.placements: List[Placement] = []

    def attempt_placement(
        self, 
        image_path: str, 
        img: Image.Image
    ) -> Optional[Placement]:
        """Attempts to place an image on the canvas at random position, scale, and rotation.
        
        Returns the Placement object if successful, else None.
        """
        # Determine scale
        scale = random.uniform(self.config.scale_min, self.config.scale_max)
        new_w = int(img.width * scale)
        new_h = int(img.height * scale)
        
        if new_w <= 0 or new_h <= 0:
            return None
            
        # Determine rotation
        rotation = random.uniform(self.config.rotation_min, self.config.rotation_max)
        
        # Resize and rotate
        resized_img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        if abs(rotation) > 0.001:
            # expand=True changes canvas size so the rotated image fits entirely
            rotated_img = resized_img.rotate(rotation, expand=True, resample=Image.Resampling.BICUBIC)
        else:
            rotated_img = resized_img
            
        # Extract candidate alpha/footprint mask
        if rotated_img.mode != 'RGBA':
            rotated_rgba = rotated_img.convert('RGBA')
        else:
            rotated_rgba = rotated_img
            
        alpha_arr = np.array(rotated_rgba)[:, :, 3]
        candidate_footprint = alpha_arr > 0
        total_footprint_pixels = np.sum(candidate_footprint)
        
        if total_footprint_pixels == 0:
            return None  # empty image
            
        # Pick random center coordinates on the canvas
        cx = random.randint(0, self.mask.width - 1)
        cy = random.randint(0, self.mask.height - 1)
        
        # Top-left coordinates of the bounding box
        rx = cx - rotated_rgba.width // 2
        ry = cy - rotated_rgba.height // 2
        
        H, W = self.mask.height, self.mask.width
        
        # Compute overlapping bounding boxes in source (mask) and candidate coordinate spaces
        src_y_start = max(0, -ry)
        src_x_start = max(0, -rx)
        src_y_end = rotated_rgba.height - max(0, (ry + rotated_rgba.height) - H)
        src_x_end = rotated_rgba.width - max(0, (rx + rotated_rgba.width) - W)
        
        dest_y_start = max(0, ry)
        dest_x_start = max(0, rx)
        dest_y_end = min(H, ry + rotated_rgba.height)
        dest_x_end = min(W, rx + rotated_rgba.width)
        
        # If the overlapping region is invalid, candidate is completely off canvas
        if dest_y_start >= dest_y_end or dest_x_start >= dest_x_end:
            # Entire footprint is off canvas
            off_canvas_pixels = total_footprint_pixels
            on_canvas_pixels = 0
            outside_pixels = off_canvas_pixels
        else:
            cropped_candidate = candidate_footprint[src_y_start:src_y_end, src_x_start:src_x_end]
            on_canvas_pixels = np.sum(cropped_candidate)
            off_canvas_pixels = total_footprint_pixels - on_canvas_pixels
            
            # Boundary Check: pixels inside candidate footprint but outside allowed mask boundary
            cropped_boundary = self.mask.array[dest_y_start:dest_y_end, dest_x_start:dest_x_end]
            outside_pixels_on_canvas = np.sum(cropped_candidate & (~cropped_boundary))
            outside_pixels = off_canvas_pixels + outside_pixels_on_canvas
            
        # 1. Error margin check
        error_ratio = outside_pixels / total_footprint_pixels
        if error_ratio > self.config.allowed_error_margin:
            return None
            
        # 2. Overlap check (only relevant if we have on-canvas pixels)
        if on_canvas_pixels > 0:
            cropped_placed = self.placed_mask[dest_y_start:dest_y_end, dest_x_start:dest_x_end]
            overlap_pixels = np.sum(cropped_candidate & cropped_placed)
            overlap_ratio = overlap_pixels / total_footprint_pixels
            if overlap_ratio > self.config.overlap_allowed:
                return None
        
        # All checks passed! Update internal states
        if on_canvas_pixels > 0:
            self.placed_mask[dest_y_start:dest_y_end, dest_x_start:dest_x_end] |= cropped_candidate
            
        placement = Placement(
            image_path=image_path,
            x=rx,
            y=ry,
            scale=scale,
            rotation=rotation,
            rotated_image=rotated_rgba
        )
        self.placements.append(placement)
        return placement

    def place_all(self, image_paths: List[str]) -> List[Placement]:
        """Runs the placement search loop to find valid coordinates for the config's num_placements."""
        if not image_paths:
            raise ValueError("No candidate images provided to place.")
            
        # Pre-load candidate images to avoid reloading from disk multiple times
        loaded_images = {}
        for path in image_paths:
            try:
                loaded_images[path] = Image.open(path)
            except Exception as e:
                # Log or raise? Let's skip invalid files
                print(f"Warning: Failed to load image {path}: {e}")
                
        valid_paths = list(loaded_images.keys())
        if not valid_paths:
            raise ValueError("No valid candidate images could be loaded.")
            
        successful_placements = 0
        attempts = 0
        
        while successful_placements < self.config.num_placements and attempts < self.config.max_attempts:
            attempts += 1
            # Select random image
            path = random.choice(valid_paths)
            img = loaded_images[path]
            
            placement = self.attempt_placement(path, img)
            if placement:
                successful_placements += 1
                
        # Clean up open file pointers
        for img in loaded_images.values():
            # In PIL, we don't strictly need to close if we've read arrays, but good practice
            pass
            
        return self.placements
