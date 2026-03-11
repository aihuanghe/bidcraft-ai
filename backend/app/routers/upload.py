"""分片上传API路由"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ..services.chunked_upload_service import ChunkedUploadService

router = APIRouter(prefix="/api/upload/chunked", tags=["分片上传"])

# 文件大小阈值，超过则使用分片上传
CHUNKED_UPLOAD_THRESHOLD = 10 * 1024 * 1024  # 10MB


class InitUploadRequest(BaseModel):
    """初始化上传请求"""
    filename: str
    file_size: int
    content_type: str = "application/octet-stream"


class UploadPartRequest(BaseModel):
    """上传分片请求"""
    upload_id: str
    part_number: int


class CompleteUploadRequest(BaseModel):
    """完成上传请求"""
    upload_id: str


@router.post("/init")
async def init_upload(request: InitUploadRequest):
    """初始化分片上传"""
    try:
        result = await ChunkedUploadService.init_upload(
            filename=request.filename,
            file_size=request.file_size,
            content_type=request.content_type
        )
        return {
            "success": True,
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"初始化上传失败: {str(e)}")


@router.post("/part")
async def upload_part(
    upload_id: str = Query(...),
    part_number: int = Query(...)
):
    """上传分片"""
    try:
        # 读取上传的分片数据
        chunk_data = await File().__class__.read()
        
        result = await ChunkedUploadService.retry_upload_part(
            upload_id=upload_id,
            part_number=part_number,
            chunk_data=chunk_data
        )
        
        return {
            "success": True,
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分片上传失败: {str(e)}")


@router.post("/part/file")
async def upload_part_file(
    upload_id: str = Query(...),
    part_number: int = Query(...),
    file: UploadFile = File(...)
):
    """通过文件上传分片"""
    try:
        # 读取文件内容
        chunk_data = await file.read()
        
        result = await ChunkedUploadService.retry_upload_part(
            upload_id=upload_id,
            part_number=part_number,
            chunk_data=chunk_data
        )
        
        return {
            "success": True,
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分片上传失败: {str(e)}")


@router.post("/complete")
async def complete_upload(request: CompleteUploadRequest):
    """完成分片上传"""
    try:
        result = await ChunkedUploadService.complete_upload(upload_id=request.upload_id)
        return {
            "success": True,
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"完成上传失败: {str(e)}")


@router.get("/status/{upload_id}")
async def get_upload_status(upload_id: str):
    """获取上传状态"""
    try:
        result = await ChunkedUploadService.get_upload_status(upload_id)
        return {
            "success": True,
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@router.delete("/{upload_id}")
async def cancel_upload(upload_id: str):
    """取消上传"""
    try:
        await ChunkedUploadService.cancel_upload(upload_id)
        return {
            "success": True,
            "message": "上传已取消"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取消上传失败: {str(e)}")
