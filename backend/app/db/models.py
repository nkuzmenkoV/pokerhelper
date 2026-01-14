"""
SQLAlchemy models for GTO charts and game data.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class PreflopRange(Base):
    """Preflop opening/calling/3betting ranges."""
    __tablename__ = "preflop_ranges"
    
    id = Column(Integer, primary_key=True)
    
    # Context
    position = Column(String(10), nullable=False, index=True)  # UTG, MP, CO, BTN, SB, BB
    action_facing = Column(String(20), nullable=False)  # open, vs_raise, vs_3bet, vs_4bet
    table_format = Column(String(10), default="6max")  # 6max, 9max, headsup
    
    # Stack depth ranges
    stack_bb_min = Column(Integer, default=0)
    stack_bb_max = Column(Integer, default=1000)
    
    # Hand and action
    hand = Column(String(4), nullable=False, index=True)  # AKs, AKo, AA, etc.
    action = Column(String(10), nullable=False)  # fold, call, raise, allin
    frequency = Column(Float, default=1.0)  # 0.0 - 1.0
    
    # Sizing (for raises)
    raise_size = Column(Float, nullable=True)  # In BB or multiplier
    
    # Metadata
    source = Column(String(50))  # PioSolver, GTO+, Custom
    created_at = Column(DateTime, default=datetime.utcnow)
    

class PostflopLine(Base):
    """Postflop action lines for specific spots."""
    __tablename__ = "postflop_lines"
    
    id = Column(Integer, primary_key=True)
    
    # Board texture
    board = Column(String(15))  # e.g., "AsKd7h", "QsJsTs"
    board_texture = Column(String(20))  # dry, wet, paired, etc.
    
    # Position and action
    hero_position = Column(String(10), nullable=False)
    villain_position = Column(String(10), nullable=False)
    street = Column(String(10), nullable=False)  # flop, turn, river
    
    # Action sequence leading to this spot
    action_sequence = Column(Text)  # e.g., "raise-call|bet-call|check-bet"
    
    # Recommended action
    hand_category = Column(String(30))  # e.g., "top_pair", "flush_draw", "air"
    action = Column(String(10), nullable=False)
    frequency = Column(Float, default=1.0)
    sizing = Column(Float, nullable=True)  # As fraction of pot
    
    source = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)


class PushFoldChart(Base):
    """Push/fold charts for short stack play."""
    __tablename__ = "push_fold_charts"
    
    id = Column(Integer, primary_key=True)
    
    # Context
    position = Column(String(10), nullable=False, index=True)
    action_type = Column(String(10), nullable=False)  # push, call
    num_players = Column(Integer, default=6)
    
    # Stack depth
    stack_bb = Column(Float, nullable=False)
    
    # Ante/blind structure
    ante_pct = Column(Float, default=0)  # Ante as % of BB
    
    # Hand and decision
    hand = Column(String(4), nullable=False)
    decision = Column(Boolean, nullable=False)  # True = push/call, False = fold
    
    # ICM adjustment
    icm_adjusted = Column(Boolean, default=False)
    bubble_factor = Column(Float, default=1.0)
    
    source = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)


class HandHistory(Base):
    """Stored hand histories for analysis."""
    __tablename__ = "hand_histories"
    
    id = Column(Integer, primary_key=True)
    
    # Hand identifiers
    hand_id = Column(String(50), unique=True)
    tournament_id = Column(String(50), nullable=True)
    
    # Game info
    table_format = Column(String(10))
    blinds = Column(String(20))  # e.g., "100/200/25"
    
    # Hand data (JSON)
    hero_cards = Column(String(10))
    board = Column(String(15))
    
    # Players and actions (JSON array)
    players = Column(JSON)
    actions = Column(JSON)
    
    # Result
    pot_won = Column(Float, nullable=True)
    showdown = Column(Boolean, default=False)
    
    # Analysis
    recommended_action = Column(String(50), nullable=True)
    actual_action = Column(String(50), nullable=True)
    ev_difference = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class CalibrationProfile(Base):
    """Screen calibration profiles for different setups."""
    __tablename__ = "calibration_profiles"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    
    # Screen resolution
    screen_width = Column(Integer, nullable=False)
    screen_height = Column(Integer, nullable=False)
    
    # Table region
    table_x = Column(Integer)
    table_y = Column(Integer)
    table_width = Column(Integer)
    table_height = Column(Integer)
    
    # Player regions (JSON)
    player_regions = Column(JSON)  # Array of {seat, x, y, width, height}
    
    # Other regions
    pot_region = Column(JSON)
    board_region = Column(JSON)
    hero_cards_region = Column(JSON)
    
    # Client theme/skin
    client_theme = Column(String(50))
    
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
