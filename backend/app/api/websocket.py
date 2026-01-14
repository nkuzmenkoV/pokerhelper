from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json
import base64
import asyncio

from app.cv.processor import CVProcessor
from app.poker.game_state import GameState
from app.poker.gto_engine import GTOEngine

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.cv_processor = CVProcessor()
        self.gto_engine = GTOEngine()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_recommendation(self, websocket: WebSocket, data: dict):
        await websocket.send_json(data)
    
    async def process_frame(self, frame_data: bytes) -> dict:
        """Process a captured frame and return recommendations."""
        # Decode and process the frame
        game_state = await self.cv_processor.process_frame(frame_data)
        
        if game_state is None:
            return {"status": "no_table_detected"}
        
        # Get GTO recommendations
        recommendations = self.gto_engine.get_recommendations(game_state)
        
        return {
            "status": "success",
            "game_state": game_state.to_dict(),
            "recommendations": recommendations,
        }


manager = ConnectionManager()


@router.websocket("/analyze")
async def websocket_analyze(websocket: WebSocket):
    """WebSocket endpoint for real-time frame analysis."""
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive frame data (base64 encoded JPEG)
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "frame":
                # Decode base64 image
                frame_data = base64.b64decode(message["data"])
                
                # Process frame and get recommendations
                result = await manager.process_frame(frame_data)
                
                # Send back recommendations
                await manager.send_recommendation(websocket, result)
            
            elif message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)
