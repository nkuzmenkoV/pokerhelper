"""
HUD (Heads-Up Display) Tracker

Tracks and calculates poker statistics for opponents based on observed actions.

Statistics tracked:
- VPIP (Voluntarily Put $ In Pot)
- PFR (Preflop Raise %)
- 3-Bet %
- Fold to 3-Bet %
- C-Bet %
- Aggression Factor (AF)
- WTSD (Went to Showdown %)
- W$SD (Won $ at Showdown %)
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from enum import Enum


class Action(Enum):
    """Poker actions."""
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"
    ALLIN = "allin"


class Street(Enum):
    """Streets in a poker hand."""
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"


@dataclass
class ActionRecord:
    """Record of a single action."""
    street: Street
    action: Action
    amount: float = 0
    is_voluntary: bool = False  # Was this a voluntary put money in pot?
    facing_bet: float = 0  # Size of bet player was facing
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class HandRecord:
    """Record of a single hand for a player."""
    hand_id: str
    position: str
    actions: list[ActionRecord] = field(default_factory=list)
    went_to_showdown: bool = False
    won_at_showdown: bool = False
    final_pot: float = 0
    
    @property
    def vpip(self) -> bool:
        """Did player voluntarily put money in pot preflop?"""
        for action in self.actions:
            if action.street == Street.PREFLOP and action.is_voluntary:
                return True
        return False
    
    @property
    def pfr(self) -> bool:
        """Did player raise preflop?"""
        for action in self.actions:
            if action.street == Street.PREFLOP and action.action in [Action.RAISE, Action.ALLIN]:
                return True
        return False
    
    @property
    def three_bet(self) -> bool:
        """Did player 3-bet preflop?"""
        raise_count = 0
        for action in self.actions:
            if action.street == Street.PREFLOP:
                if action.action in [Action.RAISE, Action.ALLIN]:
                    raise_count += 1
                    if raise_count >= 2:  # Player made the 2nd raise = 3-bet
                        return True
        return False


@dataclass
class PlayerStats:
    """Aggregated statistics for a player."""
    player_id: str
    player_name: str
    
    # Hand counts
    total_hands: int = 0
    
    # VPIP stats
    vpip_hands: int = 0  # Hands where player voluntarily put money in
    
    # PFR stats  
    pfr_hands: int = 0  # Hands where player raised preflop
    
    # 3-Bet stats
    three_bet_opportunities: int = 0  # Times player could 3-bet
    three_bet_count: int = 0  # Times player actually 3-bet
    
    # Fold to 3-Bet stats
    faced_three_bet: int = 0
    folded_to_three_bet: int = 0
    
    # C-Bet stats (Continuation Bet)
    cbet_opportunities: int = 0  # Times player was PFR and could cbet
    cbet_count: int = 0  # Times player actually cbet
    
    # Aggression stats
    bets_and_raises: int = 0  # Total bets + raises postflop
    calls: int = 0  # Total calls postflop
    
    # Showdown stats
    went_to_showdown: int = 0
    won_at_showdown: int = 0
    
    # Position stats (optional detailed breakdown)
    stats_by_position: dict = field(default_factory=dict)
    
    @property
    def vpip_pct(self) -> float:
        """VPIP percentage."""
        if self.total_hands == 0:
            return 0.0
        return (self.vpip_hands / self.total_hands) * 100
    
    @property
    def pfr_pct(self) -> float:
        """PFR percentage."""
        if self.total_hands == 0:
            return 0.0
        return (self.pfr_hands / self.total_hands) * 100
    
    @property
    def three_bet_pct(self) -> float:
        """3-Bet percentage."""
        if self.three_bet_opportunities == 0:
            return 0.0
        return (self.three_bet_count / self.three_bet_opportunities) * 100
    
    @property
    def fold_to_three_bet_pct(self) -> float:
        """Fold to 3-Bet percentage."""
        if self.faced_three_bet == 0:
            return 0.0
        return (self.folded_to_three_bet / self.faced_three_bet) * 100
    
    @property
    def cbet_pct(self) -> float:
        """C-Bet percentage."""
        if self.cbet_opportunities == 0:
            return 0.0
        return (self.cbet_count / self.cbet_opportunities) * 100
    
    @property
    def aggression_factor(self) -> float:
        """Aggression Factor (AF) = (Bets + Raises) / Calls."""
        if self.calls == 0:
            return float('inf') if self.bets_and_raises > 0 else 0.0
        return self.bets_and_raises / self.calls
    
    @property
    def wtsd_pct(self) -> float:
        """Went to Showdown percentage."""
        if self.vpip_hands == 0:
            return 0.0
        return (self.went_to_showdown / self.vpip_hands) * 100
    
    @property
    def wsd_pct(self) -> float:
        """Won $ at Showdown percentage."""
        if self.went_to_showdown == 0:
            return 0.0
        return (self.won_at_showdown / self.went_to_showdown) * 100
    
    def to_dict(self) -> dict:
        """Convert stats to dictionary for display."""
        return {
            "player_name": self.player_name,
            "hands": self.total_hands,
            "vpip": round(self.vpip_pct, 1),
            "pfr": round(self.pfr_pct, 1),
            "3bet": round(self.three_bet_pct, 1),
            "fold_to_3bet": round(self.fold_to_three_bet_pct, 1),
            "cbet": round(self.cbet_pct, 1),
            "af": round(self.aggression_factor, 1) if self.aggression_factor != float('inf') else "∞",
            "wtsd": round(self.wtsd_pct, 1),
            "wsd": round(self.wsd_pct, 1),
        }
    
    def get_summary(self) -> str:
        """Get one-line summary for HUD display."""
        return f"VPIP:{self.vpip_pct:.0f} PFR:{self.pfr_pct:.0f} 3B:{self.three_bet_pct:.0f} ({self.total_hands})"
    
    def get_player_type(self) -> str:
        """Categorize player based on stats."""
        if self.total_hands < 20:
            return "Unknown"
        
        vpip = self.vpip_pct
        pfr = self.pfr_pct
        
        # Tight = VPIP < 20%, Loose = VPIP > 30%
        # Passive = PFR < 15%, Aggressive = PFR > 20%
        
        if vpip < 20:
            if pfr > 15:
                return "TAG"  # Tight-Aggressive (good player)
            else:
                return "Rock"  # Tight-Passive (very tight)
        elif vpip < 30:
            if pfr > 18:
                return "LAG"  # Loose-Aggressive
            else:
                return "Weak-Tight"
        else:
            if pfr > 20:
                return "Maniac"  # Very loose and aggressive
            else:
                return "Fish"  # Loose-Passive (calling station)


class HUDTracker:
    """
    Tracks HUD statistics for all observed players.
    """
    
    def __init__(self):
        # Player stats by player ID
        self.players: dict[str, PlayerStats] = {}
        
        # Current hand being tracked
        self.current_hand: dict[str, HandRecord] = {}
        self.current_hand_id: Optional[str] = None
        self.current_pfr_player: Optional[str] = None  # Who was the preflop raiser
    
    def get_or_create_player(self, player_id: str, player_name: str = "") -> PlayerStats:
        """Get existing player stats or create new."""
        if player_id not in self.players:
            self.players[player_id] = PlayerStats(
                player_id=player_id,
                player_name=player_name or player_id,
            )
        return self.players[player_id]
    
    def start_new_hand(self, hand_id: str, players: list[dict]):
        """
        Start tracking a new hand.
        
        Args:
            hand_id: Unique identifier for the hand
            players: List of player dicts with {id, name, position, stack}
        """
        self.current_hand_id = hand_id
        self.current_hand = {}
        self.current_pfr_player = None
        
        for player in players:
            player_id = player.get("id", player.get("name", ""))
            self.current_hand[player_id] = HandRecord(
                hand_id=hand_id,
                position=player.get("position", ""),
            )
            
            # Increment hand count
            stats = self.get_or_create_player(player_id, player.get("name", ""))
            stats.total_hands += 1
    
    def record_action(
        self,
        player_id: str,
        action: str,
        street: str,
        amount: float = 0,
        facing_bet: float = 0,
    ):
        """
        Record a player action.
        
        Args:
            player_id: Player identifier
            action: Action type (fold, check, call, bet, raise, allin)
            street: Current street (preflop, flop, turn, river)
            amount: Action amount
            facing_bet: Size of bet player is facing
        """
        if player_id not in self.current_hand:
            return
        
        action_enum = Action(action.lower())
        street_enum = Street(street.lower())
        
        # Determine if voluntary
        is_voluntary = action_enum in [Action.CALL, Action.BET, Action.RAISE, Action.ALLIN]
        
        record = ActionRecord(
            street=street_enum,
            action=action_enum,
            amount=amount,
            is_voluntary=is_voluntary,
            facing_bet=facing_bet,
        )
        
        self.current_hand[player_id].actions.append(record)
        
        # Update stats
        stats = self.get_or_create_player(player_id)
        
        # Preflop stats
        if street_enum == Street.PREFLOP:
            if is_voluntary:
                stats.vpip_hands += 1
            
            if action_enum in [Action.RAISE, Action.ALLIN]:
                stats.pfr_hands += 1
                
                # Check if this is a 3-bet (re-raise)
                if self.current_pfr_player and self.current_pfr_player != player_id:
                    stats.three_bet_count += 1
                else:
                    self.current_pfr_player = player_id
        
        # Postflop aggression
        if street_enum != Street.PREFLOP:
            if action_enum in [Action.BET, Action.RAISE, Action.ALLIN]:
                stats.bets_and_raises += 1
            elif action_enum == Action.CALL:
                stats.calls += 1
            
            # C-Bet tracking
            if street_enum == Street.FLOP and player_id == self.current_pfr_player:
                stats.cbet_opportunities += 1
                if action_enum in [Action.BET, Action.RAISE, Action.ALLIN]:
                    stats.cbet_count += 1
    
    def record_showdown(self, player_id: str, won: bool):
        """Record showdown result for a player."""
        if player_id not in self.current_hand:
            return
        
        self.current_hand[player_id].went_to_showdown = True
        self.current_hand[player_id].won_at_showdown = won
        
        stats = self.get_or_create_player(player_id)
        stats.went_to_showdown += 1
        if won:
            stats.won_at_showdown += 1
    
    def end_hand(self):
        """Finalize the current hand."""
        self.current_hand_id = None
        self.current_hand = {}
        self.current_pfr_player = None
    
    def get_player_stats(self, player_id: str) -> Optional[dict]:
        """Get stats for a specific player."""
        if player_id in self.players:
            return self.players[player_id].to_dict()
        return None
    
    def get_all_stats(self) -> list[dict]:
        """Get stats for all tracked players."""
        return [stats.to_dict() for stats in self.players.values()]
    
    def get_hud_display(self, player_id: str) -> Optional[str]:
        """Get HUD display string for a player."""
        if player_id in self.players:
            return self.players[player_id].get_summary()
        return None
    
    def get_player_type(self, player_id: str) -> str:
        """Get player type classification."""
        if player_id in self.players:
            return self.players[player_id].get_player_type()
        return "Unknown"
    
    def export_stats(self) -> dict:
        """Export all stats as JSON-serializable dict."""
        return {
            player_id: stats.to_dict()
            for player_id, stats in self.players.items()
        }
    
    def import_stats(self, data: dict):
        """Import stats from saved data."""
        for player_id, stats_dict in data.items():
            if player_id not in self.players:
                self.players[player_id] = PlayerStats(
                    player_id=player_id,
                    player_name=stats_dict.get("player_name", player_id),
                )
            
            stats = self.players[player_id]
            stats.total_hands = stats_dict.get("hands", 0)
            # Note: Detailed stats would need to be stored separately
            # This is a simplified import for basic stats
