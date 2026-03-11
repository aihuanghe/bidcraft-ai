"""Word文档解析API路由"""
import os
from fastapi import APIRouter, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import asyncio

from ..services.parse_task_service import parse_task_service
from ..services.ws_manager import ws_manager
from ..services.word_parser_service import WordParseService
from ..config import settings

router = APIRouter(prefix="/api/parse", tags=["文档解析"])


class ParseRequest(BaseModel):
    """解析请求"""
    file_path: str
    use_cache: bool = True


class ParseResponse(BaseModel):
    """解析响应"""
    task_id: str
    status: str
    message: str


@router.post("/", response_model=ParseResponse)
async def start_parse(
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    file_path: Optional[str] = None
):
    """触发Word文档解析"""
    try:
        save_path = None
        
        # 处理文件上传
        if file:
            # 保存上传的文件
            upload_dir = os.path.join(settings.upload_dir, "parse")
            os.makedirs(upload_dir, exist_ok=True)
            
            file_ext = os.path.splitext(file.filename)[1].lower()
            if file_ext not in ['.docx', '.doc']:
                raise HTTPException(status_code=400, detail="仅支持Word文档(.docx/.doc)")
            
            from datetime import datetime
            import uuid
            filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{file_ext}"
            save_path = os.path.join(upload_dir, filename)
            
            # 异步保存文件
            content = await file.read()
            with open(save_path, 'wb') as f:
                f.write(content)
        
        elif file_path:
            # 使用已有文件
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="文件不存在")
            save_path = file_path
        else:
            raise HTTPException(status_code=400, detail="请提供文件或文件路径")
        
        # 获取文件信息
        file_size = os.path.getsize(save_path)
        file_name = os.path.basename(save_path)
        
        # 检查是否支持
        if not WordParseService.is_supported(save_path):
            raise HTTPException(status_code=400, detail="不支持的文件格式")
        
        # 创建解析任务
        task = await parse_task_service.create_task(
            file_path=save_path,
            file_name=file_name,
            file_size=file_size
        )
        
        # 启动后台解析任务
        background_tasks.add_task(
            _run_parse_task,
            task.task_id
        )
        
        return ParseResponse(
            task_id=task.task_id,
            status="pending",
            message="解析任务已创建"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建解析任务失败: {str(e)}")


async def _run_parse_task(task_id: str):
    """执行解析任务"""
    async def progress_callback(progress: int, message: str):
        await ws_manager.send_progress(task_id, progress, message)
    
    try:
        await parse_task_service.execute_parse(task_id, progress_callback)
        
        # 获取结果并发送
        task = await parse_task_service.get_task(task_id)
        if task and task.result:
            await ws_manager.send_complete(task_id, task.result)
            
    except Exception as e:
        await ws_manager.send_error(task_id, str(e))


@router.get("/{task_id}/progress")
async def get_parse_progress(task_id: str):
    """SSE流式获取解析进度"""
    async def event_generator():
        # 等待任务完成或定期推送状态
        last_progress = -1
        
        while True:
            task = await parse_task_service.get_task(task_id)
            
            if not task:
                yield "data: {\"error\": \"任务不存在\"}\n\n"
                break
            
            # 推送进度更新
            if task.progress != last_progress:
                last_progress = task.progress
                data = {
                    "progress": task.progress,
                    "message": task.message,
                    "status": task.status.value
                }
                yield f"data: {data}\n\n"
            
            # 检查是否完成
            if task.status.value in ["completed", "failed", "cancelled"]:
                if task.result:
                    yield f"data: {{\"type\": \"complete\", \"result\": {task.result}}}\n\n"
                break
            
            # 等待
            await asyncio.sleep(1)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.websocket("/ws/{task_id}")
async def websocket_parse_progress(websocket: WebSocket, task_id: str):
    """WebSocket实时推送解析进度"""
    await ws_manager.connect(task_id, websocket)
    
    try:
        # 立即发送当前状态
        task = await parse_task_service.get_task(task_id)
        if task:
            await websocket.send_json({
                "type": "status",
                "progress": task.progress,
                "message": task.message,
                "status": task.status.value
            })
        
        # 保持连接并定期推送
        last_progress = -1
        
        while True:
            task = await parse_task_service.get_task(task_id)
            
            if not task:
                await websocket.send_json({"error": "任务不存在"})
                break
            
            # 推送进度更新
            if task.progress != last_progress:
                last_progress = task.progress
                await websocket.send_json({
                    "type": "progress",
                    "progress": task.progress,
                    "message": task.message,
                    "status": task.status.value
                })
            
            # 检查是否完成
            if task.status.value == "completed":
                if task.result:
                    await websocket.send_json({
                        "type": "complete",
                        "result": task.result
                    })
                break
            elif task.status.value == "failed":
                await websocket.send_json({
                    "type": "error",
                    "error": task.error
                })
                break
            
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.disconnect(task_id, websocket)


@router.get("/{task_id}")
async def get_parse_result(task_id: str):
    """获取解析结果"""
    task = await parse_task_service.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return {
        "task_id": task.task_id,
        "file_name": task.file_name,
        "status": task.status.value,
        "progress": task.progress,
        "message": task.message,
        "result": task.result,
        "error": task.error,
        "created_at": task.created_at.isoformat(),
        "completed_at": task.completed_at.isoformat() if task.completed_at else None
    }


@router.get("/")
async def list_parse_tasks(limit: int = 20):
    """列出解析任务"""
    tasks = await parse_task_service.list_tasks(limit)
    
    return {
        "tasks": [task.to_dict() for task in tasks],
        "count": len(tasks)
    }


@router.delete("/{task_id}")
async def cancel_parse_task(task_id: str):
    """取消解析任务"""
    task = await parse_task_service.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 更新任务状态
    task.status = "cancelled"
    await parse_task_service._save_task(task)
    
    return {"success": True, "message": "任务已取消"}
