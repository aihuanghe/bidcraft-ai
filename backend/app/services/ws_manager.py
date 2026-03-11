"""WebSocket连接管理器"""
import asyncio
import json
from typing import Dict, Set, Optional, Callable, Any
from fastapi import WebSocket
from datetime import datetime


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # task_id -> set of websockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, task_id: str, websocket: WebSocket):
        """客户端连接"""
        await websocket.accept()
        
        if task_id not in self.active_connections:
            self.active_connections[task_id] = set()
        
        self.active_connections[task_id].add(websocket)
    
    def disconnect(self, task_id: str, websocket: WebSocket):
        """客户端断开"""
        if task_id in self.active_connections:
            self.active_connections[task_id].discard(websocket)
            
            # 清理空连接
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]
    
    async def send_progress(self, task_id: str, progress: int, message: str, data: Optional[Dict] = None):
        """发送进度更新"""
        if task_id not in self.active_connections:
            return
        
        message_data = {
            "type": "progress",
            "task_id": task_id,
            "progress": progress,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if data:
            message_data["data"] = data
        
        # 发送消息
        disconnected = set()
        
        for websocket in self.active_connections[task_id]:
            try:
                await websocket.send_json(message_data)
            except Exception as e:
                print(f"发送WebSocket消息失败: {e}")
                disconnected.add(websocket)
        
        # 清理断开的连接
        for ws in disconnected:
            self.disconnect(task_id, ws)
    
    async def send_complete(self, task_id: str, result: Dict[str, Any]):
        """发送完成消息"""
        if task_id not in self.active_connections:
            return
        
        message_data = {
            "type": "complete",
            "task_id": task_id,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        disconnected = set()
        
        for websocket in self.active_connections[task_id]:
            try:
                await websocket.send_json(message_data)
            except Exception as e:
                disconnected.add(websocket)
        
        for ws in disconnected:
            self.disconnect(task_id, ws)
    
    async def send_error(self, task_id: str, error: str):
        """发送错误消息"""
        if task_id not in self.active_connections:
            return
        
        message_data = {
            "type": "error",
            "task_id": task_id,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        disconnected = set()
        
        for websocket in self.active_connections[task_id]:
            try:
                await websocket.send_json(message_data)
            except Exception as e:
                disconnected.add(websocket)
        
        for ws in disconnected:
            self.disconnect(task_id, ws)
    
    async def broadcast(self, task_id: str, message: Dict[str, Any]):
        """广播消息"""
        if task_id not in self.active_connections:
            return
        
        disconnected = set()
        
        for websocket in self.active_connections[task_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                disconnected.add(websocket)
        
        for ws in disconnected:
            self.disconnect(task_id, ws)
    
    def get_connection_count(self, task_id: str) -> int:
        """获取连接数"""
        return len(self.active_connections.get(task_id, set()))


# 全局单例
ws_manager = ConnectionManager()
