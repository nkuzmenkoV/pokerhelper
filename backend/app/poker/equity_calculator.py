"""
Poker Equity Calculator

Calculates hand equity (probability of winning) against opponent ranges
using Monte Carlo simulation.

Features:
- Preflop equity vs random hand
- Equity vs specific range
- Monte Carlo simulation for any board state
- Optimized for real-time calculations
"""

import random
from dataclasses import dataclass
from typing import Optional
from itertools import combinations
import time


# Card representation
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
SUITS = ['c', 'd', 'h', 's']

RANK_VALUES = {r: i for i, r in enumerate(RANKS)}

# Full deck
FULL_DECK = [f"{r}{s}" for r in RANKS for s in SUITS]


@dataclass
class EquityResult:
    """Result of equity calculation."""
    equity: float  # Win probability (0-1)
    win_pct: float  # Win percentage
    tie_pct: float  # Tie percentage
    lose_pct: float  # Lose percentage
    simulations: int  # Number of simulations run
    time_ms: float  # Calculation time in milliseconds


class HandEvaluator:
    """
    Evaluates poker hand strength.
    
    Returns a comparable score where higher is better.
    Hand rankings:
    - 8: Straight Flush
    - 7: Four of a Kind
    - 6: Full House
    - 5: Flush
    - 4: Straight
    - 3: Three of a Kind
    - 2: Two Pair
    - 1: One Pair
    - 0: High Card
    """
    
    @staticmethod
    def card_rank(card: str) -> int:
        """Get numeric rank value of a card."""
        return RANK_VALUES[card[0]]
    
    @staticmethod
    def card_suit(card: str) -> str:
        """Get suit of a card."""
        return card[1]
    
    def evaluate(self, cards: list[str]) -> tuple[int, list[int]]:
        """
        Evaluate 5-7 cards and return best 5-card hand score.
        
        Returns:
            Tuple of (hand_rank, kickers) for comparison
        """
        if len(cards) < 5:
            return (0, [0])
        
        # Try all 5-card combinations
        best_score = (0, [0])
        
        for combo in combinations(cards, 5):
            score = self._evaluate_five(list(combo))
            if score > best_score:
                best_score = score
        
        return best_score
    
    def _evaluate_five(self, cards: list[str]) -> tuple[int, list[int]]:
        """Evaluate exactly 5 cards."""
        ranks = sorted([self.card_rank(c) for c in cards], reverse=True)
        suits = [self.card_suit(c) for c in cards]
        
        is_flush = len(set(suits)) == 1
        
        # Check for straight
        is_straight = False
        straight_high = 0
        
        if ranks == list(range(ranks[0], ranks[0] - 5, -1)):
            is_straight = True
            straight_high = ranks[0]
        # Wheel (A-2-3-4-5)
        elif ranks == [12, 3, 2, 1, 0]:
            is_straight = True
            straight_high = 3  # 5-high straight
        
        # Count rank occurrences
        rank_counts = {}
        for r in ranks:
            rank_counts[r] = rank_counts.get(r, 0) + 1
        
        counts = sorted(rank_counts.values(), reverse=True)
        count_ranks = sorted(rank_counts.keys(), key=lambda r: (rank_counts[r], r), reverse=True)
        
        # Determine hand rank
        if is_straight and is_flush:
            return (8, [straight_high])  # Straight flush
        
        if counts == [4, 1]:
            return (7, count_ranks)  # Four of a kind
        
        if counts == [3, 2]:
            return (6, count_ranks)  # Full house
        
        if is_flush:
            return (5, ranks)  # Flush
        
        if is_straight:
            return (4, [straight_high])  # Straight
        
        if counts == [3, 1, 1]:
            return (3, count_ranks)  # Three of a kind
        
        if counts == [2, 2, 1]:
            return (2, count_ranks)  # Two pair
        
        if counts == [2, 1, 1, 1]:
            return (1, count_ranks)  # One pair
        
        return (0, ranks)  # High card


class EquityCalculator:
    """
    Calculates poker equity using Monte Carlo simulation.
    """
    
    def __init__(self):
        self.evaluator = HandEvaluator()
        
        # Precomputed preflop equities vs random hand
        self._preflop_cache = {}
    
    def calculate_equity(
        self,
        hero_cards: list[str],
        board: list[str] = None,
        villain_range: list[list[str]] = None,
        num_simulations: int = 10000,
        num_villains: int = 1,
    ) -> EquityResult:
        """
        Calculate hero's equity.
        
        Args:
            hero_cards: Hero's hole cards (e.g., ["As", "Kh"])
            board: Community cards (0-5 cards)
            villain_range: List of possible villain hands, or None for random
            num_simulations: Number of Monte Carlo simulations
            num_villains: Number of opponents
            
        Returns:
            EquityResult with win/tie/lose percentages
        """
        start_time = time.time()
        
        board = board or []
        dead_cards = set(hero_cards + board)
        
        # Available deck
        deck = [c for c in FULL_DECK if c not in dead_cards]
        
        wins = 0
        ties = 0
        losses = 0
        
        for _ in range(num_simulations):
            # Shuffle deck
            random.shuffle(deck)
            deck_idx = 0
            
            # Deal villain cards
            villain_hands = []
            for v in range(num_villains):
                if villain_range and len(villain_range) > 0:
                    # Pick from range
                    hand = random.choice(villain_range)
                    # Make sure cards aren't used
                    while any(c in dead_cards or c in [card for h in villain_hands for card in h] for c in hand):
                        hand = random.choice(villain_range)
                    villain_hands.append(hand)
                else:
                    # Random hand
                    v_cards = []
                    while len(v_cards) < 2:
                        card = deck[deck_idx]
                        deck_idx += 1
                        if card not in [c for h in villain_hands for c in h]:
                            v_cards.append(card)
                    villain_hands.append(v_cards)
            
            # Complete the board
            sim_board = list(board)
            while len(sim_board) < 5:
                card = deck[deck_idx]
                deck_idx += 1
                if card not in [c for h in villain_hands for c in h]:
                    sim_board.append(card)
            
            # Evaluate hands
            hero_score = self.evaluator.evaluate(hero_cards + sim_board)
            
            hero_wins = True
            hero_ties = False
            
            for v_hand in villain_hands:
                v_score = self.evaluator.evaluate(v_hand + sim_board)
                
                if v_score > hero_score:
                    hero_wins = False
                    break
                elif v_score == hero_score:
                    hero_ties = True
            
            if hero_wins and not hero_ties:
                wins += 1
            elif hero_ties:
                ties += 1
            else:
                losses += 1
        
        total = wins + ties + losses
        elapsed_ms = (time.time() - start_time) * 1000
        
        return EquityResult(
            equity=(wins + ties * 0.5) / total,
            win_pct=wins / total * 100,
            tie_pct=ties / total * 100,
            lose_pct=losses / total * 100,
            simulations=num_simulations,
            time_ms=elapsed_ms,
        )
    
    def preflop_equity(
        self,
        hero_cards: list[str],
        num_villains: int = 1,
        num_simulations: int = 10000,
    ) -> EquityResult:
        """
        Calculate preflop equity vs random hands.
        
        Uses cache for common hands.
        """
        # Normalize hand for caching
        hand_key = self._normalize_hand(hero_cards)
        cache_key = (hand_key, num_villains)
        
        if cache_key in self._preflop_cache:
            cached = self._preflop_cache[cache_key]
            return EquityResult(
                equity=cached["equity"],
                win_pct=cached["win_pct"],
                tie_pct=cached["tie_pct"],
                lose_pct=cached["lose_pct"],
                simulations=cached["simulations"],
                time_ms=0.1,  # From cache
            )
        
        result = self.calculate_equity(
            hero_cards=hero_cards,
            board=[],
            villain_range=None,
            num_simulations=num_simulations,
            num_villains=num_villains,
        )
        
        # Cache the result
        self._preflop_cache[cache_key] = {
            "equity": result.equity,
            "win_pct": result.win_pct,
            "tie_pct": result.tie_pct,
            "lose_pct": result.lose_pct,
            "simulations": result.simulations,
        }
        
        return result
    
    def _normalize_hand(self, cards: list[str]) -> str:
        """Normalize hand for caching (suit-agnostic for pairs/offsuit)."""
        if len(cards) != 2:
            return "".join(sorted(cards))
        
        r1, r2 = cards[0][0], cards[1][0]
        s1, s2 = cards[0][1], cards[1][1]
        
        # Sort by rank
        if RANK_VALUES[r1] < RANK_VALUES[r2]:
            r1, r2 = r2, r1
            s1, s2 = s2, s1
        
        if r1 == r2:
            return f"{r1}{r2}"  # Pair
        elif s1 == s2:
            return f"{r1}{r2}s"  # Suited
        else:
            return f"{r1}{r2}o"  # Offsuit
    
    def equity_vs_range(
        self,
        hero_cards: list[str],
        villain_range_str: str,
        board: list[str] = None,
        num_simulations: int = 5000,
    ) -> EquityResult:
        """
        Calculate equity against a specific range.
        
        Args:
            hero_cards: Hero's hole cards
            villain_range_str: Range string (e.g., "AA,KK,QQ,AKs")
            board: Community cards
            num_simulations: Number of simulations
        """
        villain_range = self._parse_range(villain_range_str)
        
        return self.calculate_equity(
            hero_cards=hero_cards,
            board=board,
            villain_range=villain_range,
            num_simulations=num_simulations,
        )
    
    def _parse_range(self, range_str: str) -> list[list[str]]:
        """
        Parse range string into list of hands.
        
        Examples:
            "AA" -> all 6 combos of pocket aces
            "AKs" -> all 4 suited AK combos
            "AKo" -> all 12 offsuit AK combos
            "AA,KK" -> all aces and kings
            "TT+" -> TT, JJ, QQ, KK, AA
            "ATs+" -> ATs, AJs, AQs, AKs
        """
        hands = []
        
        parts = [p.strip() for p in range_str.split(",")]
        
        for part in parts:
            if not part:
                continue
            
            # Handle "+" notation
            if "+" in part:
                base = part.replace("+", "")
                hands.extend(self._expand_plus_range(base))
            else:
                hands.extend(self._expand_hand(part))
        
        return hands
    
    def _expand_hand(self, hand_str: str) -> list[list[str]]:
        """Expand hand notation to all combos."""
        if len(hand_str) == 2:
            # Pocket pair
            r = hand_str[0]
            combos = []
            for s1, s2 in combinations(SUITS, 2):
                combos.append([f"{r}{s1}", f"{r}{s2}"])
            return combos
        
        elif len(hand_str) == 3:
            r1, r2, suitedness = hand_str[0], hand_str[1], hand_str[2]
            combos = []
            
            if suitedness == 's':
                # Suited
                for s in SUITS:
                    combos.append([f"{r1}{s}", f"{r2}{s}"])
            else:
                # Offsuit
                for s1 in SUITS:
                    for s2 in SUITS:
                        if s1 != s2:
                            combos.append([f"{r1}{s1}", f"{r2}{s2}"])
            
            return combos
        
        return []
    
    def _expand_plus_range(self, base: str) -> list[list[str]]:
        """Expand AA+ or ATs+ notation."""
        hands = []
        
        if len(base) == 2 and base[0] == base[1]:
            # Pair+: TT+ means TT, JJ, QQ, KK, AA
            start_rank = RANK_VALUES[base[0]]
            for r in RANKS[start_rank:]:
                hands.extend(self._expand_hand(f"{r}{r}"))
        
        elif len(base) == 3:
            # Suited/Offsuit+: ATs+ means ATs, AJs, AQs, AKs
            high_rank = base[0]
            start_rank = RANK_VALUES[base[1]]
            suitedness = base[2]
            
            for r in RANKS[start_rank:RANK_VALUES[high_rank]]:
                hands.extend(self._expand_hand(f"{high_rank}{r}{suitedness}"))
        
        return hands


# Precomputed preflop equities for common hands (vs 1 random opponent)
PREFLOP_EQUITIES = {
    "AA": 0.852, "KK": 0.824, "QQ": 0.799, "JJ": 0.775, "TT": 0.750,
    "99": 0.720, "88": 0.691, "77": 0.662, "66": 0.633, "55": 0.604,
    "44": 0.575, "33": 0.546, "22": 0.518,
    "AKs": 0.670, "AQs": 0.660, "AJs": 0.650, "ATs": 0.640,
    "AKo": 0.653, "AQo": 0.643, "AJo": 0.633, "ATo": 0.623,
    "KQs": 0.634, "KJs": 0.624, "KTs": 0.615,
    "KQo": 0.615, "KJo": 0.605, "KTo": 0.595,
    "QJs": 0.603, "QTs": 0.593, "JTs": 0.582,
    "QJo": 0.583, "QTo": 0.573, "JTo": 0.562,
}
