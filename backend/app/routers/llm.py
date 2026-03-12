"""LLM统一接入层API路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from ..services.llm_provider import ProviderFactory
from ..services.llm_router import get_llm_router, reset_llm_router
from ..utils.config_manager import config_manager

router = APIRouter(prefix="/api/llm", tags=["大模型管理"])


class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    task_type: str = "general"
    provider_type: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000


class ProviderConfigRequest(BaseModel):
    providers: Dict[str, Dict[str, Any]]
    default_provider: Optional[str] = None
    failover_enabled: bool = True


class ProviderTestRequest(BaseModel):
    provider_type: str
    api_key: str
    base_url: Optional[str] = None
    model_name: str


@router.get("/providers")
async def list_providers():
    try:
        router_instance = get_llm_router()
        providers = router_instance.get_available_providers()
        
        all_providers = []
        for ptype in ProviderFactory.get_supported_providers():
            models = ProviderFactory.get_provider_models(ptype)
            is_loaded = ptype in [p["type"] for p in providers]
            
            all_providers.append({
                "type": ptype,
                "models": models,
                "is_loaded": is_loaded
            })
        
        return {
            "success": True,
            "providers": all_providers,
            "current_provider": router_instance.current_provider
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/routing")
async def get_routing_config():
    try:
        router_instance = get_llm_router()
        return {
            "success": True,
            "config": router_instance.get_routing_config()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        router_instance = get_llm_router()
        
        result = await router_instance.chat_completion(
            messages=request.messages,
            task_type=request.task_type,
            provider_type=request.provider_type,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    from fastapi.responses import StreamingResponse
    import json
    
    router_instance = get_llm_router()
    
    async def generate():
        try:
            async for chunk in router_instance.stream_chat(
                messages=request.messages,
                task_type=request.task_type,
                provider_type=request.provider_type,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            ):
                yield f"data: {json.dumps({'chunk': chunk}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/usage")
async def get_usage_stats(days: int = 30):
    try:
        router_instance = get_llm_router()
        stats = router_instance.get_usage_stats(days)
        
        total_tokens = sum(s.get("total_tokens", 0) for s in stats.values())
        total_requests = sum(s.get("total_requests", 0) for s in stats.values())
        total_errors = sum(s.get("total_errors", 0) for s in stats.values())
        
        return {
            "success": True,
            "summary": {
                "total_tokens": total_tokens,
                "total_requests": total_requests,
                "total_errors": total_errors,
                "providers": stats
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/providers")
async def update_provider_config(config: ProviderConfigRequest):
    try:
        current_config = config_manager.load_config()
        
        current_config["providers"] = config.providers
        if config.default_provider:
            current_config["default_provider"] = config.default_provider
        current_config["failover_enabled"] = config.failover_enabled
        
        config_manager.save_full_config(current_config)
        
        reset_llm_router()
        
        return {
            "success": True,
            "message": "配置已更新"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/providers/test")
async def test_provider(request: ProviderTestRequest):
    try:
        config_data = {
            "api_key": request.api_key,
            "base_url": request.base_url or "",
            "model_name": request.model_name,
            "enabled": True
        }
        
        provider = ProviderFactory.create_provider(request.provider_type, config_data)
        
        if not provider.validate_config():
            return {
                "success": False,
                "message": "配置无效，请检查API Key和模型名称"
            }
        
        test_messages = [
            {"role": "user", "content": "你好，请回复'测试成功'"}
        ]
        
        result = await provider.chat_completion(
            messages=test_messages,
            max_tokens=100
        )
        
        if result.get("content"):
            return {
                "success": True,
                "message": "连接测试成功",
                "response": result["content"]
            }
        else:
            return {
                "success": False,
                "message": "未收到有效响应"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"测试失败: {str(e)}"
        }


@router.get("/models/{provider_type}")
async def get_provider_models(provider_type: str):
    models = ProviderFactory.get_provider_models(provider_type)
    return {
        "success": True,
        "provider": provider_type,
        "models": models
    }


@router.post("/router/select")
async def select_provider(provider_type: str):
    try:
        router_instance = get_llm_router()
        router_instance.set_active_provider(provider_type)
        return {
            "success": True,
            "current_provider": provider_type
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
