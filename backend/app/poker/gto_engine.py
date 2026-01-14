"""
GTO Engine - Main recommendation engine combining all poker logic.

Provides preflop and postflop recommendations based on:
- Preloaded GTO ranges
- Push/Fold charts
- ICM considerations
"""

from typing import Optional
from dataclasses import dataclass

from app.poker.game_state import GameState
from app.poker.push_fold import PushFoldCalculator
from app.poker.icm_calculator import ICMCalculator


@dataclass
class ActionRecommendation:
    """Single action recommendation."""
    action: str  # fold, check, call, bet, raise, allin
    size: Optional[float] = None  # Bet/raise size (in chips or BB)
    frequency: float = 1.0  # How often to take this action (0-1)
    ev: float = 0.0  # Expected value
    reason: str = ""  # Explanation


@dataclass 
class HandRecommendation:
    """Complete recommendation for current hand."""
    primary_action: ActionRecommendation
    alternative_actions: list[ActionRecommendation]
    hand: str  # Hero's hand
    position: str
    stack_bb: float
    street: str
    is_push_fold: bool  # Whether push/fold mode applies
    icm_adjusted: bool  # Whether ICM adjustments were applied
    range_strength: float  # How strong this hand is in the range (0-1)
    notes: list[str]  # Additional notes/tips


# Preflop open raise ranges by position (percentage of hands)
OPEN_RAISE_RANGES = {
    "6max": {
        "UTG": 0.15,  # ~15% of hands
        "MP": 0.20,
        "CO": 0.28,
        "BTN": 0.45,
        "SB": 0.40,
    },
    "9max": {
        "UTG": 0.10,
        "UTG1": 0.12,
        "UTG2": 0.14,
        "MP": 0.16,
        "MP1": 0.18,
        "CO": 0.25,
        "BTN": 0.40,
        "SB": 0.35,
    },
    "headsup": {
        "BTN": 0.80,  # Very wide
        "BB": 0.50,
    }
}


# 3-bet ranges vs open (percentage of calling range)
THREE_BET_RANGES = {
    "6max": {
        "vs_UTG": 0.05,
        "vs_MP": 0.07,
        "vs_CO": 0.10,
        "vs_BTN": 0.12,
        "vs_SB": 0.15,
    }
}


class GTOEngine:
    """Main GTO recommendation engine."""
    
    def __init__(self):
        self.push_fold = PushFoldCalculator()
        self.icm = ICMCalculator()
        self.gto_ranges = {}  # Will be loaded from database
        
    def get_recommendations(self, game_state: GameState) -> dict:
        """
        Get action recommendations for current game state.
        
        Returns dict with:
        - primary: Main recommended action
        - alternatives: Other viable actions
        - analysis: Detailed analysis
        """
        if game_state.hero is None or not game_state.hero_cards:
            return {"error": "No hero cards detected"}
        
        hero_hand = game_state.hero_hand
        if not hero_hand:
            return {"error": "Could not determine hero's hand"}
        
        # Determine if push/fold applies (short stack)
        is_short_stack = game_state.hero_stack_bb <= 15
        
        if game_state.is_preflop:
            recommendation = self._get_preflop_recommendation(game_state, is_short_stack)
        else:
            recommendation = self._get_postflop_recommendation(game_state)
        
        return recommendation.to_dict() if hasattr(recommendation, 'to_dict') else recommendation
    
    def _get_preflop_recommendation(
        self,
        game_state: GameState,
        is_short_stack: bool,
    ) -> dict:
        """Get preflop recommendation."""
        hero_hand = game_state.hero_hand
        position = game_state.hero_position
        stack_bb = game_state.hero_stack_bb
        
        notes = []
        icm_adjusted = False
        
        # Check if we're in push/fold territory
        if is_short_stack:
            pf_result = self.push_fold.should_push(
                hand=hero_hand,
                position=position,
                stack_bb=stack_bb,
                facing_raise=self._is_facing_raise(game_state),
                num_players_behind=self._count_players_behind(game_state),
            )
            
            if pf_result.action == "push":
                primary = ActionRecommendation(
                    action="allin",
                    size=stack_bb,
                    frequency=1.0,
                    ev=pf_result.equity,
                    reason=f"Push with {hero_hand} from {position} at {stack_bb:.1f}BB",
                )
                alternatives = [
                    ActionRecommendation(
                        action="fold",
                        frequency=0.0,
                        reason="Folding loses equity",
                    )
                ]
            else:
                primary = ActionRecommendation(
                    action="fold",
                    frequency=1.0,
                    ev=0,
                    reason=f"{hero_hand} not strong enough to push from {position}",
                )
                alternatives = []
            
            notes.append(f"Push/Fold mode: Stack = {stack_bb:.1f}BB")
            
            return {
                "primary": {
                    "action": primary.action,
                    "size": primary.size,
                    "frequency": primary.frequency,
                    "reason": primary.reason,
                },
                "alternatives": [
                    {"action": a.action, "reason": a.reason}
                    for a in alternatives
                ],
                "hand": hero_hand,
                "position": position,
                "stack_bb": stack_bb,
                "is_push_fold": True,
                "icm_adjusted": icm_adjusted,
                "range_strength": pf_result.hand_strength,
                "notes": notes,
            }
        
        # Regular preflop play
        hand_strength = self.push_fold.get_hand_strength(hero_hand)
        
        # Determine if facing action
        facing_raise = self._is_facing_raise(game_state)
        facing_3bet = self._is_facing_3bet(game_state)
        
        if not facing_raise and not facing_3bet:
            # First to act or limped pot
            return self._get_open_raise_recommendation(game_state, hand_strength)
        elif facing_raise and not facing_3bet:
            # Facing open raise
            return self._get_vs_raise_recommendation(game_state, hand_strength)
        else:
            # Facing 3bet
            return self._get_vs_3bet_recommendation(game_state, hand_strength)
    
    def _get_open_raise_recommendation(
        self,
        game_state: GameState,
        hand_strength: float,
    ) -> dict:
        """Get recommendation for opening the pot."""
        position = game_state.hero_position
        hero_hand = game_state.hero_hand
        stack_bb = game_state.hero_stack_bb
        
        # Get opening threshold for position
        table_format = game_state.table_format
        thresholds = OPEN_RAISE_RANGES.get(table_format, OPEN_RAISE_RANGES["6max"])
        
        # Convert threshold to hand strength (approximate)
        open_threshold = 1 - thresholds.get(position, 0.15)
        
        if hand_strength >= open_threshold:
            # Standard raise size
            raise_size = 2.5 if position in ["BTN", "SB"] else 3.0
            
            primary = {
                "action": "raise",
                "size": raise_size,
                "frequency": 1.0,
                "reason": f"Open raise {hero_hand} from {position}",
            }
            alternatives = [
                {"action": "fold", "frequency": 0.0, "reason": "Folding is -EV"},
            ]
        else:
            primary = {
                "action": "fold",
                "frequency": 1.0,
                "reason": f"{hero_hand} outside opening range from {position}",
            }
            alternatives = []
        
        return {
            "primary": primary,
            "alternatives": alternatives,
            "hand": hero_hand,
            "position": position,
            "stack_bb": stack_bb,
            "is_push_fold": False,
            "icm_adjusted": False,
            "range_strength": hand_strength,
            "notes": [f"Open raising range from {position}: ~{thresholds.get(position, 0.15)*100:.0f}%"],
        }
    
    def _get_vs_raise_recommendation(
        self,
        game_state: GameState,
        hand_strength: float,
    ) -> dict:
        """Get recommendation when facing a raise."""
        position = game_state.hero_position
        hero_hand = game_state.hero_hand
        stack_bb = game_state.hero_stack_bb
        
        # Premium hands: 3-bet
        if hand_strength >= 0.90:
            primary = {
                "action": "raise",
                "size": 3.0,  # 3x the open
                "frequency": 0.85,
                "reason": f"3-bet {hero_hand} for value",
            }
            alternatives = [
                {"action": "call", "frequency": 0.15, "reason": "Occasionally flat to disguise"},
            ]
        # Strong hands: Mix of 3-bet and call
        elif hand_strength >= 0.75:
            primary = {
                "action": "call",
                "frequency": 0.6,
                "reason": f"Call with {hero_hand}, strong but not premium",
            }
            alternatives = [
                {"action": "raise", "size": 3.0, "frequency": 0.4, "reason": "3-bet as bluff/value"},
            ]
        # Playable hands: Call or fold based on position
        elif hand_strength >= 0.55:
            if position in ["BTN", "BB"]:
                primary = {
                    "action": "call",
                    "frequency": 0.7,
                    "reason": f"Defend {hero_hand} in position",
                }
            else:
                primary = {
                    "action": "fold",
                    "frequency": 1.0,
                    "reason": f"{hero_hand} too weak to continue OOP",
                }
            alternatives = []
        else:
            primary = {
                "action": "fold",
                "frequency": 1.0,
                "reason": f"{hero_hand} not strong enough vs raise",
            }
            alternatives = []
        
        return {
            "primary": primary,
            "alternatives": alternatives,
            "hand": hero_hand,
            "position": position,
            "stack_bb": stack_bb,
            "is_push_fold": False,
            "icm_adjusted": False,
            "range_strength": hand_strength,
            "notes": [],
        }
    
    def _get_vs_3bet_recommendation(
        self,
        game_state: GameState,
        hand_strength: float,
    ) -> dict:
        """Get recommendation when facing a 3-bet."""
        hero_hand = game_state.hero_hand
        position = game_state.hero_position
        stack_bb = game_state.hero_stack_bb
        
        # Only continue with premium hands
        if hand_strength >= 0.94:  # QQ+, AKs
            primary = {
                "action": "raise",  # 4-bet
                "size": 2.5,
                "frequency": 0.8,
                "reason": f"4-bet {hero_hand} for value",
            }
            alternatives = [
                {"action": "call", "frequency": 0.2, "reason": "Flat to trap"},
            ]
        elif hand_strength >= 0.88:  # JJ, AKo
            primary = {
                "action": "call",
                "frequency": 0.7,
                "reason": f"Call with {hero_hand}, evaluate flop",
            }
            alternatives = [
                {"action": "raise", "frequency": 0.3, "reason": "4-bet for value sometimes"},
            ]
        else:
            primary = {
                "action": "fold",
                "frequency": 1.0,
                "reason": f"{hero_hand} cannot profitably continue vs 3-bet",
            }
            alternatives = []
        
        return {
            "primary": primary,
            "alternatives": alternatives,
            "hand": hero_hand,
            "position": position,
            "stack_bb": stack_bb,
            "is_push_fold": False,
            "icm_adjusted": False,
            "range_strength": hand_strength,
            "notes": ["Facing 3-bet: tighten significantly"],
        }
    
    def _get_postflop_recommendation(self, game_state: GameState) -> dict:
        """Get postflop recommendation (simplified)."""
        # Postflop analysis is complex and would require:
        # - Board texture analysis
        # - Hand vs range evaluation
        # - Position considerations
        # - Pot odds calculations
        
        hero_hand = game_state.hero_hand
        position = game_state.hero_position
        street = game_state.street
        pot_bb = game_state.pot_bb
        
        return {
            "primary": {
                "action": "check",
                "frequency": 0.5,
                "reason": "Postflop analysis not yet implemented",
            },
            "alternatives": [
                {"action": "bet", "size": pot_bb * 0.5, "frequency": 0.5, "reason": "Standard c-bet"},
            ],
            "hand": hero_hand,
            "position": position,
            "stack_bb": game_state.hero_stack_bb,
            "street": street,
            "is_push_fold": False,
            "icm_adjusted": False,
            "range_strength": 0.5,
            "notes": [f"Street: {street}", "Full postflop solver coming soon"],
        }
    
    def _is_facing_raise(self, game_state: GameState) -> bool:
        """Check if hero is facing a raise."""
        for player in game_state.players:
            if not player.is_hero and player.current_bet > game_state.big_blind:
                return True
        return False
    
    def _is_facing_3bet(self, game_state: GameState) -> bool:
        """Check if hero is facing a 3-bet (re-raise)."""
        # Simplified: check if there are multiple raises
        raise_count = sum(
            1 for p in game_state.players
            if p.current_bet > game_state.big_blind * 2
        )
        return raise_count >= 1 and self._is_facing_raise(game_state)
    
    def _count_players_behind(self, game_state: GameState) -> int:
        """Count active players yet to act."""
        hero = game_state.hero
        if not hero:
            return 0
        
        # This is simplified - would need action order tracking
        return sum(
            1 for p in game_state.players
            if p.is_active and not p.is_hero and not p.is_turn
        )
