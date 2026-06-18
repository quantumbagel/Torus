import numpy as np
from PIL import Image

class BoundaryMask:
    """Represents the black and white source image boundary mask."""

    def __init__(self, mask_array: np.ndarray):
        # mask_array is a boolean NumPy array (True for active/allowed area, False for forbidden)
        self.array = mask_array
        self.height, self.width = mask_array.shape

    @classmethod
    def load(cls, filepath: str, invert: bool = False) -> 'BoundaryMask':
        """Loads a boundary mask from an image file.
        
        By default, white pixels (or values > 127) represent allowed areas.
        If invert is True, black pixels (or values <= 127) represent allowed areas.
        """
        with Image.open(filepath) as img:
            # Convert to grayscale
            gray_img = img.convert('L')
            gray_arr = np.array(gray_img)
            
            # Create boolean mask: values > 127 are True
            mask_arr = gray_arr > 127
            
            if invert:
                mask_arr = ~mask_arr
                
            return cls(mask_arr)
            
    def is_allowed(self, x: int, y: int) -> bool:
        """Returns True if the coordinate is within the allowed boundary."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return bool(self.array[y, x])
        return False
