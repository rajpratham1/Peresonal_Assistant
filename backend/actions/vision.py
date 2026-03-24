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
