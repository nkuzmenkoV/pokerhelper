"""
GTO Engine - Main recommendation engine combining all poker logic.

Provides preflop and postflop recommendations based on:
- JSON-loaded GTO ranges
- Push/Fold charts
- ICM considerations
"""

from typing import Optional
from dataclasses import dataclass

from app.poker.game_state import GameState
from app.poker.push_fold import PushFoldCalculator
from app.poker.icm_calculator import ICMCalculator
from app.db.charts import (
    get_opening_range, 
    get_3bet_range, 
    is_hand_in_range,
    get_chart_stats
)


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


class GTOEngine:
    """Main GTO recommendation engine."""
    
    def __init__(self, table_format: str = "9max"):
        self.table_format = table_format
        self.push_fold = PushFoldCalculator(table_format=table_format)
        self.icm = ICMCalculator()
        
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
        
        # Update table format from game state
        self.table_format = game_state.table_format
        self.push_fold.table_format = game_state.table_format
        
        # Determine if push/fold applies (short stack)
        is_short_stack = game_state.hero_stack_bb <= 15
        
        if game_state.is_preflop:
            recommendation = self._get_preflop_recommendation(game_state, is_short_stack)
        else:
            recommendation = self._get_postflop_recommendation(game_state)
        
        return recommendation
    
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
            
            # Get push range percentage for notes
            push_range = self.push_fold.get_push_range(position, stack_bb)
            range_pct = self.push_fold.get_range_percentage(push_range)
            
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
                    reason=f"{hero_hand} not in push range from {position}",
                )
                alternatives = []
            
            notes.append(f"Push/Fold mode: Stack = {stack_bb:.1f}BB")
            notes.append(f"Push range: {range_pct:.1f}% of hands")
            
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
                "in_range": pf_result.in_range,
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
        
        # Get opening range from JSON charts
        open_data = get_opening_range(position, self.table_format)
        open_range = open_data.get("raise", [])
        raise_size = open_data.get("raise_size", 2.5)
        
        in_range = is_hand_in_range(hero_hand, open_range)
        range_pct = self.push_fold.get_range_percentage(open_range)
        
        if in_range:
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
            "in_range": in_range,
            "notes": [
                f"Opening range from {position}: ~{range_pct:.0f}%",
                open_data.get("description", "")
            ],
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
        
        # Determine villain's position
        villain_position = self._get_raiser_position(game_state)
        
        # Get 3-bet range from JSON charts
        three_bet_data = get_3bet_range(villain_position)
        value_range = three_bet_data.get("3bet_value", [])
        bluff_range = three_bet_data.get("3bet_bluff", [])
        call_range = three_bet_data.get("call", [])
        
        in_value = is_hand_in_range(hero_hand, value_range)
        in_bluff = is_hand_in_range(hero_hand, bluff_range)
        in_call = is_hand_in_range(hero_hand, call_range)
        
        # Determine action
        if in_value:
            primary = {
                "action": "raise",
                "size": 3.0,  # 3x the open
                "frequency": 1.0,
                "reason": f"3-bet {hero_hand} for value vs {villain_position}",
            }
            alternatives = [
                {"action": "call", "frequency": 0.0, "reason": "Occasionally flat to disguise"},
            ]
        elif in_bluff:
            primary = {
                "action": "raise",
                "size": 3.0,
                "frequency": 0.5,
                "reason": f"3-bet {hero_hand} as bluff vs {villain_position}",
            }
            alternatives = [
                {"action": "fold", "frequency": 0.5, "reason": "Can also fold this hand"},
            ]
        elif in_call:
            primary = {
                "action": "call",
                "frequency": 1.0,
                "reason": f"Call with {hero_hand} vs {villain_position} raise",
            }
            alternatives = []
        else:
            primary = {
                "action": "fold",
                "frequency": 1.0,
                "reason": f"{hero_hand} not strong enough vs {villain_position}",
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
            "in_range": in_value or in_bluff or in_call,
            "notes": [
                f"Facing raise from {villain_position}",
                three_bet_data.get("description", "")
            ],
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
        
        # Only continue with premium hands vs 3-bet
        if hand_strength >= 0.94:  # QQ+, AKs
            primary = {
                "action": "raise",  # 4-bet
                "size": 2.25,
                "frequency": 0.8,
                "reason": f"4-bet {hero_hand} for value",
            }
            alternatives = [
                {"action": "call", "frequency": 0.2, "reason": "Flat to trap occasionally"},
            ]
            in_range = True
        elif hand_strength >= 0.88:  # JJ, AKo, QQ
            primary = {
                "action": "call",
                "frequency": 0.7,
                "reason": f"Call with {hero_hand}, evaluate flop",
            }
            alternatives = [
                {"action": "raise", "frequency": 0.3, "reason": "4-bet for value sometimes"},
            ]
            in_range = True
        elif hand_strength >= 0.70:  # A5s (blocker bluff)
            if hero_hand in ["A5s", "A4s", "A3s"]:
                primary = {
                    "action": "raise",
                    "size": 2.25,
                    "frequency": 0.4,
                    "reason": f"4-bet {hero_hand} as blocker bluff",
                }
                alternatives = [
                    {"action": "fold", "frequency": 0.6, "reason": "Fold most of the time"},
                ]
                in_range = True
            else:
                primary = {
                    "action": "fold",
                    "frequency": 1.0,
                    "reason": f"{hero_hand} cannot profitably continue vs 3-bet",
                }
                alternatives = []
                in_range = False
        else:
            primary = {
                "action": "fold",
                "frequency": 1.0,
                "reason": f"{hero_hand} cannot profitably continue vs 3-bet",
            }
            alternatives = []
            in_range = False
        
        return {
            "primary": primary,
            "alternatives": alternatives,
            "hand": hero_hand,
            "position": position,
            "stack_bb": stack_bb,
            "is_push_fold": False,
            "icm_adjusted": False,
            "range_strength": hand_strength,
            "in_range": in_range,
            "notes": ["Facing 3-bet: tighten significantly"],
        }
    
    def _get_postflop_recommendation(self, game_state: GameState) -> dict:
        """Get postflop recommendation (simplified)."""
        hero_hand = game_state.hero_hand
        position = game_state.hero_position
        street = game_state.street
        pot_bb = game_state.pot_bb
        
        return {
            "primary": {
                "action": "check",
                "frequency": 0.5,
                "reason": "Postflop analysis - see solver for details",
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
            "in_range": True,
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
        
        return sum(
            1 for p in game_state.players
            if p.is_active and not p.is_hero and not p.is_turn
        )
    
    def _get_raiser_position(self, game_state: GameState) -> str:
        """Get the position of the player who raised."""
        for player in game_state.players:
            if not player.is_hero and player.current_bet > game_state.big_blind:
                return player.position or "UTG"
        return "UTG"
    
    def get_chart_info(self) -> dict:
        """Get information about loaded charts."""
        return get_chart_stats()
