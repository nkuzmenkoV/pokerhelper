import cv2
import numpy as np
from typing import Optional
import io
from PIL import Image

from app.cv.card_detector import CardDetector
from app.cv.ocr_engine import OCREngine
from app.cv.table_detector import TableDetector
from app.cv.regions import PokerOKRegions
from app.poker.game_state import GameState, PlayerState, Card


class CVProcessor:
    """Main computer vision pipeline for processing poker table screenshots."""
    
    def __init__(self):
        self.card_detector = CardDetector()
        self.ocr_engine = OCREngine()
        self.table_detector = TableDetector()
        self.regions = PokerOKRegions()
        self._initialized = False
    
    async def initialize(self):
        """Initialize all CV components."""
        if self._initialized:
            return
        
        await self.card_detector.load_model()
        self._initialized = True
    
    def _decode_image(self, frame_data: bytes) -> np.ndarray:
        """Decode JPEG bytes to OpenCV image."""
        image = Image.open(io.BytesIO(frame_data))
        return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    async def process_frame(self, frame_data: bytes) -> Optional[GameState]:
        """
        Process a single frame and extract game state.
        
        Args:
            frame_data: JPEG encoded image bytes
            
        Returns:
            GameState object or None if table not detected
        """
        if not self._initialized:
            await self.initialize()
        
        # Decode image
        image = self._decode_image(frame_data)
        height, width = image.shape[:2]
        
        # Update regions for current resolution
        self.regions.update_for_resolution(width, height)
        
        # Detect if this is a valid poker table
        if not self.table_detector.is_poker_table(image):
            return None
        
        # Detect table format (6max, 9max, etc.)
        table_format = self.table_detector.detect_table_format(image)
        
        # Extract hero cards
        hero_cards_roi = self.regions.get_hero_cards_region(image)
        hero_cards = self.card_detector.detect_cards(hero_cards_roi)
        
        # Extract board cards
        board_roi = self.regions.get_board_region(image)
        board_cards = self.card_detector.detect_cards(board_roi)
        
        # Extract pot size
        pot_roi = self.regions.get_pot_region(image)
        pot_size = self.ocr_engine.read_number(pot_roi)
        
        # Extract blinds/ante from title bar
        title_roi = self.regions.get_title_region(image)
        blinds = self.ocr_engine.read_blinds(title_roi)
        
        # Detect button position
        button_position = self.table_detector.find_button_position(image, self.regions)
        
        # Extract player states (stacks, bets, active status)
        players = []
        num_seats = 6 if table_format == "6max" else 9 if table_format == "9max" else 2
        
        for seat in range(num_seats):
            player_region = self.regions.get_player_region(image, seat, num_seats)
            
            # Check if seat is occupied
            if not self.table_detector.is_seat_occupied(player_region):
                continue
            
            # Extract stack
            stack_roi = self.regions.get_stack_region(player_region)
            stack = self.ocr_engine.read_number(stack_roi)
            
            # Extract current bet
            bet_roi = self.regions.get_bet_region(image, seat, num_seats)
            current_bet = self.ocr_engine.read_number(bet_roi)
            
            # Check if player is active (has cards)
            is_active = self.table_detector.is_player_active(player_region)
            
            # Check if it's hero's turn
            is_hero = seat == self.regions.hero_seat
            is_turn = self.table_detector.is_players_turn(player_region)
            
            players.append(PlayerState(
                seat=seat,
                stack=stack or 0,
                current_bet=current_bet or 0,
                is_active=is_active,
                is_hero=is_hero,
                is_turn=is_turn,
                position=self._calculate_position(seat, button_position, num_seats),
            ))
        
        # Determine current street
        street = self._determine_street(board_cards)
        
        return GameState(
            hero_cards=hero_cards,
            board_cards=board_cards,
            pot_size=pot_size or 0,
            players=players,
            button_seat=button_position,
            small_blind=blinds[0] if blinds else 0,
            big_blind=blinds[1] if blinds else 0,
            ante=blinds[2] if blinds and len(blinds) > 2 else 0,
            street=street,
            table_format=table_format,
        )
    
    def _calculate_position(self, seat: int, button_seat: int, num_seats: int) -> str:
        """Calculate position name based on seat and button location."""
        if button_seat is None:
            return "UNKNOWN"
        
        # Calculate relative position from button
        relative = (seat - button_seat) % num_seats
        
        if num_seats == 6:
            positions = ["BTN", "SB", "BB", "UTG", "MP", "CO"]
        elif num_seats == 9:
            positions = ["BTN", "SB", "BB", "UTG", "UTG1", "UTG2", "MP", "MP1", "CO"]
        else:  # heads-up
            positions = ["BTN", "BB"]
        
        return positions[relative] if relative < len(positions) else "UNKNOWN"
    
    def _determine_street(self, board_cards: list[Card]) -> str:
        """Determine current street based on board cards."""
        num_cards = len(board_cards)
        if num_cards == 0:
            return "preflop"
        elif num_cards == 3:
            return "flop"
        elif num_cards == 4:
            return "turn"
        elif num_cards == 5:
            return "river"
        return "unknown"
