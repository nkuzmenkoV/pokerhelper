"""
Chart loading and management utilities.
Loads GTO charts from JSON files and provides lookup functions.
"""

import json
from pathlib import Path
from typing import Optional
from functools import lru_cache


# Path to chart data
CHARTS_DIR = Path(__file__).parent.parent.parent / "data" / "gto_charts"


@lru_cache(maxsize=4)
def load_chart(chart_name: str) -> dict:
    """Load a chart from JSON file with caching."""
    chart_path = CHARTS_DIR / f"{chart_name}.json"
    if not chart_path.exists():
        return {}
    
    with open(chart_path, "r") as f:
        return json.load(f)


def get_push_fold_range(
    position: str,
    stack_bb: int,
    table_format: str = "9max"
) -> list[str]:
    """
    Get push range for given position and stack.
    
    Args:
        position: Player position (UTG, HJ, CO, BTN, SB, etc.)
        stack_bb: Stack in big blinds (will be rounded to nearest bucket)
        table_format: "6max" or "9max"
    
    Returns:
        List of hands in the push range
    """
    chart_file = f"push_fold_{table_format}"
    chart = load_chart(chart_file)
    
    if not chart:
        return []
    
    ranges = chart.get("ranges", {})
    position_ranges = ranges.get(position, {})
    
    # Find nearest stack bucket
    stack_key = _get_stack_key(stack_bb, position_ranges)
    
    if not stack_key:
        return []
    
    range_data = position_ranges.get(stack_key, [])
    
    # Handle "any" case (push any hand)
    if range_data == "any":
        return ["any"]
    
    return range_data


def get_call_range(
    position: str,
    stack_bb: int,
    table_format: str = "9max",
    vs_position: str = "SB"
) -> list[str]:
    """
    Get calling range vs all-in.
    
    Args:
        position: Hero's position (typically BB)
        stack_bb: Effective stack
        table_format: "6max" or "9max"
        vs_position: Villain's position
    
    Returns:
        List of hands in the call range
    """
    chart_file = f"push_fold_{table_format}"
    chart = load_chart(chart_file)
    
    if not chart:
        return []
    
    call_ranges = chart.get("call_ranges", {})
    range_key = f"{position}_vs_{vs_position}"
    position_ranges = call_ranges.get(range_key, {})
    
    stack_key = _get_stack_key(stack_bb, position_ranges)
    
    if not stack_key:
        return []
    
    return position_ranges.get(stack_key, [])


def get_opening_range(
    position: str,
    table_format: str = "9max"
) -> dict:
    """
    Get opening range for position.
    
    Returns:
        Dict with 'raise' list and 'raise_size'
    """
    chart = load_chart("opening_ranges")
    
    if not chart:
        return {"raise": [], "raise_size": 2.5}
    
    ranges = chart.get("ranges", {})
    format_ranges = ranges.get(table_format, ranges.get("9max", {}))
    position_data = format_ranges.get(position, {})
    
    return {
        "raise": position_data.get("raise", []),
        "raise_size": position_data.get("raise_size", 2.5),
        "description": position_data.get("description", "")
    }


def get_3bet_range(
    vs_position: str
) -> dict:
    """
    Get 3-bet range vs given position.
    
    Returns:
        Dict with 'value', 'bluff', and 'call' lists
    """
    chart = load_chart("3bet_ranges")
    
    if not chart:
        return {"3bet_value": [], "3bet_bluff": [], "call": []}
    
    ranges = chart.get("ranges", {})
    range_key = f"vs_{vs_position}"
    position_data = ranges.get(range_key, {})
    
    return {
        "3bet_value": position_data.get("3bet_value", []),
        "3bet_bluff": position_data.get("3bet_bluff", []),
        "call": position_data.get("call", []),
        "description": position_data.get("description", "")
    }


def is_hand_in_range(hand: str, range_list: list[str]) -> bool:
    """
    Check if a hand is in the given range.
    
    Args:
        hand: Hand notation (e.g., "AKs", "QQ", "T9o")
        range_list: List of hands in the range
    
    Returns:
        True if hand is in range
    """
    if not range_list:
        return False
    
    if "any" in range_list:
        return True
    
    # Normalize hand notation
    normalized = _normalize_hand(hand)
    
    return normalized in range_list


def _normalize_hand(hand: str) -> str:
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


def _get_stack_key(stack_bb: int, ranges: dict) -> Optional[str]:
    """Find the nearest stack bucket key."""
    # Standard buckets
    buckets = [3, 4, 5, 6, 7, 8, 10, 12, 15]
    
    # Find nearest bucket that exists in ranges
    available_keys = [k for k in ranges.keys() if k.endswith("bb")]
    
    if not available_keys:
        # Try without 'bb' suffix
        available_keys = list(ranges.keys())
    
    # Parse available stack sizes
    available_stacks = []
    for key in available_keys:
        try:
            stack = int(key.replace("bb", ""))
            available_stacks.append((stack, key))
        except ValueError:
            continue
    
    if not available_stacks:
        return None
    
    # Find nearest bucket
    available_stacks.sort(key=lambda x: x[0])
    
    for stack, key in available_stacks:
        if stack_bb <= stack:
            return key
    
    # Return largest if stack exceeds all buckets
    return available_stacks[-1][1]


def get_chart_stats() -> dict:
    """Get statistics about loaded charts."""
    stats = {
        "charts_loaded": [],
        "total_ranges": 0,
    }
    
    chart_files = ["push_fold_9max", "push_fold_6max", "opening_ranges", "3bet_ranges"]
    
    for chart_name in chart_files:
        chart = load_chart(chart_name)
        if chart:
            stats["charts_loaded"].append(chart_name)
            ranges = chart.get("ranges", {})
            stats["total_ranges"] += len(ranges)
    
    return stats


def clear_chart_cache():
    """Clear the chart loading cache."""
    load_chart.cache_clear()
