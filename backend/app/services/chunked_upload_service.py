"""分片上传服务"""
import os
import uuid
import hashlib
import json
import asyncio
import aiofiles
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

from ..config import settings
from ..services.redis_service import redis_service
from ..services.minio_service import minio_service


class ChunkedUploadService:
    """分片上传服务"""
    
    CHUNK_SIZE = 5 * 1024 * 1024  # 5MB per chunk
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB max file size
    MAX_CONCURRENT_UPLOADS = 3
    EXPIRE_HOURS = 24
    MAX_RETRIES = 3
    
    # Redis key prefixes
    UPLOAD_META_PREFIX = "upload:meta:"
    UPLOAD_CHUNKS_PREFIX = "upload:chunks:"
    FILE_HASH_PREFIX = "file:hash:"
    
    @staticmethod
    def get_temp_dir(upload_id: str) -> str:
        """获取临时分片目录"""
        temp_dir = os.path.join(settings.upload_dir, "temp", upload_id)
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir
    
    @staticmethod
    async def init_upload(
        filename: str,
        file_size: int,
        content_type: str = "application/octet-stream"
    ) -> Dict[str, Any]:
        """初始化分片上传"""
        # 验证文件大小
        if file_size > ChunkedUploadService.MAX_FILE_SIZE:
            raise ValueError(f"文件大小超过限制 ({ChunkedUploadService.MAX_FILE_SIZE / 1024 / 1024}MB)")
        
        # 生成唯一上传ID
        upload_id = str(uuid.uuid4())
        
        # 计算总分片数
        total_chunks = (file_size + ChunkedUploadService.CHUNK_SIZE - 1) // ChunkedUploadService.CHUNK_SIZE
        
        # 保存上传元数据到Redis
        meta_key = f"{ChunkedUploadService.UPLOAD_META_PREFIX}{upload_id}"
        meta_data = {
            "upload_id": upload_id,
            "filename": filename,
            "file_size": file_size,
            "content_type": content_type,
            "chunk_size": ChunkedUploadService.CHUNK_SIZE,
            "total_chunks": total_chunks,
            "uploaded_chunks": [],
            "status": "init",
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=ChunkedUploadService.EXPIRE_HOURS)).isoformat()
        }
        
        await redis_service.set(meta_key, json.dumps(meta_data), ttl=ChunkedUploadService.EXPIRE_HOURS * 3600)
        
        # 初始化已上传分片集合
        chunks_key = f"{ChunkedUploadService.UPLOAD_CHUNKS_PREFIX}{upload_id}"
        await redis_service.client.delete(chunks_key) if redis_service.client else None
        
        return {
            "upload_id": upload_id,
            "chunk_size": ChunkedUploadService.CHUNK_SIZE,
            "total_chunks": total_chunks,
            "filename": filename,
            "file_size": file_size
        }
    
    @staticmethod
    async def upload_part(
        upload_id: str,
        part_number: int,
        chunk_data: bytes
    ) -> Dict[str, Any]:
        """上传分片"""
        # 获取上传元数据
        meta_key = f"{ChunkedUploadService.UPLOAD_META_PREFIX}{upload_id}"
        meta_json = await redis_service.get(meta_key)
        
        if not meta_json:
            raise ValueError("上传会话不存在或已过期")
        
        meta_data = json.loads(meta_json)
        
        if meta_data["status"] != "init" and meta_data["status"] != "uploading":
            raise ValueError(f"上传状态异常: {meta_data['status']}")
        
        # 保存分片到临时文件
        temp_dir = ChunkedUploadService.get_temp_dir(upload_id)
        chunk_path = os.path.join(temp_dir, f"part_{part_number:05d}")
        
        async with aiofiles.open(chunk_path, 'wb') as f:
            await f.write(chunk_data)
        
        # 更新已上传分片列表
        chunks_key = f"{ChunkedUploadService.UPLOAD_CHUNKS_PREFIX}{upload_id}"
        if redis_service.client:
            await redis_service.client.sadd(chunks_key, part_number)
        
        # 更新上传状态
        meta_data["status"] = "uploading"
        await redis_service.set(meta_key, json.dumps(meta_data), ttl=ChunkedUploadService.EXPIRE_HOURS * 3600)
        
        return {
            "upload_id": upload_id,
            "part_number": part_number,
            "chunk_size": len(chunk_data),
            "status": "success"
        }
    
    @staticmethod
    async def get_upload_status(upload_id: str) -> Dict[str, Any]:
        """获取上传状态"""
        meta_key = f"{ChunkedUploadService.UPLOAD_META_PREFIX}{upload_id}"
        meta_json = await redis_service.get(meta_key)
        
        if not meta_json:
            raise ValueError("上传会话不存在或已过期")
        
        meta_data = json.loads(meta_json)
        
        # 获取已上传的分片列表
        chunks_key = f"{ChunkedUploadService.UPLOAD_CHUNKS_PREFIX}{upload_id}"
        uploaded_chunks = []
        if redis_service.client:
            uploaded_chunks = list(await redis_service.client.smembers(chunks_key))
            uploaded_chunks = [int(x) for x in uploaded_chunks]
        
        meta_data["uploaded_chunks"] = uploaded_chunks
        meta_data["uploaded_count"] = len(uploaded_chunks)
        
        return meta_data
    
    @staticmethod
    async def complete_upload(upload_id: str) -> Dict[str, Any]:
        """完成分片上传"""
        # 获取上传元数据
        meta_key = f"{ChunkedUploadService.UPLOAD_META_PREFIX}{upload_id}"
        meta_json = await redis_service.get(meta_key)
        
        if not meta_json:
            raise ValueError("上传会话不存在或已过期")
        
        meta_data = json.loads(meta_json)
        
        # 检查是否所有分片都已上传
        chunks_key = f"{ChunkedUploadService.UPLOAD_CHUNKS_PREFIX}{upload_id}"
        if redis_service.client:
            uploaded_chunks = list(await redis_service.client.smembers(chunks_key))
            uploaded_chunks = sorted([int(x) for x in uploaded_chunks])
        else:
            # Redis不可用时，从文件系统读取
            temp_dir = ChunkedUploadService.get_temp_dir(upload_id)
            uploaded_chunks = []
            for f in os.listdir(temp_dir):
                if f.startswith("part_"):
                    part_num = int(f.split("_")[1])
                    uploaded_chunks.append(part_num)
            uploaded_chunks = sorted(uploaded_chunks)
        
        expected_chunks = meta_data["total_chunks"]
        
        if len(uploaded_chunks) != expected_chunks:
            raise ValueError(f"分片上传不完整: 已上传 {len(uploaded_chunks)}/{expected_chunks}")
        
        # 检查是否已存在相同文件（秒传）
        temp_dir = ChunkedUploadService.get_temp_dir(upload_id)
        merged_path = os.path.join(temp_dir, "merged_file")
        
        # 合并分片
        await ChunkedUploadService._merge_chunks(temp_dir, uploaded_chunks, merged_path)
        
        # 计算文件MD5
        file_hash = await ChunkedUploadService._calculate_md5(merged_path)
        
        # 检查秒传
        existing_file_key = f"{ChunkedUploadService.FILE_HASH_PREFIX}{file_hash}"
        existing_file_info = await redis_service.get(existing_file_key)
        
        if existing_file_info:
            # 秒传成功
            file_info = json.loads(existing_file_info)
            result = {
                "upload_id": upload_id,
                "file_url": file_info["file_url"],
                "file_size": meta_data["file_size"],
                "file_hash": file_hash,
                "skip_upload": True,
                "message": "秒传成功，文件已存在"
            }
        else:
            # 上传到MinIO
            try:
                object_name = f"documents/{datetime.now().strftime('%Y%m%d')}/{meta_data['filename']}"
                file_url = await minio_service.upload_file(
                    file_path=merged_path,
                    object_name=object_name,
                    content_type=meta_data["content_type"]
                )
                
                # 保存文件哈希用于秒传
                file_info = {
                    "file_hash": file_hash,
                    "file_url": file_url,
                    "file_size": meta_data["file_size"],
                    "filename": meta_data["filename"],
                    "created_at": datetime.utcnow().isoformat()
                }
                await redis_service.set(existing_file_key, json.dumps(file_info), ttl=None)
                
                result = {
                    "upload_id": upload_id,
                    "file_url": file_url,
                    "file_size": meta_data["file_size"],
                    "file_hash": file_hash,
                    "skip_upload": False,
                    "message": "文件上传成功"
                }
            except Exception as e:
                # MinIO上传失败，使用本地文件
                result = {
                    "upload_id": upload_id,
                    "file_url": merged_path,
                    "file_size": meta_data["file_size"],
                    "file_hash": file_hash,
                    "skip_upload": False,
                    "message": f"文件上传成功（本地存储）: {str(e)}"
                }
        
        # 更新上传状态
        meta_data["status"] = "completed"
        meta_data["completed_at"] = datetime.utcnow().isoformat()
        await redis_service.set(meta_key, json.dumps(meta_data), ttl=3600)  # 保留1小时
        
        # 清理临时分片文件
        await ChunkedUploadService._cleanup_chunks(temp_dir, uploaded_chunks)
        
        return result
    
    @staticmethod
    async def _merge_chunks(temp_dir: str, chunks: List[int], output_path: str):
        """合并分片文件"""
        async with aiofiles.open(output_path, 'wb') as out_file:
            for part_num in chunks:
                chunk_path = os.path.join(temp_dir, f"part_{part_num:05d}")
                async with aiofiles.open(chunk_path, 'rb') as in_file:
                    await out_file.write(await in_file.read())
    
    @staticmethod
    async def _calculate_md5(file_path: str) -> str:
        """计算文件MD5"""
        md5_hash = hashlib.md5()
        async with aiofiles.open(file_path, 'rb') as f:
            while True:
                chunk = await f.read(8192)
                if not chunk:
                    break
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    
    @staticmethod
    async def _cleanup_chunks(temp_dir: str, chunks: List[int]):
        """清理分片文件"""
        try:
            for part_num in chunks:
                chunk_path = os.path.join(temp_dir, f"part_{part_num:05d}")
                if os.path.exists(chunk_path):
                    os.remove(chunk_path)
            
            # 删除合并后的临时文件
            merged_path = os.path.join(temp_dir, "merged_file")
            if os.path.exists(merged_path):
                os.remove(merged_path)
            
            # 删除空目录
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except Exception as e:
            print(f"清理临时文件失败: {e}")
    
    @staticmethod
    async def cancel_upload(upload_id: str):
        """取消上传"""
        meta_key = f"{ChunkedUploadService.UPLOAD_META_PREFIX}{upload_id}"
        chunks_key = f"{ChunkedUploadService.UPLOAD_CHUNKS_PREFIX}{upload_id}"
        
        # 删除Redis记录
        await redis_service.delete(meta_key)
        if redis_service.client:
            await redis_service.client.delete(chunks_key)
        
        # 清理临时文件
        temp_dir = ChunkedUploadService.get_temp_dir(upload_id)
        if os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @staticmethod
    async def retry_upload_part(
        upload_id: str,
        part_number: int,
        chunk_data: bytes,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """带重试的分片上传"""
        last_error = None
        for attempt in range(max_retries):
            try:
                return await ChunkedUploadService.upload_part(upload_id, part_number, chunk_data)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    # 指数退避
                    await asyncio.sleep(2 ** attempt)
        
        raise Exception(f"分片上传失败，已重试 {max_retries} 次: {last_error}")


# 全局单例
chunked_upload_service = ChunkedUploadService()
