"""WebSocket support for real-time progress updates"""
import json
import logging
from typing import Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for progress updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.search_status: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, search_id: str):
        """Connect a WebSocket for a specific search"""
        await websocket.accept()
        self.active_connections[search_id] = websocket
        
        # Initialize status
        self.search_status[search_id] = {
            "search_id": search_id,
            "status": "connecting",
            "progress": 0,
            "platforms_completed": [],
            "platforms_remaining": [],
            "total_platforms": 0,
            "results_found": 0,
            "started_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        await self.send_status(search_id)
        logger.info(f"WebSocket connected for search: {search_id}")
    
    def disconnect(self, search_id: str):
        """Disconnect a WebSocket"""
        if search_id in self.active_connections:
            del self.active_connections[search_id]
        logger.info(f"WebSocket disconnected for search: {search_id}")
    
    async def send_status(self, search_id: str):
        """Send current status to client"""
        if search_id in self.active_connections:
            websocket = self.active_connections[search_id]
            status = self.search_status.get(search_id, {})
            
            try:
                await websocket.send_json(status)
            except Exception as e:
                logger.error(f"Error sending status to {search_id}: {e}")
                self.disconnect(search_id)
    
    async def update_progress(
        self,
        search_id: str,
        progress: float,
        platform: Optional[str] = None,
        status: Optional[str] = None
    ):
        """Update search progress"""
        if search_id not in self.search_status:
            return
        
        status_data = self.search_status[search_id]
        
        if progress is not None:
            status_data["progress"] = min(100, max(0, progress))
        
        if platform is not None:
            if platform not in status_data["platforms_completed"]:
                status_data["platforms_completed"].append(platform)
            status_data["results_found"] += 1
        
        if status is not None:
            status_data["status"] = status
        
        status_data["updated_at"] = datetime.utcnow().isoformat()
        
        await self.send_status(search_id)
    
    async def complete_search(
        self,
        search_id: str,
        total_results: int,
        execution_time_ms: float
    ):
        """Mark search as completed"""
        if search_id not in self.search_status:
            return
        
        status_data = self.search_status[search_id]
        status_data["status"] = "completed"
        status_data["progress"] = 100
        status_data["results_found"] = total_results
        status_data["execution_time_ms"] = execution_time_ms
        status_data["completed_at"] = datetime.utcnow().isoformat()
        status_data["updated_at"] = datetime.utcnow().isoformat()
        
        await self.send_status(search_id)
    
    async def fail_search(
        self,
        search_id: str,
        error: str
    ):
        """Mark search as failed"""
        if search_id not in self.search_status:
            return
        
        status_data = self.search_status[search_id]
        status_data["status"] = "failed"
        status_data["error"] = error
        status_data["updated_at"] = datetime.utcnow().isoformat()
        
        await self.send_status(search_id)
    
    def get_status(self, search_id: str) -> Optional[Dict[str, Any]]:
        """Get current status for a search"""
        return self.search_status.get(search_id)


# Global connection manager instance
manager = ConnectionManager()


class ProgressTracker:
    """Tracks progress of long-running searches"""
    
    def __init__(self, search_id: str, total_platforms: int):
        self.search_id = search_id
        self.total_platforms = total_platforms
        self.completed_platforms = 0
        self.results_found = 0
        self.start_time = datetime.utcnow()
    
    async def start(self):
        """Start tracking progress"""
        await manager.update_progress(
            self.search_id,
            progress=0,
            status="running"
        )
        await manager.update_progress(
            self.search_id,
            progress=0,
            status="running"
        )
    
    async def update_platform_progress(self, platform: str, results: int):
        """Update progress after completing a platform"""
        self.completed_platforms += 1
        self.results_found += results
        
        progress = (self.completed_platforms / self.total_platforms) * 100
        
        await manager.update_progress(
            self.search_id,
            progress=progress,
            platform=platform
        )
    
    async def complete(self, total_results: int):
        """Mark tracking as complete"""
        execution_time_ms = int(
            (datetime.utcnow() - self.start_time).total_seconds() * 1000
        )
        
        await manager.complete_search(
            self.search_id,
            total_results,
            execution_time_ms
        )
    
    async def fail(self, error: str):
        """Mark tracking as failed"""
        await manager.fail_search(self.search_id, error)


async def handle_websocket_connection(
    websocket: WebSocket,
    search_id: str
):
    """Handle WebSocket connection for a search"""
    await manager.connect(websocket, search_id)
    
    try:
        # Keep connection alive and handle any client messages
        while True:
            data = await websocket.receive_text()
            
            # Handle client messages (if any)
            try:
                message = json.loads(data)
                
                # Client can request status update
                if message.get("action") == "get_status":
                    await manager.send_status(search_id)
                
                # Client can cancel search
                elif message.get("action") == "cancel":
                    await manager.fail_search(search_id, "Cancelled by user")
                    break
                
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from {search_id}")
                continue
    
    except WebSocketDisconnect:
        manager.disconnect(search_id)
    except Exception as e:
        logger.error(f"WebSocket error for {search_id}: {e}")
        manager.disconnect(search_id)


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager"""
    return manager
