"""
Auto-detector for card regions in poker table screenshots.

Uses color analysis and contour detection to find potential card regions
before the model is trained, and uses the trained model afterwards.
"""

import cv2
import numpy as np
from typing import Optional
from pathlib import Path
from dataclasses import dataclass, field
import base64
import json


@dataclass
class DetectedRegion:
    """A detected card region."""
    x: int  # Top-left x (pixels)
    y: int  # Top-left y (pixels)
    width: int  # Width (pixels)
    height: int  # Height (pixels)
    confidence: float  # Detection confidence
    suggested_class: Optional[str] = None  # If model detected it
    region_type: str = "card"  # card, board, hero
    position_index: int = -1  # Index within position type (e.g., board card 0-4)
    
    def to_normalized(self, img_width: int, img_height: int) -> dict:
        """Convert to normalized coordinates (0-1)."""
        x_center = (self.x + self.width / 2) / img_width
        y_center = (self.y + self.height / 2) / img_height
        w = self.width / img_width
        h = self.height / img_height
        return {
            "x_center": x_center,
            "y_center": y_center,
            "width": w,
            "height": h,
            "x": self.x,
            "y": self.y,
            "pixel_width": self.width,
            "pixel_height": self.height,
            "confidence": self.confidence,
            "suggested_class": self.suggested_class,
            "region_type": self.region_type,
            "position_index": self.position_index,
        }


@dataclass
class CardPosition:
    """Configuration for a card position on the table."""
    x: float  # Normalized x (0-1)
    y: float  # Normalized y (0-1)
    width: float  # Normalized width
    height: float  # Normalized height
    region_type: str  # "hero", "board", "opponent"
    index: int = 0  # Position index


@dataclass 
class PokerOKLayout:
    """
    PokerOK table layout configuration.
    
    Contains preset positions for different table sizes and resolutions.
    Users can calibrate and save custom positions.
    """
    name: str = "default"
    
    # Hero cards (2 cards, bottom center)
    hero_cards: list[CardPosition] = field(default_factory=list)
    
    # Board cards (5 cards, center)
    board_cards: list[CardPosition] = field(default_factory=list)
    
    # Opponent card positions (for showdown, by seat)
    opponent_cards: dict[int, list[CardPosition]] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.hero_cards:
            self.hero_cards = self._default_hero_positions()
        if not self.board_cards:
            self.board_cards = self._default_board_positions()
    
    def _default_hero_positions(self) -> list[CardPosition]:
        """Default hero card positions for PokerOK."""
        # These are typical positions for hero cards
        return [
            CardPosition(x=0.435, y=0.68, width=0.045, height=0.10, region_type="hero", index=0),
            CardPosition(x=0.485, y=0.68, width=0.045, height=0.10, region_type="hero", index=1),
        ]
    
    def _default_board_positions(self) -> list[CardPosition]:
        """Default board card positions for PokerOK."""
        # 5 community cards in the center
        base_x = 0.315
        spacing = 0.055
        return [
            CardPosition(x=base_x + i * spacing, y=0.38, width=0.045, height=0.095, region_type="board", index=i)
            for i in range(5)
        ]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "hero_cards": [
                {"x": c.x, "y": c.y, "width": c.width, "height": c.height, "index": c.index}
                for c in self.hero_cards
            ],
            "board_cards": [
                {"x": c.x, "y": c.y, "width": c.width, "height": c.height, "index": c.index}
                for c in self.board_cards
            ],
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PokerOKLayout':
        """Create from dictionary."""
        layout = cls(name=data.get("name", "custom"))
        
        if "hero_cards" in data:
            layout.hero_cards = [
                CardPosition(
                    x=c["x"], y=c["y"], width=c["width"], height=c["height"],
                    region_type="hero", index=c.get("index", i)
                )
                for i, c in enumerate(data["hero_cards"])
            ]
        
        if "board_cards" in data:
            layout.board_cards = [
                CardPosition(
                    x=c["x"], y=c["y"], width=c["width"], height=c["height"],
                    region_type="board", index=c.get("index", i)
                )
                for i, c in enumerate(data["board_cards"])
            ]
        
        return layout


# Preset layouts for different PokerOK configurations
POKEROK_PRESETS = {
    # Standard 6-max table
    "6max_default": PokerOKLayout(
        name="6max_default",
        hero_cards=[
            CardPosition(x=0.435, y=0.68, width=0.045, height=0.10, region_type="hero", index=0),
            CardPosition(x=0.485, y=0.68, width=0.045, height=0.10, region_type="hero", index=1),
        ],
        board_cards=[
            CardPosition(x=0.315, y=0.38, width=0.045, height=0.095, region_type="board", index=0),
            CardPosition(x=0.370, y=0.38, width=0.045, height=0.095, region_type="board", index=1),
            CardPosition(x=0.425, y=0.38, width=0.045, height=0.095, region_type="board", index=2),
            CardPosition(x=0.480, y=0.38, width=0.045, height=0.095, region_type="board", index=3),
            CardPosition(x=0.535, y=0.38, width=0.045, height=0.095, region_type="board", index=4),
        ],
    ),
    
    # Standard 9-max table
    "9max_default": PokerOKLayout(
        name="9max_default",
        hero_cards=[
            CardPosition(x=0.435, y=0.70, width=0.042, height=0.09, region_type="hero", index=0),
            CardPosition(x=0.480, y=0.70, width=0.042, height=0.09, region_type="hero", index=1),
        ],
        board_cards=[
            CardPosition(x=0.320, y=0.40, width=0.042, height=0.088, region_type="board", index=0),
            CardPosition(x=0.370, y=0.40, width=0.042, height=0.088, region_type="board", index=1),
            CardPosition(x=0.420, y=0.40, width=0.042, height=0.088, region_type="board", index=2),
            CardPosition(x=0.470, y=0.40, width=0.042, height=0.088, region_type="board", index=3),
            CardPosition(x=0.520, y=0.40, width=0.042, height=0.088, region_type="board", index=4),
        ],
    ),
    
    # Wide screen / larger resolution
    "wide_6max": PokerOKLayout(
        name="wide_6max",
        hero_cards=[
            CardPosition(x=0.440, y=0.65, width=0.040, height=0.095, region_type="hero", index=0),
            CardPosition(x=0.485, y=0.65, width=0.040, height=0.095, region_type="hero", index=1),
        ],
        board_cards=[
            CardPosition(x=0.330, y=0.36, width=0.040, height=0.085, region_type="board", index=0),
            CardPosition(x=0.378, y=0.36, width=0.040, height=0.085, region_type="board", index=1),
            CardPosition(x=0.426, y=0.36, width=0.040, height=0.085, region_type="board", index=2),
            CardPosition(x=0.474, y=0.36, width=0.040, height=0.085, region_type="board", index=3),
            CardPosition(x=0.522, y=0.36, width=0.040, height=0.085, region_type="board", index=4),
        ],
    ),
}


class CardAutoDetector:
    """
    Automatically detects card regions in poker screenshots.
    
    Uses a combination of:
    1. Color-based detection (white card backgrounds)
    2. Contour analysis (rectangular shapes)
    3. Position heuristics (expected card locations)
    4. Trained YOLO model (when available)
    """
    
    # Expected card aspect ratio (width/height)
    CARD_ASPECT_RATIO = 0.7
    ASPECT_TOLERANCE = 0.3
    
    # Minimum and maximum card sizes (as fraction of image)
    MIN_CARD_SIZE = 0.02
    MAX_CARD_SIZE = 0.15
    
    # White card detection thresholds
    WHITE_THRESHOLD = 200
    
    # Brightness threshold for card presence
    CARD_BRIGHTNESS_THRESHOLD = 100
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        layout: Optional[PokerOKLayout] = None,
        config_path: str = "data/detector_config.json",
    ):
        self.model = None
        self.model_path = model_path
        self.config_path = Path(config_path)
        
        # Load or use default layout
        self.layout = layout or self._load_layout()
        
        if model_path and Path(model_path).exists():
            self._load_model(model_path)
    
    def _load_layout(self) -> PokerOKLayout:
        """Load layout from config file or use default."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    return PokerOKLayout.from_dict(data.get("layout", {}))
            except Exception as e:
                print(f"Failed to load layout config: {e}")
        
        return POKEROK_PRESETS["6max_default"]
    
    def save_layout(self, layout: Optional[PokerOKLayout] = None):
        """Save current or provided layout to config."""
        layout = layout or self.layout
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, 'w') as f:
            json.dump({"layout": layout.to_dict()}, f, indent=2)
    
    def set_layout(self, layout: PokerOKLayout):
        """Set and save new layout."""
        self.layout = layout
        self.save_layout()
    
    def set_preset(self, preset_name: str):
        """Set layout from preset."""
        if preset_name in POKEROK_PRESETS:
            self.layout = POKEROK_PRESETS[preset_name]
            self.save_layout()
            return True
        return False
    
    def get_available_presets(self) -> list[str]:
        """Get list of available preset names."""
        return list(POKEROK_PRESETS.keys())
    
    def _load_model(self, model_path: str):
        """Load YOLO model for detection."""
        try:
            from ultralytics import YOLO
            self.model = YOLO(model_path)
            print(f"Loaded detection model from {model_path}")
        except Exception as e:
            print(f"Failed to load model: {e}")
            self.model = None
    
    def reload_model(self, model_path: str):
        """Reload model from new path."""
        self._load_model(model_path)
    
    def detect_regions(
        self,
        image_data: str,  # Base64 encoded
        use_model: bool = True,
        use_heuristics: bool = True,
        use_positions: bool = True,
    ) -> list[dict]:
        """
        Detect card regions in image.
        
        Args:
            image_data: Base64 encoded image
            use_model: Use trained model if available
            use_heuristics: Use color/contour detection
            use_positions: Use configured position presets
        
        Returns:
            List of detected regions
        """
        # Decode image
        img_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return []
        
        height, width = img.shape[:2]
        regions = []
        
        # Use trained model if available (highest priority)
        if use_model and self.model is not None:
            model_regions = self._detect_with_model(img)
            regions.extend(model_regions)
        
        # Use configured positions (medium priority)
        if use_positions and not regions:
            position_regions = self._detect_at_positions(img)
            regions.extend(position_regions)
        
        # Use heuristic detection (lowest priority, fills gaps)
        if use_heuristics:
            heuristic_regions = self._detect_with_heuristics(img)
            
            # Filter out duplicates (regions that overlap with existing)
            for hr in heuristic_regions:
                if not self._overlaps_existing(hr, regions):
                    regions.append(hr)
        
        # Convert to normalized format
        return [r.to_normalized(width, height) for r in regions]
    
    def _detect_with_model(self, img: np.ndarray) -> list[DetectedRegion]:
        """Detect cards using trained YOLO model."""
        regions = []
        
        results = self.model(img, verbose=False)
        
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
            
            for box in boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                
                # Get class name
                class_name = result.names.get(cls, "")
                
                regions.append(DetectedRegion(
                    x=int(x1),
                    y=int(y1),
                    width=int(x2 - x1),
                    height=int(y2 - y1),
                    confidence=conf,
                    suggested_class=class_name,
                    region_type="card",
                ))
        
        return regions
    
    def _detect_at_positions(self, img: np.ndarray) -> list[DetectedRegion]:
        """Detect cards at configured positions."""
        height, width = img.shape[:2]
        regions = []
        
        # Check hero card positions
        for pos in self.layout.hero_cards:
            region = self._check_position(img, pos, width, height)
            if region:
                regions.append(region)
        
        # Check board card positions
        for pos in self.layout.board_cards:
            region = self._check_position(img, pos, width, height)
            if region:
                regions.append(region)
        
        return regions
    
    def _check_position(
        self,
        img: np.ndarray,
        pos: CardPosition,
        img_width: int,
        img_height: int,
    ) -> Optional[DetectedRegion]:
        """Check if there's a card at the given position."""
        x = int(pos.x * img_width)
        y = int(pos.y * img_height)
        w = int(pos.width * img_width)
        h = int(pos.height * img_height)
        
        # Ensure within bounds
        x = max(0, min(x, img_width - w))
        y = max(0, min(y, img_height - h))
        
        # Extract ROI
        roi = img[y:y+h, x:x+w]
        if roi.size == 0:
            return None
        
        # Check if there's a card (based on brightness and variance)
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray_roi)
        std_brightness = np.std(gray_roi)
        
        # Cards have white background with dark symbols = high mean, high std
        if mean_brightness > self.CARD_BRIGHTNESS_THRESHOLD and std_brightness > 30:
            confidence = min((mean_brightness - 100) / 100, 0.9)  # Higher brightness = higher confidence
            
            return DetectedRegion(
                x=x,
                y=y,
                width=w,
                height=h,
                confidence=confidence,
                region_type=pos.region_type,
                position_index=pos.index,
            )
        
        return None
    
    def _detect_with_heuristics(self, img: np.ndarray) -> list[DetectedRegion]:
        """Detect card regions using color and contour analysis."""
        height, width = img.shape[:2]
        regions = []
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Find white regions (card faces are typically white)
        _, white_mask = cv2.threshold(gray, self.WHITE_THRESHOLD, 255, cv2.THRESH_BINARY)
        
        # Morphological operations to clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_CLOSE, kernel)
        white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_OPEN, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Check size constraints
            rel_w = w / width
            rel_h = h / height
            
            if rel_w < self.MIN_CARD_SIZE or rel_h < self.MIN_CARD_SIZE:
                continue
            if rel_w > self.MAX_CARD_SIZE or rel_h > self.MAX_CARD_SIZE:
                continue
            
            # Check aspect ratio
            aspect = w / h if h > 0 else 0
            if abs(aspect - self.CARD_ASPECT_RATIO) > self.ASPECT_TOLERANCE:
                continue
            
            # Calculate confidence based on shape and color
            area_ratio = cv2.contourArea(contour) / (w * h) if w * h > 0 else 0
            confidence = area_ratio * 0.8  # Rectangular shapes score higher
            
            regions.append(DetectedRegion(
                x=x,
                y=y,
                width=w,
                height=h,
                confidence=confidence,
                region_type="card",
            ))
        
        return regions
    
    def _overlaps_existing(
        self,
        new_region: DetectedRegion,
        existing: list[DetectedRegion],
        threshold: float = 0.5,
    ) -> bool:
        """Check if new region overlaps significantly with existing regions."""
        for existing_region in existing:
            iou = self._calculate_iou(new_region, existing_region)
            if iou > threshold:
                return True
        return False
    
    def _calculate_iou(self, r1: DetectedRegion, r2: DetectedRegion) -> float:
        """Calculate Intersection over Union of two regions."""
        x1 = max(r1.x, r2.x)
        y1 = max(r1.y, r2.y)
        x2 = min(r1.x + r1.width, r2.x + r2.width)
        y2 = min(r1.y + r1.height, r2.y + r2.height)
        
        if x2 < x1 or y2 < y1:
            return 0.0
        
        intersection = (x2 - x1) * (y2 - y1)
        area1 = r1.width * r1.height
        area2 = r2.width * r2.height
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def extract_region(
        self,
        image_data: str,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> str:
        """
        Extract a region from the image.
        
        Returns base64 encoded cropped image.
        """
        img_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return ""
        
        # Crop region
        crop = img[y:y+height, x:x+width]
        
        # Encode back to base64
        _, buffer = cv2.imencode('.jpg', crop, [cv2.IMWRITE_JPEG_QUALITY, 95])
        return base64.b64encode(buffer).decode('utf-8')
    
    def get_current_layout(self) -> dict:
        """Get current layout configuration."""
        return self.layout.to_dict()
    
    def update_position(
        self,
        region_type: str,
        index: int,
        x: float,
        y: float,
        width: float,
        height: float,
    ):
        """Update a single card position."""
        if region_type == "hero" and index < len(self.layout.hero_cards):
            self.layout.hero_cards[index] = CardPosition(
                x=x, y=y, width=width, height=height,
                region_type="hero", index=index
            )
        elif region_type == "board" and index < len(self.layout.board_cards):
            self.layout.board_cards[index] = CardPosition(
                x=x, y=y, width=width, height=height,
                region_type="board", index=index
            )
        
        self.save_layout()
