"""解析任务服务"""
import os
import json
import asyncio
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
import uuid

from ..config import settings
from .word_parser_service import WordParseService


class ParseStatus(Enum):
    """解析状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ParseTask:
    """解析任务"""
    task_id: str
    file_path: str
    file_name: str
    file_size: int
    status: ParseStatus = ParseStatus.PENDING
    progress: int = 0
    message: str = ""
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "status": self.status.value,
            "progress": self.progress,
            "message": self.message,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class ParseTaskService:
    """解析任务服务"""
    
    # 任务存储目录
    TASK_DIR = os.path.join(settings.upload_dir, "tasks")
    
    # 缓存相关
    CACHE_TTL_DAYS = 7
    
    def __init__(self):
        os.makedirs(self.TASK_DIR, exist_ok=True)
    
    def _get_task_file(self, task_id: str) -> str:
        """获取任务文件路径"""
        return os.path.join(self.TASK_DIR, f"{task_id}.json")
    
    def _get_cache_file(self, file_hash: str) -> str:
        """获取缓存文件路径"""
        return os.path.join(self.TASK_DIR, "cache", f"{file_hash}.json")
    
    async def create_task(
        self,
        file_path: str,
        file_name: str,
        file_size: int
    ) -> ParseTask:
        """创建解析任务"""
        task_id = str(uuid.uuid4())
        
        task = ParseTask(
            task_id=task_id,
            file_path=file_path,
            file_name=file_name,
            file_size=file_size
        )
        
        # 保存任务
        await self._save_task(task)
        
        return task
    
    async def _save_task(self, task: ParseTask):
        """保存任务到文件"""
        task_file = self._get_task_file(task.task_id)
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(task.to_dict(), f, ensure_ascii=False, indent=2)
    
    async def get_task(self, task_id: str) -> Optional[ParseTask]:
        """获取任务"""
        task_file = self._get_task_file(task_id)
        if not os.path.exists(task_file):
            return None
        
        with open(task_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        task = ParseTask(
            task_id=data["task_id"],
            file_path=data["file_path"],
            file_name=data["file_name"],
            file_size=data["file_size"],
            status=ParseStatus(data["status"]),
            progress=data["progress"],
            message=data["message"],
            result=data.get("result"),
            error=data.get("error"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
        )
        
        return task
    
    async def update_progress(
        self,
        task_id: str,
        progress: int,
        message: str
    ):
        """更新任务进度"""
        task = await self.get_task(task_id)
        if task:
            task.progress = progress
            task.message = message
            task.status = ParseStatus.PROCESSING
            task.updated_at = datetime.utcnow()
            await self._save_task(task)
    
    async def complete_task(
        self,
        task_id: str,
        result: Dict[str, Any]
    ):
        """完成任务"""
        task = await self.get_task(task_id)
        if task:
            task.status = ParseStatus.COMPLETED
            task.progress = 100
            task.message = "解析完成"
            task.result = result
            task.completed_at = datetime.utcnow()
            task.updated_at = datetime.utcnow()
            await self._save_task(task)
            
            # 缓存结果
            await self._cache_result(task.file_path, result)
    
    async def fail_task(self, task_id: str, error: str):
        """任务失败"""
        task = await self.get_task(task_id)
        if task:
            task.status = ParseStatus.FAILED
            task.error = error
            task.updated_at = datetime.utcnow()
            await self._save_task(task)
    
    async def _cache_result(self, file_path: str, result: Dict[str, Any]):
        """缓存解析结果"""
        try:
            # 计算文件hash
            file_hash = self._calculate_file_hash(file_path)
            
            # 保存到缓存
            cache_dir = os.path.join(self.TASK_DIR, "cache")
            os.makedirs(cache_dir, exist_ok=True)
            
            cache_file = self._get_cache_file(file_hash)
            cache_data = {
                "file_hash": file_hash,
                "file_path": file_path,
                "result": result,
                "cached_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(days=self.CACHE_TTL_DAYS)).isoformat()
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"缓存解析结果失败: {e}")
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件hash"""
        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    async def get_cached_result(self, file_path: str) -> Optional[Dict[str, Any]]:
        """获取缓存的解析结果"""
        try:
            file_hash = self._calculate_file_hash(file_path)
            cache_file = self._get_cache_file(file_hash)
            
            if not os.path.exists(cache_file):
                return None
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # 检查是否过期
            expires_at = datetime.fromisoformat(cache_data["expires_at"])
            if datetime.utcnow() > expires_at:
                # 过期，删除
                os.remove(cache_file)
                return None
            
            return cache_data["result"]
            
        except Exception as e:
            print(f"获取缓存失败: {e}")
            return None
    
    async def execute_parse(
        self,
        task_id: str,
        progress_callback: Optional[callable] = None
    ):
        """执行解析任务"""
        task = await self.get_task(task_id)
        if not task:
            return
        
        # 检查缓存
        cached_result = await self.get_cached_result(task.file_path)
        if cached_result:
            await self.complete_task(task_id, cached_result)
            if progress_callback:
                await progress_callback(100, "从缓存加载")
            return
        
        # 执行解析
        try:
            task.status = ParseStatus.PROCESSING
            task.updated_at = datetime.utcnow()
            await self._save_task(task)
            
            # 定义进度回调
            async def on_progress(progress: int, message: str):
                await self.update_progress(task_id, progress, message)
                if progress_callback:
                    await progress_callback(progress, message)
            
            # 解析Word文档
            result = await WordParseService.parse_word_full(
                task.file_path,
                progress_callback=on_progress
            )
            
            # 完成
            await self.complete_task(task_id, result)
            
        except Exception as e:
            await self.fail_task(task_id, str(e))
            if progress_callback:
                await progress_callback(-1, f"解析失败: {str(e)}")
    
    async def list_tasks(self, limit: int = 100) -> List[ParseTask]:
        """列出所有任务"""
        tasks = []
        if not os.path.exists(self.TASK_DIR):
            return tasks
        
        for filename in os.listdir(self.TASK_DIR):
            if filename.endswith('.json') and filename != 'cache':
                task_id = filename[:-5]
                task = await self.get_task(task_id)
                if task:
                    tasks.append(task)
        
        # 按创建时间排序
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return tasks[:limit]


# 全局单例
parse_task_service = ParseTaskService()
