import numpy as np
import cv2
from typing import Optional

from app.cv.regions import PokerOKRegions


class TableDetector:
    """Detects poker table elements and states."""
    
    # PokerOK table color signatures (BGR format)
    TABLE_GREEN_LOW = np.array([35, 80, 35])
    TABLE_GREEN_HIGH = np.array([85, 180, 85])
    
    # Button/dealer chip colors
    BUTTON_WHITE_LOW = np.array([200, 200, 200])
    BUTTON_WHITE_HIGH = np.array([255, 255, 255])
    
    # Active player highlight (yellow/gold glow)
    ACTIVE_GLOW_LOW = np.array([20, 100, 100])
    ACTIVE_GLOW_HIGH = np.array([40, 255, 255])
    
    def __init__(self):
        self.button_template = None
        self._load_templates()
    
    def _load_templates(self):
        """Load template images for matching."""
        # TODO: Load actual button template from assets
        # self.button_template = cv2.imread("assets/button.png")
        pass
    
    def is_poker_table(self, image: np.ndarray) -> bool:
        """
        Detect if the image contains a poker table.
        
        Uses color analysis to find the green felt area.
        """
        if image is None or image.size == 0:
            return False
        
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Green felt mask (typical poker table color)
        green_mask = cv2.inRange(hsv, (35, 50, 50), (85, 255, 200))
        
        # Calculate percentage of green pixels
        green_ratio = np.sum(green_mask > 0) / green_mask.size
        
        # If more than 15% of image is green felt, likely a poker table
        return green_ratio > 0.15
    
    def detect_table_format(self, image: np.ndarray) -> str:
        """
        Detect the table format (6max, 9max, heads-up).
        
        Based on the layout and number of player positions visible.
        """
        height, width = image.shape[:2]
        
        # Analyze player position regions
        # 6-max has wider spacing between players
        # 9-max has more compressed player areas
        
        # Simple heuristic based on aspect ratio and layout
        aspect_ratio = width / height
        
        if aspect_ratio > 1.8:
            # Wide table - likely 9-max or 6-max
            # Check for additional player positions
            # For now, default to 6-max
            return "6max"
        elif aspect_ratio > 1.4:
            return "6max"
        else:
            # Square-ish - could be heads-up
            return "headsup"
    
    def find_button_position(self, image: np.ndarray, regions: PokerOKRegions) -> Optional[int]:
        """
        Find the dealer button position on the table.
        
        Returns the seat number (0-indexed) or None if not found.
        """
        if self.button_template is not None:
            return self._find_button_with_template(image, regions)
        else:
            return self._find_button_with_color(image, regions)
    
    def _find_button_with_template(self, image: np.ndarray, regions: PokerOKRegions) -> Optional[int]:
        """Find button using template matching."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(self.button_template, cv2.COLOR_BGR2GRAY)
        
        result = cv2.matchTemplate(gray, template_gray, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val > 0.7:  # Threshold for match confidence
            button_x, button_y = max_loc
            # Determine which seat the button is near
            return regions.get_nearest_seat(button_x, button_y)
        
        return None
    
    def _find_button_with_color(self, image: np.ndarray, regions: PokerOKRegions) -> Optional[int]:
        """Find button using color detection (white/yellow dealer button)."""
        # Look for bright white/yellow circular object
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # White button mask
        white_mask = cv2.inRange(image, self.BUTTON_WHITE_LOW, self.BUTTON_WHITE_HIGH)
        
        # Find contours
        contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            # Button should be a small circular shape
            if 100 < area < 5000:
                # Check circularity
                perimeter = cv2.arcLength(contour, True)
                if perimeter > 0:
                    circularity = 4 * np.pi * area / (perimeter * perimeter)
                    if circularity > 0.6:  # Reasonably circular
                        M = cv2.moments(contour)
                        if M["m00"] > 0:
                            cx = int(M["m10"] / M["m00"])
                            cy = int(M["m01"] / M["m00"])
                            return regions.get_nearest_seat(cx, cy)
        
        return None
    
    def is_seat_occupied(self, player_region: np.ndarray) -> bool:
        """Check if a seat has a player (not empty)."""
        if player_region is None or player_region.size == 0:
            return False
        
        # Empty seats typically have uniform color or "Sit Here" button
        # Occupied seats have player avatar, name, stack
        
        # Calculate color variance - occupied seats have more variety
        gray = cv2.cvtColor(player_region, cv2.COLOR_BGR2GRAY)
        variance = np.var(gray)
        
        return variance > 500  # Threshold for visual complexity
    
    def is_player_active(self, player_region: np.ndarray) -> bool:
        """Check if player is still in the hand (has cards)."""
        if player_region is None or player_region.size == 0:
            return False
        
        # Active players typically have card backs visible or colored border
        # Folded players are grayed out
        
        # Check for saturation - active players have more color
        hsv = cv2.cvtColor(player_region, cv2.COLOR_BGR2HSV)
        avg_saturation = np.mean(hsv[:, :, 1])
        
        return avg_saturation > 30
    
    def is_players_turn(self, player_region: np.ndarray) -> bool:
        """Check if it's this player's turn to act (highlighted)."""
        if player_region is None or player_region.size == 0:
            return False
        
        # Active player usually has a glow or bright border
        hsv = cv2.cvtColor(player_region, cv2.COLOR_BGR2HSV)
        
        # Look for yellow/gold highlight
        glow_mask = cv2.inRange(hsv, self.ACTIVE_GLOW_LOW, self.ACTIVE_GLOW_HIGH)
        glow_ratio = np.sum(glow_mask > 0) / glow_mask.size
        
        return glow_ratio > 0.05
    
    def detect_action_buttons(self, image: np.ndarray) -> dict:
        """
        Detect available action buttons (Fold, Call, Raise, All-in).
        
        Returns dict with button names and their bounding boxes.
        """
        buttons = {}
        
        # Action buttons are typically at the bottom of the screen
        height, width = image.shape[:2]
        button_region = image[int(height * 0.8):, :]
        
        # TODO: Use OCR or template matching to find buttons
        # For now, return empty dict
        
        return buttons
