"""
Chart loading and management utilities.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import PreflopRange, PushFoldChart


async def get_preflop_range(
    session: AsyncSession,
    position: str,
    action_facing: str,
    stack_bb: float,
    table_format: str = "6max",
) -> list[dict]:
    """
    Get preflop range for given spot.
    
    Returns list of hands with their actions and frequencies.
    """
    query = select(PreflopRange).where(
        PreflopRange.position == position,
        PreflopRange.action_facing == action_facing,
        PreflopRange.table_format == table_format,
        PreflopRange.stack_bb_min <= stack_bb,
        PreflopRange.stack_bb_max >= stack_bb,
    )
    
    result = await session.execute(query)
    ranges = result.scalars().all()
    
    return [
        {
            "hand": r.hand,
            "action": r.action,
            "frequency": r.frequency,
            "raise_size": r.raise_size,
        }
        for r in ranges
    ]


async def get_hand_action(
    session: AsyncSession,
    hand: str,
    position: str,
    action_facing: str,
    stack_bb: float,
    table_format: str = "6max",
) -> Optional[dict]:
    """
    Get recommended action for specific hand in given spot.
    """
    query = select(PreflopRange).where(
        PreflopRange.hand == hand,
        PreflopRange.position == position,
        PreflopRange.action_facing == action_facing,
        PreflopRange.table_format == table_format,
        PreflopRange.stack_bb_min <= stack_bb,
        PreflopRange.stack_bb_max >= stack_bb,
    )
    
    result = await session.execute(query)
    range_entry = result.scalar_one_or_none()
    
    if range_entry:
        return {
            "action": range_entry.action,
            "frequency": range_entry.frequency,
            "raise_size": range_entry.raise_size,
        }
    
    return None


def generate_default_ranges() -> list[dict]:
    """
    Generate default opening ranges for seeding the database.
    
    Based on standard TAG (Tight-Aggressive) strategy.
    """
    ranges = []
    
    # All possible hands
    ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
    
    # Generate all hand combinations
    hands = []
    for i, r1 in enumerate(ranks):
        for j, r2 in enumerate(ranks):
            if i == j:
                hands.append(f"{r1}{r2}")  # Pocket pair
            elif i < j:
                hands.append(f"{r1}{r2}s")  # Suited
                hands.append(f"{r1}{r2}o")  # Offsuit
    
    # Define opening ranges by position
    position_ranges = {
        "UTG": {
            "raise": ["AA", "KK", "QQ", "JJ", "TT", "99", "88",
                     "AKs", "AQs", "AJs", "ATs", "KQs",
                     "AKo", "AQo"],
        },
        "MP": {
            "raise": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77",
                     "AKs", "AQs", "AJs", "ATs", "A9s", "KQs", "KJs", "QJs",
                     "AKo", "AQo", "AJo"],
        },
        "CO": {
            "raise": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66",
                     "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s",
                     "KQs", "KJs", "KTs", "QJs", "QTs", "JTs",
                     "AKo", "AQo", "AJo", "ATo", "KQo", "KJo"],
        },
        "BTN": {
            "raise": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44",
                     "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
                     "KQs", "KJs", "KTs", "K9s", "K8s",
                     "QJs", "QTs", "Q9s",
                     "JTs", "J9s",
                     "T9s", "T8s",
                     "98s", "97s",
                     "87s", "76s", "65s", "54s",
                     "AKo", "AQo", "AJo", "ATo", "A9o",
                     "KQo", "KJo", "KTo",
                     "QJo", "QTo",
                     "JTo"],
        },
        "SB": {
            "raise": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55",
                     "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s",
                     "KQs", "KJs", "KTs", "K9s",
                     "QJs", "QTs",
                     "JTs", "J9s",
                     "T9s",
                     "98s", "87s", "76s",
                     "AKo", "AQo", "AJo", "ATo",
                     "KQo", "KJo",
                     "QJo"],
        },
    }
    
    for position, actions in position_ranges.items():
        for action, hand_list in actions.items():
            for hand in hand_list:
                ranges.append({
                    "position": position,
                    "action_facing": "open",
                    "table_format": "6max",
                    "stack_bb_min": 20,
                    "stack_bb_max": 1000,
                    "hand": hand,
                    "action": action,
                    "frequency": 1.0,
                    "raise_size": 2.5 if position in ["BTN", "SB"] else 3.0,
                    "source": "default",
                })
    
    return ranges


async def seed_default_ranges(session: AsyncSession):
    """Seed database with default ranges."""
    ranges = generate_default_ranges()
    
    for range_data in ranges:
        entry = PreflopRange(**range_data)
        session.add(entry)
    
    await session.commit()
