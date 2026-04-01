"""Image recognition utilities using OpenCV template matching."""

import os
import cv2
import numpy as np
from PIL import Image
from typing import Optional, Tuple

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "templates")


def load_template(relative_path: str) -> Optional[np.ndarray]:
    """Load a template image from assets/templates/."""
    full_path = os.path.join(TEMPLATES_DIR, relative_path)
    if not os.path.exists(full_path):
        return None
    return cv2.imread(full_path, cv2.IMREAD_COLOR)


def pil_to_cv2(pil_image: Image.Image) -> np.ndarray:
    """Convert PIL image to OpenCV BGR array."""
    return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)


def find_template(
    screenshot: np.ndarray,
    template: np.ndarray,
    threshold: float = 0.8,
) -> Optional[Tuple[int, int]]:
    """
    Find a template in a screenshot using normalized cross-correlation.

    Returns the (x, y) center of the best match if confidence >= threshold,
    otherwise None.
    """
    if screenshot is None or template is None:
        return None
    # OpenCV requires both arrays to be the same type and at most 2-D depth
    if screenshot.dtype != template.dtype:
        template = template.astype(screenshot.dtype)
    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    if max_val >= threshold:
        h, w = template.shape[:2]
        cx = max_loc[0] + w // 2
        cy = max_loc[1] + h // 2
        return cx, cy
    return None


def find_template_by_name(
    screenshot: np.ndarray,
    template_name: str,
    threshold: float = 0.8,
) -> Optional[Tuple[int, int]]:
    """Convenience wrapper — loads template by relative path and searches."""
    template = load_template(template_name)
    if template is None:
        return None
    return find_template(screenshot, template, threshold)


def is_on_screen(
    screenshot: np.ndarray,
    template_name: str,
    threshold: float = 0.8,
) -> bool:
    """Return True if the template is visible in the screenshot."""
    return find_template_by_name(screenshot, template_name, threshold) is not None
