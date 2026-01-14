"""
Database models for player statistics storage.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Index
from sqlalchemy.sql import func
from datetime import datetime

from app.db.models import Base


class PlayerStatistics(Base):
    """Stored player statistics."""
    __tablename__ = "player_statistics"
    
    id = Column(Integer, primary_key=True)
    
    # Player identification
    player_id = Column(String(100), nullable=False, index=True)
    player_name = Column(String(100), nullable=False)
    
    # Platform/room info
    room = Column(String(50), default="pokerok")
    
    # Basic stats
    total_hands = Column(Integer, default=0)
    vpip_hands = Column(Integer, default=0)
    pfr_hands = Column(Integer, default=0)
    
    # 3-bet stats
    three_bet_opportunities = Column(Integer, default=0)
    three_bet_count = Column(Integer, default=0)
    faced_three_bet = Column(Integer, default=0)
    folded_to_three_bet = Column(Integer, default=0)
    
    # C-bet stats
    cbet_opportunities = Column(Integer, default=0)
    cbet_count = Column(Integer, default=0)
    
    # Aggression stats
    bets_and_raises = Column(Integer, default=0)
    calls = Column(Integer, default=0)
    
    # Showdown stats
    went_to_showdown = Column(Integer, default=0)
    won_at_showdown = Column(Integer, default=0)
    
    # Position breakdown (JSON)
    position_stats = Column(JSON, default=dict)
    
    # Timestamps
    first_seen = Column(DateTime, default=func.now())
    last_seen = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Create composite index for player lookup
    __table_args__ = (
        Index('idx_player_room', 'player_id', 'room'),
    )
    
    @property
    def vpip_pct(self) -> float:
        if self.total_hands == 0:
            return 0.0
        return (self.vpip_hands / self.total_hands) * 100
    
    @property
    def pfr_pct(self) -> float:
        if self.total_hands == 0:
            return 0.0
        return (self.pfr_hands / self.total_hands) * 100
    
    @property
    def three_bet_pct(self) -> float:
        if self.three_bet_opportunities == 0:
            return 0.0
        return (self.three_bet_count / self.three_bet_opportunities) * 100
    
    @property
    def aggression_factor(self) -> float:
        if self.calls == 0:
            return 0.0
        return self.bets_and_raises / self.calls
    
    def to_dict(self) -> dict:
        return {
            "player_id": self.player_id,
            "player_name": self.player_name,
            "hands": self.total_hands,
            "vpip": round(self.vpip_pct, 1),
            "pfr": round(self.pfr_pct, 1),
            "three_bet": round(self.three_bet_pct, 1),
            "af": round(self.aggression_factor, 1),
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
        }


class HandHistoryRecord(Base):
    """Individual hand history records for detailed analysis."""
    __tablename__ = "hand_history_records"
    
    id = Column(Integer, primary_key=True)
    hand_id = Column(String(50), nullable=False, unique=True, index=True)
    
    # Game context
    room = Column(String(50), default="pokerok")
    game_type = Column(String(20))  # NLH, PLO, etc.
    stakes = Column(String(20))  # e.g., "100/200"
    table_size = Column(Integer)  # 2, 6, 9
    
    # Hand data (JSON)
    players = Column(JSON)  # List of player states
    hero_cards = Column(String(10))
    board = Column(String(20))
    actions = Column(JSON)  # List of actions per street
    
    # Results
    pot_size = Column(Float)
    winner_id = Column(String(100))
    
    # Timestamp
    played_at = Column(DateTime, default=func.now())
