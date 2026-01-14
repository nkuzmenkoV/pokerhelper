"""
Push/Fold charts for short stack play.

Based on Nash equilibrium solutions for push/fold scenarios,
loaded from JSON chart files.
"""

from typing import Optional
from dataclasses import dataclass

from app.db.charts import get_push_fold_range, get_call_range, is_hand_in_range


@dataclass
class PushFoldDecision:
    """Result of push/fold analysis."""
    action: str  # "push", "fold", "call"
    equity: float  # Expected equity
    hand_strength: float  # Hand ranking 0-1
    chart_position: str  # Position in the chart
    in_range: bool  # Whether hand is in optimal range


# Hand rankings (higher = better)
# Based on Sklansky-Chubukov rankings for push/fold play
HAND_RANKINGS = {
    # Pocket pairs
    "AA": 1.00, "KK": 0.98, "QQ": 0.96, "JJ": 0.94, "TT": 0.90,
    "99": 0.85, "88": 0.80, "77": 0.75, "66": 0.70, "55": 0.65,
    "44": 0.60, "33": 0.55, "22": 0.50,
    
    # Suited Aces
    "AKs": 0.95, "AQs": 0.90, "AJs": 0.85, "ATs": 0.82,
    "A9s": 0.75, "A8s": 0.72, "A7s": 0.70, "A6s": 0.68,
    "A5s": 0.70, "A4s": 0.68, "A3s": 0.66, "A2s": 0.64,
    
    # Offsuit Aces
    "AKo": 0.88, "AQo": 0.82, "AJo": 0.78, "ATo": 0.74,
    "A9o": 0.68, "A8o": 0.65, "A7o": 0.62, "A6o": 0.60,
    "A5o": 0.62, "A4o": 0.58, "A3o": 0.56, "A2o": 0.54,
    
    # Suited Kings
    "KQs": 0.82, "KJs": 0.78, "KTs": 0.75, "K9s": 0.68,
    "K8s": 0.62, "K7s": 0.58, "K6s": 0.55, "K5s": 0.52,
    "K4s": 0.50, "K3s": 0.48, "K2s": 0.46,
    
    # Offsuit Kings
    "KQo": 0.75, "KJo": 0.70, "KTo": 0.66, "K9o": 0.58,
    "K8o": 0.50, "K7o": 0.46, "K6o": 0.42, "K5o": 0.40,
    "K4o": 0.38, "K3o": 0.36, "K2o": 0.34,
    
    # Suited Queens
    "QJs": 0.72, "QTs": 0.68, "Q9s": 0.60, "Q8s": 0.52,
    "Q7s": 0.48, "Q6s": 0.45, "Q5s": 0.42, "Q4s": 0.40,
    "Q3s": 0.38, "Q2s": 0.36,
    
    # Offsuit Queens
    "QJo": 0.65, "QTo": 0.60, "Q9o": 0.50, "Q8o": 0.42,
    "Q7o": 0.38, "Q6o": 0.35, "Q5o": 0.32, "Q4o": 0.30,
    "Q3o": 0.28, "Q2o": 0.26,
    
    # Suited Jacks
    "JTs": 0.68, "J9s": 0.58, "J8s": 0.50, "J7s": 0.45,
    "J6s": 0.40, "J5s": 0.38, "J4s": 0.35, "J3s": 0.33,
    "J2s": 0.31,
    
    # Offsuit Jacks
    "JTo": 0.58, "J9o": 0.48, "J8o": 0.40, "J7o": 0.35,
    "J6o": 0.30, "J5o": 0.28, "J4o": 0.26, "J3o": 0.24,
    "J2o": 0.22,
    
    # Suited Tens
    "T9s": 0.55, "T8s": 0.48, "T7s": 0.42, "T6s": 0.38,
    "T5s": 0.34, "T4s": 0.32, "T3s": 0.30, "T2s": 0.28,
    
    # Offsuit Tens
    "T9o": 0.45, "T8o": 0.38, "T7o": 0.32, "T6o": 0.28,
    "T5o": 0.24, "T4o": 0.22, "T3o": 0.20, "T2o": 0.18,
    
    # Suited connectors and others
    "98s": 0.48, "97s": 0.40, "96s": 0.35, "95s": 0.30, "94s": 0.26, "93s": 0.24, "92s": 0.22,
    "87s": 0.45, "86s": 0.38, "85s": 0.32, "84s": 0.28, "83s": 0.24, "82s": 0.22,
    "76s": 0.42, "75s": 0.35, "74s": 0.28, "73s": 0.24, "72s": 0.20,
    "65s": 0.40, "64s": 0.32, "63s": 0.26, "62s": 0.22,
    "54s": 0.38, "53s": 0.30, "52s": 0.24,
    "43s": 0.32, "42s": 0.25,
    "32s": 0.28,
    
    # Offsuit connectors
    "98o": 0.38, "97o": 0.30, "96o": 0.25, "95o": 0.20, "94o": 0.18, "93o": 0.16, "92o": 0.14,
    "87o": 0.35, "86o": 0.28, "85o": 0.22, "84o": 0.18, "83o": 0.16, "82o": 0.14,
    "76o": 0.32, "75o": 0.25, "74o": 0.20, "73o": 0.16, "72o": 0.12,
    "65o": 0.30, "64o": 0.22, "63o": 0.18, "62o": 0.14,
    "54o": 0.28, "53o": 0.20, "52o": 0.16,
    "43o": 0.22, "42o": 0.18,
    "32o": 0.18,
}


class PushFoldCalculator:
    """Calculator for push/fold decisions in short stack situations."""
    
    def __init__(self, table_format: str = "9max"):
        self.table_format = table_format
    
    def get_hand_strength(self, hand: str) -> float:
        """Get normalized hand strength (0-1)."""
        if hand in HAND_RANKINGS:
            return HAND_RANKINGS[hand]
        
        # Try to normalize hand notation
        normalized = self._normalize_hand(hand)
        return HAND_RANKINGS.get(normalized, 0.3)
    
    def _normalize_hand(self, hand: str) -> str:
        """Normalize hand notation (e.g., 'KAs' -> 'AKs')."""
        if len(hand) < 2:
            return hand
        
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        rank_order = {r: i for i, r in enumerate(ranks)}
        
        r1, r2 = hand[0].upper(), hand[1].upper()
        suffix = hand[2:].lower() if len(hand) > 2 else ""
        
        # Sort ranks (higher first)
        if rank_order.get(r1, 0) < rank_order.get(r2, 0):
            r1, r2 = r2, r1
        
        # Pairs don't have suffix
        if r1 == r2:
            return f"{r1}{r2}"
        
        return f"{r1}{r2}{suffix}"
    
    def should_push(
        self,
        hand: str,
        position: str,
        stack_bb: float,
        facing_raise: bool = False,
        num_players_behind: int = 0,
    ) -> PushFoldDecision:
        """
        Determine if hero should push all-in.
        
        Args:
            hand: Hand notation (e.g., "AKs", "QQ")
            position: Position (UTG, MP, CO, BTN, SB, BB)
            stack_bb: Stack in big blinds
            facing_raise: Whether facing a raise
            num_players_behind: Number of players yet to act
        """
        normalized_hand = self._normalize_hand(hand)
        hand_strength = self.get_hand_strength(normalized_hand)
        
        # Get push range from JSON charts
        push_range = get_push_fold_range(
            position=position,
            stack_bb=int(stack_bb),
            table_format=self.table_format
        )
        
        # Check if hand is in range
        in_range = is_hand_in_range(normalized_hand, push_range)
        
        # Adjust for facing raise (need tighter range)
        if facing_raise:
            # When facing raise, tighten by ~20%
            if in_range and hand_strength < 0.70:
                in_range = hand_strength >= 0.55
        
        # Adjust for players behind (tighten range)
        if num_players_behind > 3 and in_range:
            if hand_strength < 0.65:
                in_range = False
        
        action = "push" if in_range else "fold"
        
        return PushFoldDecision(
            action=action,
            equity=hand_strength,
            hand_strength=hand_strength,
            chart_position=f"{position}_{int(stack_bb)}BB",
            in_range=in_range,
        )
    
    def should_call(
        self,
        hand: str,
        position: str,
        stack_bb: float,
        villain_position: str = "SB",
        pot_bb: float = 1.5,
    ) -> PushFoldDecision:
        """
        Determine if hero should call an all-in.
        
        Args:
            hand: Hand notation
            position: Hero's position
            stack_bb: Hero's stack in BB
            villain_position: Villain's position
            pot_bb: Current pot in BB
        """
        normalized_hand = self._normalize_hand(hand)
        hand_strength = self.get_hand_strength(normalized_hand)
        
        # Get call range from JSON charts
        call_range = get_call_range(
            position=position,
            stack_bb=int(stack_bb),
            table_format=self.table_format,
            vs_position=villain_position
        )
        
        in_range = is_hand_in_range(normalized_hand, call_range)
        
        # Adjust for pot odds
        call_amount = min(stack_bb, stack_bb)  # Simplified
        total_pot = pot_bb + call_amount * 2
        required_equity = call_amount / total_pot if total_pot > 0 else 0.5
        
        # If getting great pot odds, widen calling range
        if required_equity < 0.35 and hand_strength >= 0.40:
            in_range = True
        
        action = "call" if in_range else "fold"
        
        return PushFoldDecision(
            action=action,
            equity=hand_strength,
            hand_strength=hand_strength,
            chart_position=f"call_{position}_vs_{villain_position}_{int(stack_bb)}BB",
            in_range=in_range,
        )
    
    def get_push_range(self, position: str, stack_bb: float) -> list[str]:
        """Get all hands that should be pushed from this position/stack."""
        return get_push_fold_range(
            position=position,
            stack_bb=int(stack_bb),
            table_format=self.table_format
        )
    
    def get_call_range(
        self, 
        position: str, 
        stack_bb: float, 
        vs_position: str = "SB"
    ) -> list[str]:
        """Get all hands that should call an all-in."""
        return get_call_range(
            position=position,
            stack_bb=int(stack_bb),
            table_format=self.table_format,
            vs_position=vs_position
        )
    
    def get_range_percentage(self, range_list: list[str]) -> float:
        """Calculate what percentage of hands a range represents."""
        if not range_list:
            return 0.0
        
        if "any" in range_list:
            return 100.0
        
        # Total possible starting hands: 169 unique combinations
        # But actual combos: 1326
        # Pairs: 13 * 6 = 78
        # Suited: 78 * 4 = 312  
        # Offsuit: 78 * 12 = 936
        
        total_combos = 1326
        range_combos = 0
        
        for hand in range_list:
            if len(hand) == 2:  # Pair
                range_combos += 6
            elif hand.endswith('s'):  # Suited
                range_combos += 4
            elif hand.endswith('o'):  # Offsuit
                range_combos += 12
        
        return (range_combos / total_combos) * 100
