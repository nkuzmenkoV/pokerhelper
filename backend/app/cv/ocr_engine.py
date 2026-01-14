import numpy as np
import re
from typing import Optional
import cv2


class OCREngine:
    """OCR engine for reading text from poker table (stacks, pots, blinds)."""
    
    def __init__(self):
        self.reader = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """Lazy initialization of EasyOCR reader."""
        if self._initialized:
            return
        
        try:
            import easyocr
            self.reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            self._initialized = True
        except Exception as e:
            print(f"Failed to initialize EasyOCR: {e}")
            self.reader = None
            self._initialized = True
    
    def preprocess_for_ocr(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results."""
        if image is None or image.size == 0:
            return image
        
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Increase contrast
        gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)
        
        # Apply threshold to get cleaner text
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Resize for better OCR (2x upscale)
        height, width = thresh.shape
        if width < 100:
            thresh = cv2.resize(thresh, (width * 2, height * 2), interpolation=cv2.INTER_CUBIC)
        
        return thresh
    
    def read_text(self, image: np.ndarray) -> str:
        """Read text from image region."""
        self._ensure_initialized()
        
        if self.reader is None or image is None or image.size == 0:
            return ""
        
        processed = self.preprocess_for_ocr(image)
        
        try:
            results = self.reader.readtext(processed, detail=0)
            return " ".join(results)
        except Exception as e:
            print(f"OCR error: {e}")
            return ""
    
    def read_number(self, image: np.ndarray) -> Optional[float]:
        """
        Read a numeric value from image (stack, pot, bet).
        
        Handles formats like:
        - "1,234" -> 1234
        - "1.2K" -> 1200
        - "1.5M" -> 1500000
        - "$500" -> 500
        """
        text = self.read_text(image)
        return self.parse_number(text)
    
    def parse_number(self, text: str) -> Optional[float]:
        """Parse numeric value from text string."""
        if not text:
            return None
        
        # Clean the text
        text = text.strip().upper()
        text = text.replace("$", "").replace(",", "").replace(" ", "")
        
        # Handle K/M/B suffixes
        multiplier = 1
        if text.endswith("K"):
            multiplier = 1000
            text = text[:-1]
        elif text.endswith("M"):
            multiplier = 1000000
            text = text[:-1]
        elif text.endswith("B") or text.endswith("BB"):
            # Could be "BB" (big blinds) or "B" (billion)
            if text.endswith("BB"):
                text = text[:-2]
                multiplier = 1  # Will need context to convert to chips
            else:
                multiplier = 1000000000
                text = text[:-1]
        
        # Extract numeric part
        match = re.search(r'[\d.]+', text)
        if match:
            try:
                value = float(match.group()) * multiplier
                return value
            except ValueError:
                return None
        
        return None
    
    def read_blinds(self, title_image: np.ndarray) -> Optional[tuple[float, float, float]]:
        """
        Read blinds and ante from table title.
        
        Expected formats:
        - "NL Hold'em 100/200" -> (100, 200, 0)
        - "NL 100/200/25" -> (100, 200, 25)
        - "Blinds: 50/100 Ante: 10" -> (50, 100, 10)
        """
        text = self.read_text(title_image)
        
        if not text:
            return None
        
        # Pattern for blinds: number/number or number/number/number
        patterns = [
            r'(\d+(?:[.,]\d+)?)\s*/\s*(\d+(?:[.,]\d+)?)\s*/\s*(\d+(?:[.,]\d+)?)',  # SB/BB/Ante
            r'(\d+(?:[.,]\d+)?)\s*/\s*(\d+(?:[.,]\d+)?)',  # SB/BB
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.replace(",", ""))
            if match:
                groups = match.groups()
                sb = float(groups[0])
                bb = float(groups[1])
                ante = float(groups[2]) if len(groups) > 2 else 0
                return (sb, bb, ante)
        
        # Try to find ante separately
        ante_match = re.search(r'ante[:\s]*(\d+)', text, re.IGNORECASE)
        ante = float(ante_match.group(1)) if ante_match else 0
        
        return None
    
    def read_player_name(self, image: np.ndarray) -> str:
        """Read player name from image."""
        text = self.read_text(image)
        # Clean up common OCR errors in player names
        text = text.strip()
        return text if text else "Unknown"
