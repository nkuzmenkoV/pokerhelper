from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class CalibrationData(BaseModel):
    """Screen calibration data for ROI regions."""
    screen_width: int
    screen_height: int
    table_x: int
    table_y: int
    table_width: int
    table_height: int


class GameSettings(BaseModel):
    """Game settings for analysis."""
    table_format: str = "6max"  # 6max, 9max, headsup
    ante_enabled: bool = True
    icm_enabled: bool = True


@router.get("/status")
async def get_status():
    """Get current system status."""
    return {
        "cv_ready": True,
        "gto_ready": True,
        "models_loaded": True,
    }


@router.post("/calibrate")
async def calibrate_screen(data: CalibrationData):
    """Save screen calibration data."""
    # TODO: Save calibration to database/config
    return {"status": "calibrated", "data": data}


@router.get("/settings")
async def get_settings():
    """Get current game settings."""
    return GameSettings()


@router.post("/settings")
async def update_settings(settings: GameSettings):
    """Update game settings."""
    # TODO: Save settings
    return {"status": "updated", "settings": settings}


@router.get("/charts/{position}")
async def get_chart(position: str, stack_bb: Optional[float] = None):
    """Get preflop chart for position."""
    valid_positions = ["UTG", "UTG1", "UTG2", "MP", "MP1", "CO", "BTN", "SB", "BB"]
    if position.upper() not in valid_positions:
        raise HTTPException(status_code=400, detail=f"Invalid position: {position}")
    
    # TODO: Fetch from database
    return {
        "position": position.upper(),
        "stack_bb": stack_bb,
        "ranges": {},
    }
