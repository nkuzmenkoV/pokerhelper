import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional


@dataclass
class Region:
    """Represents a rectangular region of interest."""
    x: int
    y: int
    width: int
    height: int
    
    def extract(self, image: np.ndarray) -> np.ndarray:
        """Extract this region from an image."""
        return image[self.y:self.y + self.height, self.x:self.x + self.width]
    
    def scale(self, scale_x: float, scale_y: float) -> 'Region':
        """Return a scaled copy of this region."""
        return Region(
            x=int(self.x * scale_x),
            y=int(self.y * scale_y),
            width=int(self.width * scale_x),
            height=int(self.height * scale_y),
        )


class PokerOKRegions:
    """
    Defines ROI (Region of Interest) coordinates for PokerOK client.
    
    These coordinates are calibrated for a specific resolution and will
    be scaled proportionally for other resolutions.
    
    Base resolution: 1920x1080
    """
    
    # Base resolution for calibration
    BASE_WIDTH = 1920
    BASE_HEIGHT = 1080
    
    def __init__(self):
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.hero_seat = 0  # Default hero position (bottom center)
        
        # ===== Define regions for base resolution =====
        
        # Hero cards (bottom center)
        self._hero_cards = Region(x=850, y=720, width=220, height=140)
        
        # Board cards (center of table)
        self._board = Region(x=660, y=400, width=600, height=120)
        
        # Pot display (above board)
        self._pot = Region(x=860, y=340, width=200, height=40)
        
        # Title bar (table name, blinds)
        self._title = Region(x=600, y=0, width=720, height=40)
        
        # 6-max seat positions (clockwise from hero at bottom)
        # Each tuple is (center_x, center_y) for the seat
        self._seats_6max = [
            (960, 800),   # Seat 0: Bottom center (Hero)
            (1600, 650),  # Seat 1: Bottom right
            (1650, 350),  # Seat 2: Top right
            (960, 200),   # Seat 3: Top center
            (270, 350),   # Seat 4: Top left
            (320, 650),   # Seat 5: Bottom left
        ]
        
        # 9-max seat positions
        self._seats_9max = [
            (960, 800),   # Seat 0: Bottom center (Hero)
            (1450, 720),  # Seat 1: Bottom right 1
            (1700, 550),  # Seat 2: Right
            (1650, 300),  # Seat 3: Top right
            (1200, 180),  # Seat 4: Top right center
            (720, 180),   # Seat 5: Top left center
            (270, 300),   # Seat 6: Top left
            (220, 550),   # Seat 7: Left
            (470, 720),   # Seat 8: Bottom left 1
        ]
        
        # Heads-up positions
        self._seats_headsup = [
            (960, 800),   # Seat 0: Bottom (Hero)
            (960, 200),   # Seat 1: Top (Villain)
        ]
        
        # Player region dimensions (centered on seat position)
        self._player_width = 180
        self._player_height = 120
        
        # Stack position relative to player center
        self._stack_offset_y = 50
        self._stack_width = 120
        self._stack_height = 25
        
        # Bet position relative to seat (towards center)
        self._bet_offsets_6max = [
            (0, -100),    # Seat 0
            (-150, -80),  # Seat 1
            (-150, 50),   # Seat 2
            (0, 80),      # Seat 3
            (150, 50),    # Seat 4
            (150, -80),   # Seat 5
        ]
    
    def update_for_resolution(self, width: int, height: int):
        """Update scale factors for current screen resolution."""
        self.scale_x = width / self.BASE_WIDTH
        self.scale_y = height / self.BASE_HEIGHT
    
    def get_hero_cards_region(self, image: np.ndarray) -> np.ndarray:
        """Get the region containing hero's hole cards."""
        region = self._hero_cards.scale(self.scale_x, self.scale_y)
        return region.extract(image)
    
    def get_board_region(self, image: np.ndarray) -> np.ndarray:
        """Get the region containing board cards."""
        region = self._board.scale(self.scale_x, self.scale_y)
        return region.extract(image)
    
    def get_pot_region(self, image: np.ndarray) -> np.ndarray:
        """Get the region containing pot size."""
        region = self._pot.scale(self.scale_x, self.scale_y)
        return region.extract(image)
    
    def get_title_region(self, image: np.ndarray) -> np.ndarray:
        """Get the title bar region."""
        region = self._title.scale(self.scale_x, self.scale_y)
        return region.extract(image)
    
    def get_seat_position(self, seat: int, num_seats: int) -> Tuple[int, int]:
        """Get the center position of a seat."""
        if num_seats == 6:
            seats = self._seats_6max
        elif num_seats == 9:
            seats = self._seats_9max
        else:
            seats = self._seats_headsup
        
        if seat >= len(seats):
            return (0, 0)
        
        x, y = seats[seat]
        return (int(x * self.scale_x), int(y * self.scale_y))
    
    def get_player_region(self, image: np.ndarray, seat: int, num_seats: int) -> np.ndarray:
        """Get the region containing a player's avatar/info."""
        cx, cy = self.get_seat_position(seat, num_seats)
        
        w = int(self._player_width * self.scale_x)
        h = int(self._player_height * self.scale_y)
        
        x = max(0, cx - w // 2)
        y = max(0, cy - h // 2)
        
        # Clamp to image bounds
        height, width = image.shape[:2]
        x = min(x, width - w)
        y = min(y, height - h)
        
        return image[y:y + h, x:x + w]
    
    def get_stack_region(self, player_region: np.ndarray) -> np.ndarray:
        """Get the stack text region from a player region."""
        h, w = player_region.shape[:2]
        
        # Stack is typically below the avatar
        stack_y = int(h * 0.7)
        stack_x = int(w * 0.1)
        stack_w = int(w * 0.8)
        stack_h = int(h * 0.2)
        
        return player_region[stack_y:stack_y + stack_h, stack_x:stack_x + stack_w]
    
    def get_bet_region(self, image: np.ndarray, seat: int, num_seats: int) -> np.ndarray:
        """Get the region containing a player's current bet."""
        cx, cy = self.get_seat_position(seat, num_seats)
        
        # Get bet offset for this seat
        if num_seats == 6 and seat < len(self._bet_offsets_6max):
            offset_x, offset_y = self._bet_offsets_6max[seat]
        else:
            # Default offset towards table center
            offset_x, offset_y = 0, -80
        
        bet_x = int((cx + offset_x) * self.scale_x)
        bet_y = int((cy + offset_y) * self.scale_y)
        bet_w = int(100 * self.scale_x)
        bet_h = int(30 * self.scale_y)
        
        # Center the region
        x = max(0, bet_x - bet_w // 2)
        y = max(0, bet_y - bet_h // 2)
        
        # Clamp to image bounds
        height, width = image.shape[:2]
        x = min(x, width - bet_w)
        y = min(y, height - bet_h)
        
        return image[y:y + bet_h, x:x + bet_w]
    
    def get_nearest_seat(self, x: int, y: int, num_seats: int = 6) -> Optional[int]:
        """Find the nearest seat to a given point."""
        min_dist = float('inf')
        nearest = None
        
        for seat in range(num_seats):
            sx, sy = self.get_seat_position(seat, num_seats)
            dist = ((x - sx) ** 2 + (y - sy) ** 2) ** 0.5
            if dist < min_dist:
                min_dist = dist
                nearest = seat
        
        return nearest
    
    def set_hero_seat(self, seat: int):
        """Set which seat the hero is sitting at."""
        self.hero_seat = seat
