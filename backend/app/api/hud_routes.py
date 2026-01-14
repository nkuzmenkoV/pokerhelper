"""
API routes for HUD statistics and equity calculator.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.poker.hud_tracker import HUDTracker
from app.poker.equity_calculator import EquityCalculator, EquityResult

router = APIRouter()

# Global instances (in production, use dependency injection)
hud_tracker = HUDTracker()
equity_calculator = EquityCalculator()


# ============ Request/Response Models ============

class PlayerAction(BaseModel):
    """Single player action."""
    player_id: str
    action: str  # fold, check, call, bet, raise, allin
    street: str  # preflop, flop, turn, river
    amount: float = 0
    facing_bet: float = 0


class NewHandRequest(BaseModel):
    """Request to start tracking a new hand."""
    hand_id: str
    players: list[dict]  # [{id, name, position, stack}, ...]


class ShowdownResult(BaseModel):
    """Showdown result for a player."""
    player_id: str
    won: bool


class EquityRequest(BaseModel):
    """Request for equity calculation."""
    hero_cards: list[str]  # ["As", "Kh"]
    board: list[str] = []  # ["Qd", "Jc", "Ts"]
    villain_range: Optional[str] = None  # "AA,KK,QQ,AKs"
    num_villains: int = 1
    num_simulations: int = 10000


class EquityResponse(BaseModel):
    """Equity calculation response."""
    equity: float
    win_pct: float
    tie_pct: float
    lose_pct: float
    simulations: int
    time_ms: float


# ============ HUD Routes ============

@router.post("/hud/hand/start")
async def start_hand(request: NewHandRequest):
    """Start tracking a new hand."""
    hud_tracker.start_new_hand(request.hand_id, request.players)
    return {"status": "started", "hand_id": request.hand_id}


@router.post("/hud/action")
async def record_action(action: PlayerAction):
    """Record a player action."""
    hud_tracker.record_action(
        player_id=action.player_id,
        action=action.action,
        street=action.street,
        amount=action.amount,
        facing_bet=action.facing_bet,
    )
    return {"status": "recorded"}


@router.post("/hud/showdown")
async def record_showdown(result: ShowdownResult):
    """Record showdown result."""
    hud_tracker.record_showdown(result.player_id, result.won)
    return {"status": "recorded"}


@router.post("/hud/hand/end")
async def end_hand():
    """End the current hand."""
    hud_tracker.end_hand()
    return {"status": "ended"}


@router.get("/hud/stats/{player_id}")
async def get_player_stats(player_id: str):
    """Get statistics for a specific player."""
    stats = hud_tracker.get_player_stats(player_id)
    if stats is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return stats


@router.get("/hud/stats")
async def get_all_stats():
    """Get statistics for all tracked players."""
    return hud_tracker.get_all_stats()


@router.get("/hud/display/{player_id}")
async def get_hud_display(player_id: str):
    """Get HUD display string for a player."""
    display = hud_tracker.get_hud_display(player_id)
    if display is None:
        return {"display": "No data"}
    return {"display": display, "type": hud_tracker.get_player_type(player_id)}


@router.get("/hud/export")
async def export_stats():
    """Export all player statistics."""
    return hud_tracker.export_stats()


# ============ Equity Routes ============

@router.post("/equity/calculate", response_model=EquityResponse)
async def calculate_equity(request: EquityRequest):
    """Calculate equity for given hand."""
    if len(request.hero_cards) != 2:
        raise HTTPException(status_code=400, detail="Hero must have exactly 2 cards")
    
    if len(request.board) > 5:
        raise HTTPException(status_code=400, detail="Board cannot have more than 5 cards")
    
    if request.villain_range:
        result = equity_calculator.equity_vs_range(
            hero_cards=request.hero_cards,
            villain_range_str=request.villain_range,
            board=request.board if request.board else None,
            num_simulations=min(request.num_simulations, 50000),
        )
    else:
        result = equity_calculator.calculate_equity(
            hero_cards=request.hero_cards,
            board=request.board if request.board else None,
            num_simulations=min(request.num_simulations, 50000),
            num_villains=request.num_villains,
        )
    
    return EquityResponse(
        equity=result.equity,
        win_pct=result.win_pct,
        tie_pct=result.tie_pct,
        lose_pct=result.lose_pct,
        simulations=result.simulations,
        time_ms=result.time_ms,
    )


@router.get("/equity/preflop/{hand}")
async def get_preflop_equity(hand: str, num_villains: int = 1):
    """
    Get preflop equity for a hand notation.
    
    Examples: AA, AKs, AKo, QJs
    """
    # Parse hand notation to actual cards
    if len(hand) == 2:
        # Pocket pair: "AA" -> ["As", "Ah"]
        r = hand[0]
        cards = [f"{r}s", f"{r}h"]
    elif len(hand) == 3:
        r1, r2, suit = hand[0], hand[1], hand[2]
        if suit == 's':
            cards = [f"{r1}s", f"{r2}s"]  # Suited
        else:
            cards = [f"{r1}s", f"{r2}h"]  # Offsuit
    else:
        raise HTTPException(status_code=400, detail="Invalid hand notation")
    
    result = equity_calculator.preflop_equity(
        hero_cards=cards,
        num_villains=num_villains,
        num_simulations=10000,
    )
    
    return {
        "hand": hand,
        "cards": cards,
        "equity": round(result.equity * 100, 1),
        "vs_villains": num_villains,
    }
