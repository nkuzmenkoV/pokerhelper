"""
Push/Fold charts for short stack play.

Based on Nash equilibrium solutions for heads-up push/fold scenarios,
adjusted for different stack depths and positions.
"""

from typing import Optional
from dataclasses import dataclass


@dataclass
class PushFoldDecision:
    """Result of push/fold analysis."""
    action: str  # "push", "fold", "call"
    equity: float  # Expected equity
    hand_strength: float  # Hand ranking 0-1
    chart_position: str  # Position in the chart


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
    "98s": 0.48, "97s": 0.40, "96s": 0.35, "95s": 0.30,
    "87s": 0.45, "86s": 0.38, "85s": 0.32,
    "76s": 0.42, "75s": 0.35, "74s": 0.28,
    "65s": 0.40, "64s": 0.32, "63s": 0.26,
    "54s": 0.38, "53s": 0.30, "52s": 0.24,
    "43s": 0.32, "42s": 0.25,
    "32s": 0.28,
    
    # Offsuit connectors
    "98o": 0.38, "97o": 0.30, "96o": 0.25,
    "87o": 0.35, "86o": 0.28, "85o": 0.22,
    "76o": 0.32, "75o": 0.25,
    "65o": 0.30, "64o": 0.22,
    "54o": 0.28, "53o": 0.20,
    "43o": 0.22, "42o": 0.18,
    "32o": 0.18,
}


# Push ranges by position and stack depth (in BB)
# Values represent minimum hand strength to push
PUSH_THRESHOLDS = {
    # Stack: {Position: min_hand_strength}
    3: {  # 3BB - very wide pushing range
        "BTN": 0.20, "SB": 0.25, "BB": 0.30,
        "CO": 0.35, "MP": 0.45, "UTG": 0.55,
    },
    5: {  # 5BB
        "BTN": 0.30, "SB": 0.35, "BB": 0.40,
        "CO": 0.45, "MP": 0.55, "UTG": 0.65,
    },
    8: {  # 8BB
        "BTN": 0.40, "SB": 0.45, "BB": 0.50,
        "CO": 0.55, "MP": 0.65, "UTG": 0.75,
    },
    10: {  # 10BB
        "BTN": 0.50, "SB": 0.55, "BB": 0.60,
        "CO": 0.65, "MP": 0.72, "UTG": 0.80,
    },
    12: {  # 12BB
        "BTN": 0.55, "SB": 0.60, "BB": 0.65,
        "CO": 0.70, "MP": 0.78, "UTG": 0.85,
    },
    15: {  # 15BB - tightest push range
        "BTN": 0.65, "SB": 0.68, "BB": 0.72,
        "CO": 0.75, "MP": 0.82, "UTG": 0.90,
    },
}


# Call ranges (vs all-in) by position
CALL_THRESHOLDS = {
    3: {"BB": 0.35, "SB": 0.40, "BTN": 0.50, "CO": 0.60, "MP": 0.70, "UTG": 0.80},
    5: {"BB": 0.45, "SB": 0.50, "BTN": 0.60, "CO": 0.68, "MP": 0.75, "UTG": 0.85},
    8: {"BB": 0.55, "SB": 0.60, "BTN": 0.68, "CO": 0.75, "MP": 0.82, "UTG": 0.88},
    10: {"BB": 0.60, "SB": 0.65, "BTN": 0.72, "CO": 0.78, "MP": 0.85, "UTG": 0.90},
    12: {"BB": 0.65, "SB": 0.70, "BTN": 0.76, "CO": 0.82, "MP": 0.88, "UTG": 0.92},
    15: {"BB": 0.70, "SB": 0.75, "BTN": 0.80, "CO": 0.85, "MP": 0.90, "UTG": 0.95},
}


class PushFoldCalculator:
    """Calculator for push/fold decisions in short stack situations."""
    
    def __init__(self):
        pass
    
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
        
        r1, r2 = hand[0], hand[1]
        suffix = hand[2:] if len(hand) > 2 else ""
        
        # Sort ranks (higher first)
        if rank_order.get(r1, 0) < rank_order.get(r2, 0):
            r1, r2 = r2, r1
        
        return f"{r1}{r2}{suffix}"
    
    def _get_stack_bucket(self, stack_bb: float) -> int:
        """Get the nearest stack bucket for threshold lookup."""
        buckets = [3, 5, 8, 10, 12, 15]
        for bucket in buckets:
            if stack_bb <= bucket:
                return bucket
        return 15
    
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
        hand_strength = self.get_hand_strength(hand)
        stack_bucket = self._get_stack_bucket(stack_bb)
        
        # Get threshold for this position and stack
        thresholds = PUSH_THRESHOLDS.get(stack_bucket, PUSH_THRESHOLDS[15])
        threshold = thresholds.get(position, 0.70)
        
        # Adjust for players behind
        threshold += num_players_behind * 0.03
        
        # Adjust if facing raise (need tighter range)
        if facing_raise:
            threshold += 0.15
        
        # Clamp threshold
        threshold = min(threshold, 0.98)
        
        action = "push" if hand_strength >= threshold else "fold"
        
        return PushFoldDecision(
            action=action,
            equity=hand_strength,
            hand_strength=hand_strength,
            chart_position=f"{position}_{stack_bucket}BB",
        )
    
    def should_call(
        self,
        hand: str,
        position: str,
        stack_bb: float,
        villain_stack_bb: float,
        pot_bb: float = 1.5,
    ) -> PushFoldDecision:
        """
        Determine if hero should call an all-in.
        
        Args:
            hand: Hand notation
            position: Hero's position
            stack_bb: Hero's stack in BB
            villain_stack_bb: Villain's all-in amount in BB
            pot_bb: Current pot in BB
        """
        hand_strength = self.get_hand_strength(hand)
        
        # Calculate pot odds
        call_amount = min(stack_bb, villain_stack_bb)
        total_pot = pot_bb + call_amount * 2
        required_equity = call_amount / total_pot
        
        # Get calling threshold
        stack_bucket = self._get_stack_bucket(villain_stack_bb)
        thresholds = CALL_THRESHOLDS.get(stack_bucket, CALL_THRESHOLDS[15])
        threshold = thresholds.get(position, 0.70)
        
        # Adjust for pot odds
        threshold = max(threshold - (0.5 - required_equity) * 0.3, required_equity + 0.05)
        
        action = "call" if hand_strength >= threshold else "fold"
        
        return PushFoldDecision(
            action=action,
            equity=hand_strength,
            hand_strength=hand_strength,
            chart_position=f"call_{position}_{stack_bucket}BB",
        )
    
    def get_push_range(self, position: str, stack_bb: float) -> list[str]:
        """Get all hands that should be pushed from this position/stack."""
        stack_bucket = self._get_stack_bucket(stack_bb)
        thresholds = PUSH_THRESHOLDS.get(stack_bucket, PUSH_THRESHOLDS[15])
        threshold = thresholds.get(position, 0.70)
        
        return [
            hand for hand, strength in HAND_RANKINGS.items()
            if strength >= threshold
        ]
