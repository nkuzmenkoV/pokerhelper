"""
ICM (Independent Chip Model) Calculator for tournament poker.

ICM calculates the dollar value of tournament chips based on payout structure
and remaining stack sizes.
"""

from typing import Optional
from dataclasses import dataclass
from itertools import permutations


@dataclass
class ICMResult:
    """Result of ICM calculation."""
    chip_ev: float  # Expected value in chips
    dollar_ev: float  # Expected value in dollars
    icm_adjustment: float  # ICM adjustment factor
    risk_premium: float  # Extra equity needed due to ICM


class ICMCalculator:
    """
    Calculates ICM equity for tournament situations.
    
    ICM is crucial for final table and bubble play where chip
    value is non-linear due to payout structure.
    """
    
    def __init__(self):
        self._cache = {}
    
    def calculate_icm_equity(
        self,
        stacks: list[float],
        payouts: list[float],
        hero_index: int = 0,
    ) -> float:
        """
        Calculate hero's ICM equity (dollar EV).
        
        Args:
            stacks: List of player stacks (chips)
            payouts: List of payouts (descending order)
            hero_index: Index of hero in stacks list
            
        Returns:
            Hero's expected dollar value
        """
        if not stacks or not payouts:
            return 0.0
        
        # Normalize stacks
        total_chips = sum(stacks)
        if total_chips == 0:
            return 0.0
        
        normalized_stacks = [s / total_chips for s in stacks]
        
        # Use Malmuth-Harville method
        return self._malmuth_harville(normalized_stacks, payouts, hero_index)
    
    def _malmuth_harville(
        self,
        stacks: list[float],
        payouts: list[float],
        hero_index: int,
    ) -> float:
        """
        Malmuth-Harville ICM calculation.
        
        Probability of finishing in position i is proportional to stack size,
        with conditional probabilities for subsequent positions.
        """
        n_players = len(stacks)
        n_payouts = len(payouts)
        
        # For small player counts, we can enumerate all permutations
        if n_players <= 7:
            return self._exact_icm(stacks, payouts, hero_index)
        else:
            # For larger fields, use approximation
            return self._approximate_icm(stacks, payouts, hero_index)
    
    def _exact_icm(
        self,
        stacks: list[float],
        payouts: list[float],
        hero_index: int,
    ) -> float:
        """Exact ICM using recursive probability calculation."""
        n_players = len(stacks)
        n_payouts = min(len(payouts), n_players)
        
        # Calculate probability of each finish position for hero
        finish_probs = [0.0] * n_payouts
        
        # Probability of finishing 1st = stack proportion
        finish_probs[0] = stacks[hero_index]
        
        # For other positions, calculate conditional probabilities
        for pos in range(1, n_payouts):
            prob = self._prob_finish_position(stacks, hero_index, pos)
            finish_probs[pos] = prob
        
        # Expected value = sum of (probability * payout)
        ev = sum(p * payouts[i] for i, p in enumerate(finish_probs))
        return ev
    
    def _prob_finish_position(
        self,
        stacks: list[float],
        hero_index: int,
        position: int,
    ) -> float:
        """
        Calculate probability of hero finishing in given position.
        
        Uses recursive Malmuth-Harville formula.
        """
        n = len(stacks)
        if position == 0:
            return stacks[hero_index]
        
        # Sum over all players who could finish before hero
        prob = 0.0
        for i in range(n):
            if i == hero_index:
                continue
            
            # Probability that player i finishes first
            # multiplied by probability hero finishes in (position-1) of remaining
            p_i_first = stacks[i]
            
            # Remaining stacks without player i
            remaining_stacks = stacks[:i] + stacks[i+1:]
            new_hero_idx = hero_index if hero_index < i else hero_index - 1
            
            # Renormalize
            total = sum(remaining_stacks)
            if total > 0:
                remaining_stacks = [s / total for s in remaining_stacks]
                
                # Recursive probability
                if position == 1:
                    p_hero_next = remaining_stacks[new_hero_idx]
                else:
                    p_hero_next = self._prob_finish_position(
                        remaining_stacks, new_hero_idx, position - 1
                    )
                
                prob += p_i_first * p_hero_next
        
        return prob
    
    def _approximate_icm(
        self,
        stacks: list[float],
        payouts: list[float],
        hero_index: int,
    ) -> float:
        """Approximate ICM for large fields using simulation."""
        # Simple approximation: stack proportion of total prize pool
        total_prizes = sum(payouts)
        return stacks[hero_index] * total_prizes
    
    def calculate_icm_pressure(
        self,
        stacks: list[float],
        payouts: list[float],
        hero_index: int,
    ) -> float:
        """
        Calculate ICM pressure (how much to tighten up).
        
        Returns a multiplier (0.5 = very tight, 1.0 = neutral, 1.2 = can be looser).
        """
        n_players = len(stacks)
        hero_stack = stacks[hero_index]
        avg_stack = sum(stacks) / n_players
        
        # Calculate relative stack size
        rel_stack = hero_stack / avg_stack
        
        # Calculate payout jumps
        if len(payouts) < 2:
            return 1.0
        
        # Find where hero is likely to finish
        sorted_indices = sorted(range(n_players), key=lambda i: stacks[i], reverse=True)
        hero_rank = sorted_indices.index(hero_index)
        
        # ICM pressure is higher when:
        # 1. Near bubble or payout jump
        # 2. Short stacks can bust before you
        # 3. You have a medium stack (most to lose)
        
        # Bubble factor
        if hero_rank == n_players - 1:  # Short stack
            pressure = 0.7  # Can take more risks
        elif hero_rank < n_players // 3:  # Big stack
            pressure = 0.9  # Slightly more aggressive
        else:  # Medium stack
            pressure = 0.75  # Tightest
        
        # Adjust for stack depth
        if rel_stack < 0.5:
            pressure = min(pressure + 0.2, 1.0)
        elif rel_stack > 2.0:
            pressure = max(pressure - 0.1, 0.6)
        
        return pressure
    
    def calculate_calling_adjustment(
        self,
        stacks: list[float],
        payouts: list[float],
        hero_index: int,
        villain_index: int,
        pot_chips: float,
    ) -> float:
        """
        Calculate the equity edge needed to call due to ICM.
        
        Returns the minimum equity edge (above 50%) required.
        """
        # Current ICM equity
        current_icm = self.calculate_icm_equity(stacks, payouts, hero_index)
        
        hero_stack = stacks[hero_index]
        villain_stack = stacks[villain_index]
        
        # If we win
        win_stacks = stacks.copy()
        win_amount = min(hero_stack, villain_stack)
        win_stacks[hero_index] += win_amount
        win_stacks[villain_index] -= win_amount
        if win_stacks[villain_index] <= 0:
            win_stacks = [s for i, s in enumerate(win_stacks) if i != villain_index]
            win_hero_idx = hero_index if villain_index > hero_index else hero_index
            # Adjust index if villain was removed before hero
            if villain_index < hero_index:
                win_hero_idx = hero_index - 1
            else:
                win_hero_idx = hero_index
        else:
            win_hero_idx = hero_index
        
        win_icm = self.calculate_icm_equity(win_stacks, payouts, win_hero_idx)
        
        # If we lose
        lose_stacks = stacks.copy()
        lose_stacks[hero_index] -= win_amount
        lose_stacks[villain_index] += win_amount
        
        if lose_stacks[hero_index] <= 0:
            lose_icm = 0  # Busted
        else:
            lose_icm = self.calculate_icm_equity(lose_stacks, payouts, hero_index)
        
        # Required equity to break even
        # EV = equity * win_icm + (1-equity) * lose_icm >= current_icm
        # equity * (win_icm - lose_icm) >= current_icm - lose_icm
        
        icm_diff = win_icm - lose_icm
        if icm_diff <= 0:
            return 1.0  # Never profitable
        
        required_equity = (current_icm - lose_icm) / icm_diff
        
        return max(0, required_equity - 0.5)  # Edge above 50%


# Common tournament payout structures
PAYOUT_STRUCTURES = {
    "9_player_sng": [0.50, 0.30, 0.20],
    "6_player_sng": [0.65, 0.35],
    "18_player": [0.30, 0.20, 0.15, 0.12, 0.10, 0.08, 0.05],
    "45_player": [0.25, 0.17, 0.12, 0.09, 0.07, 0.06, 0.05, 0.04, 0.04, 0.03, 0.02, 0.02, 0.02, 0.01, 0.01],
    "mtt_final_table": [0.295, 0.175, 0.125, 0.095, 0.075, 0.065, 0.055, 0.045, 0.04],
}
