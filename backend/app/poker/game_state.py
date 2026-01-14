from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class Street(Enum):
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"


class Action(Enum):
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"
    ALLIN = "allin"


@dataclass
class Card:
    """Represents a playing card."""
    rank: str  # 2-9, T, J, Q, K, A
    suit: str  # c, d, h, s
    confidence: float = 1.0
    bbox: Optional[tuple[int, int, int, int]] = None
    
    def __str__(self):
        return f"{self.rank}{self.suit}"
    
    def __eq__(self, other):
        if isinstance(other, Card):
            return self.rank == other.rank and self.suit == other.suit
        return False
    
    def __hash__(self):
        return hash((self.rank, self.suit))


@dataclass
class PlayerState:
    """State of a single player at the table."""
    seat: int
    stack: float
    current_bet: float = 0
    is_active: bool = True  # Still in hand
    is_hero: bool = False
    is_turn: bool = False
    position: str = "UNKNOWN"  # UTG, MP, CO, BTN, SB, BB
    name: str = ""
    
    @property
    def stack_bb(self) -> float:
        """Stack in big blinds (requires game context)."""
        return self.stack  # Will be calculated externally
    
    def to_dict(self) -> dict:
        return {
            "seat": self.seat,
            "stack": self.stack,
            "current_bet": self.current_bet,
            "is_active": self.is_active,
            "is_hero": self.is_hero,
            "is_turn": self.is_turn,
            "position": self.position,
            "name": self.name,
        }


@dataclass
class GameState:
    """Complete state of a poker hand."""
    hero_cards: list[Card] = field(default_factory=list)
    board_cards: list[Card] = field(default_factory=list)
    pot_size: float = 0
    players: list[PlayerState] = field(default_factory=list)
    button_seat: Optional[int] = None
    small_blind: float = 0
    big_blind: float = 0
    ante: float = 0
    street: str = "preflop"
    table_format: str = "6max"
    
    @property
    def hero(self) -> Optional[PlayerState]:
        """Get hero's player state."""
        for player in self.players:
            if player.is_hero:
                return player
        return None
    
    @property
    def hero_position(self) -> str:
        """Get hero's position."""
        hero = self.hero
        return hero.position if hero else "UNKNOWN"
    
    @property
    def hero_stack_bb(self) -> float:
        """Get hero's stack in big blinds."""
        hero = self.hero
        if hero and self.big_blind > 0:
            return hero.stack / self.big_blind
        return 0
    
    @property
    def effective_stack_bb(self) -> float:
        """Get effective stack in BB (minimum of hero and active opponents)."""
        hero = self.hero
        if not hero or self.big_blind <= 0:
            return 0
        
        hero_bb = hero.stack / self.big_blind
        
        # Find minimum stack among active opponents
        opponent_stacks = [
            p.stack / self.big_blind 
            for p in self.players 
            if p.is_active and not p.is_hero
        ]
        
        if not opponent_stacks:
            return hero_bb
        
        return min(hero_bb, min(opponent_stacks))
    
    @property
    def num_active_players(self) -> int:
        """Number of players still in the hand."""
        return sum(1 for p in self.players if p.is_active)
    
    @property
    def pot_bb(self) -> float:
        """Pot size in big blinds."""
        if self.big_blind > 0:
            return self.pot_size / self.big_blind
        return 0
    
    @property
    def is_preflop(self) -> bool:
        return self.street == "preflop"
    
    @property
    def hero_hand(self) -> Optional[str]:
        """Get hero's hand in notation (e.g., 'AKs', 'QQ')."""
        if len(self.hero_cards) != 2:
            return None
        
        card1, card2 = self.hero_cards
        rank1, rank2 = card1.rank, card2.rank
        suit1, suit2 = card1.suit, card2.suit
        
        # Rank ordering
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        rank_order = {r: i for i, r in enumerate(ranks)}
        
        # Sort by rank (higher first)
        if rank_order[rank1] < rank_order[rank2]:
            rank1, rank2 = rank2, rank1
            suit1, suit2 = suit2, suit1
        
        if rank1 == rank2:
            return f"{rank1}{rank2}"  # Pocket pair
        elif suit1 == suit2:
            return f"{rank1}{rank2}s"  # Suited
        else:
            return f"{rank1}{rank2}o"  # Offsuit
    
    def get_player_at_seat(self, seat: int) -> Optional[PlayerState]:
        """Get player at specific seat."""
        for player in self.players:
            if player.seat == seat:
                return player
        return None
    
    def get_player_by_position(self, position: str) -> Optional[PlayerState]:
        """Get player at specific position."""
        for player in self.players:
            if player.position == position:
                return player
        return None
    
    def get_acting_player(self) -> Optional[PlayerState]:
        """Get the player whose turn it is."""
        for player in self.players:
            if player.is_turn:
                return player
        return None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "hero_cards": [str(c) for c in self.hero_cards],
            "board_cards": [str(c) for c in self.board_cards],
            "pot_size": self.pot_size,
            "pot_bb": self.pot_bb,
            "players": [p.to_dict() for p in self.players],
            "button_seat": self.button_seat,
            "small_blind": self.small_blind,
            "big_blind": self.big_blind,
            "ante": self.ante,
            "street": self.street,
            "table_format": self.table_format,
            "hero_position": self.hero_position,
            "hero_stack_bb": self.hero_stack_bb,
            "effective_stack_bb": self.effective_stack_bb,
            "hero_hand": self.hero_hand,
            "num_active_players": self.num_active_players,
        }
