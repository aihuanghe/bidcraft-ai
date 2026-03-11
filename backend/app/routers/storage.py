"""存储相关API路由"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from typing import Optional
import os
import uuid
from pathlib import Path

from ..config import settings
from ..services.minio_service import minio_service

router = APIRouter(prefix="/api/storage", tags=["存储管理"])


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    folder: Optional[str] = "documents"
):
    """上传文件到存储"""
    try:
        # 生唯一文件名
        file_ext = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        
        # 保存到本地临时文件
        temp_path = os.path.join(settings.upload_dir, "temp", unique_filename)
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)
        
        # 上传到MinIO
        object_name = f"{folder}/{unique_filename}"
        file_url = await minio_service.upload_file(
            file_path=temp_path,
            object_name=object_name,
            content_type=file.content_type
        )
        
        # 清理临时文件
        os.remove(temp_path)
        
        return {
            "success": True,
            "filename": file.filename,
            "object_name": object_name,
            "file_url": file_url,
            "size": len(content)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.get("/download/{object_name:path}")
async def download_file(object_name: str):
    """下载文件"""
    try:
        local_path = await minio_service.download_file(object_name)
        return FileResponse(
            path=local_path,
            filename=os.path.basename(object_name),
            media_type="application/octet-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"文件不存在: {str(e)}")


@router.get("/url/{object_name:path}")
async def get_file_url(object_name: str, expires: int = 3600):
    """获取文件访问URL"""
    try:
        url = minio_service.get_presigned_url(object_name, expires)
        return {
            "success": True,
            "url": url,
            "expires": expires
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取URL失败: {str(e)}")


@router.delete("/{object_name:path}")
async def delete_file(object_name: str):
    """删除文件"""
    try:
        await minio_service.delete_file(object_name)
        return {"success": True, "message": "文件已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.get("/list")
async def list_files(
    prefix: str = "documents/",
    max_keys: int = 100
):
    """列出文件"""
    try:
        files = await minio_service.list_objects(prefix, max_keys)
        return {
            "success": True,
            "files": files,
            "count": len(files)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"列表获取失败: {str(e)}")
