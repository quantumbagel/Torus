from dataclasses import dataclass
from typing import Optional, Union, Tuple

@dataclass
class GeneratorConfig:
    """Configuration options for the PFP generator."""
    allowed_error_margin: float = 0.0  # Max fraction of overlay pixels allowed outside mask
    overlap_allowed: float = 0.0       # Max fraction of overlay pixels allowed to overlap existing placements
    num_placements: int = 50           # Number of successful placements to attempt
    max_attempts: int = 1000           # Max total candidate placement attempts
    scale_min: float = 0.5             # Minimum scale factor
    scale_max: float = 1.2             # Maximum scale factor
    rotation_min: float = 0.0          # Minimum rotation angle in degrees
    rotation_max: float = 0.0          # Maximum rotation angle in degrees (0.0 to 0.0 means no rotation)
    random_tint: float = 0.0           # Max random brightness shift (0.0 to 1.0) per placement
    bg_color: Optional[Union[str, Tuple[int, int, int], Tuple[int, int, int, int]]] = None  # None means transparent
    clip_to_mask: bool = False         # If True, clip overlay images to boundary at render time
    invert_mask: bool = False          # If True, treat black as allowed and white as forbidden area
