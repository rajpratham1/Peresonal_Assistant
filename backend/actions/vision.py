import os
from datetime import datetime
try:
    import easyocr
except ImportError:
    easyocr = None

from backend.actions.system_control import take_screenshot
from backend.config import PROJECT_ROOT

_READER = None

def get_reader():
    """Load the EasyOCR engine. Done lazily so it doesn't block startup."""
    global _READER
    if _READER is None and easyocr is not None:
        _READER = easyocr.Reader(['en'])
    return _READER

def read_screen() -> str:
    """Takes a screenshot of the display, extracts text via PyTorch, and returns it."""
    if easyocr is None:
        return "OCR module is not installed."
        
    reader = get_reader()
    if not reader:
         return "Could not initialize the optical character reader."
         
    tmp_path = PROJECT_ROOT / "screenshots" / f"ocr_{datetime.now().strftime('%Y%m%d-%H%M%S')}.png"
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    take_screenshot(str(tmp_path))
    
    try:
        result = reader.readtext(str(tmp_path), detail=0)
        os.remove(tmp_path)
    except Exception as e:
        return f"Optical vision failed: {e}"
        
    text = " ".join(result).strip()
    return text if text else "I don't see any text on your screen right now."

def find_text_coordinates(target_text: str) -> tuple[int, int] | None:
    """Finds the (x, y) coordinates of a specific text on screen."""
    if easyocr is None:
        return None
        
    reader = get_reader()
    if not reader:
        return None
        
    tmp_path = PROJECT_ROOT / "screenshots" / "ocr_click.png"
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    take_screenshot(str(tmp_path))
    
    try:
        # detail=1 returns [[coords], text, confidence]
        results = reader.readtext(str(tmp_path), detail=1)
        os.remove(tmp_path)
        
        target_lower = target_text.lower()
        for (bbox, text, prob) in results:
            if target_lower in text.lower():
                # bbox is [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
                # Find center point
                center_x = int((bbox[0][0] + bbox[1][0]) / 2)
                center_y = int((bbox[0][1] + bbox[2][1]) / 2)
                return (center_x, center_y)
    except Exception:
        pass
    return None
