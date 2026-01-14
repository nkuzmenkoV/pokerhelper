import numpy as np
from typing import Optional
from pathlib import Path

from app.poker.game_state import Card
from app.config import get_settings


class CardDetector:
    """Detects and classifies playing cards using YOLOv8."""
    
    # Card rank mapping
    RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    SUITS = ['c', 'd', 'h', 's']  # clubs, diamonds, hearts, spades
    
    # Class names for YOLO model (52 cards)
    CLASS_NAMES = [f"{r}{s}" for s in SUITS for r in RANKS]
    
    def __init__(self):
        self.model = None
        self.settings = get_settings()
    
    async def load_model(self):
        """Load the YOLO model for card detection."""
        model_path = Path(self.settings.yolo_model_path)
        
        if not model_path.exists():
            print(f"Warning: YOLO model not found at {model_path}")
            print("Using fallback template matching for card detection")
            self.model = None
            return
        
        try:
            from ultralytics import YOLO
            self.model = YOLO(str(model_path))
            print(f"Loaded YOLO model from {model_path}")
        except Exception as e:
            print(f"Failed to load YOLO model: {e}")
            self.model = None
    
    def detect_cards(self, image: np.ndarray) -> list[Card]:
        """
        Detect cards in the given image region.
        
        Args:
            image: BGR image (numpy array)
            
        Returns:
            List of detected Card objects
        """
        if image is None or image.size == 0:
            return []
        
        if self.model is not None:
            return self._detect_with_yolo(image)
        else:
            return self._detect_with_template(image)
    
    def _detect_with_yolo(self, image: np.ndarray) -> list[Card]:
        """Detect cards using YOLO model."""
        results = self.model(image, verbose=False)
        cards = []
        
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
            
            for box in boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                
                if conf > 0.5 and cls < len(self.CLASS_NAMES):
                    card_name = self.CLASS_NAMES[cls]
                    rank = card_name[0]
                    suit = card_name[1]
                    
                    # Get bounding box for position
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    
                    cards.append(Card(
                        rank=rank,
                        suit=suit,
                        confidence=conf,
                        bbox=(int(x1), int(y1), int(x2), int(y2))
                    ))
        
        # Sort by x-coordinate (left to right)
        cards.sort(key=lambda c: c.bbox[0] if c.bbox else 0)
        
        return cards
    
    def _detect_with_template(self, image: np.ndarray) -> list[Card]:
        """
        Fallback template matching for card detection.
        This is a simplified version - real implementation would use
        pre-saved card templates from PokerOK.
        """
        import cv2
        
        cards = []
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Simple color-based suit detection
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Red detection (hearts, diamonds)
        red_mask = cv2.inRange(hsv, (0, 100, 100), (10, 255, 255))
        red_mask |= cv2.inRange(hsv, (160, 100, 100), (180, 255, 255))
        
        # Black detection (spades, clubs)
        black_mask = cv2.inRange(hsv, (0, 0, 0), (180, 50, 50))
        
        # TODO: Implement proper template matching with saved card images
        # For now, return empty list
        
        return cards
    
    def card_to_string(self, card: Card) -> str:
        """Convert Card object to string representation (e.g., 'As', 'Kh')."""
        return f"{card.rank}{card.suit}"
    
    def cards_to_hand(self, cards: list[Card]) -> Optional[str]:
        """
        Convert list of cards to hand notation.
        
        Examples:
            [As, Ks] -> "AKs"
            [Ah, Kc] -> "AKo"
            [As, Ad] -> "AA"
        """
        if len(cards) != 2:
            return None
        
        rank1, rank2 = cards[0].rank, cards[1].rank
        suit1, suit2 = cards[0].suit, cards[1].suit
        
        # Sort by rank (A highest)
        rank_order = {r: i for i, r in enumerate(self.RANKS)}
        if rank_order[rank1] < rank_order[rank2]:
            rank1, rank2 = rank2, rank1
            suit1, suit2 = suit2, suit1
        
        if rank1 == rank2:
            return f"{rank1}{rank2}"  # Pocket pair
        elif suit1 == suit2:
            return f"{rank1}{rank2}s"  # Suited
        else:
            return f"{rank1}{rank2}o"  # Offsuit
