"""大模型Router服务"""
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio

from .llm_provider import BaseLLMProvider, ProviderFactory
from ..utils.config_manager import config_manager


class LLMRouter:
    """大模型路由器 - 支持智能路由和故障转移"""
    
    DEFAULT_ROUTING = {
        'parsing': ['kimi', 'deepseek', 'openai'],
        'generation': ['deepseek', 'kimi', 'openai'],
        'embedding': ['openai'],
        'general': ['openai', 'kimi', 'deepseek']
    }
    
    def __init__(self):
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.current_provider: Optional[str] = None
        self.failover_enabled = True
        self.routing_strategy = self.DEFAULT_ROUTING.copy()
        self.usage_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'total_requests': 0,
            'total_tokens': 0,
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_errors': 0,
            'daily_usage': defaultdict(lambda: {'requests': 0, 'tokens': 0})
        })
        self._load_config()
    
    def _load_config(self):
        """从配置加载Provider信息"""
        config = config_manager.load_config()
        
        self.failover_enabled = config.get('failover_enabled', True)
        self.routing_strategy = config.get('routing_strategy', self.DEFAULT_ROUTING.copy())
        
        providers_config = config.get('providers', {})
        default_provider = config.get('default_provider', 'openai')
        
        for provider_type, provider_config in providers_config.items():
            if provider_config.get('enabled', False):
                try:
                    provider = ProviderFactory.create_provider(provider_type, provider_config)
                    if provider.validate_config():
                        self.providers[provider_type] = provider
                        if provider_type == default_provider:
                            self.current_provider = provider_type
                except Exception as e:
                    print(f"加载Provider {provider_type} 失败: {e}")
        
        if not self.current_provider and self.providers:
            self.current_provider = next(iter(self.providers.keys()))
    
    def get_available_providers(self) -> List[Dict[str, Any]]:
        """获取可用的Provider列表"""
        return [
            {
                'type': ptype,
                'model': p.model_name,
                'enabled': True
            }
            for ptype, p in self.providers.items()
        ]
    
    def _select_provider_by_task(self, task_type: str) -> Optional[str]:
        """根据任务类型选择Provider"""
        providers_list = self.routing_strategy.get(task_type, self.routing_strategy.get('general', []))
        
        for provider_type in providers_list:
            if provider_type in self.providers:
                return provider_type
        
        return None
    
    def _select_provider_by_context(self, context_length: int) -> Optional[str]:
        """根据上下文长度选择Provider"""
        for ptype, provider in self.providers.items():
            if hasattr(provider, 'get_context_limit'):
                if provider.get_context_limit() >= context_length:
                    return ptype
        
        return None
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        task_type: str = "general",
        provider_type: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """发送聊天请求，支持故障转移"""
        if provider_type:
            providers_to_try = [provider_type]
        else:
            selected = self._select_provider_by_task(task_type)
            providers_to_try = [selected] if selected else list(self.providers.keys())
        
        if self.failover_enabled and not provider_type:
            config = config_manager.load_config()
            providers_config = config.get('providers', {})
            for ptype in providers_to_try:
                if ptype in providers_config:
                    fallback_list = providers_config[ptype].get('fallback', [])
                    providers_to_try.extend(fallback_list)
        
        last_error = None
        for ptype in providers_to_try:
            if ptype not in self.providers:
                continue
            
            provider = self.providers[ptype]
            
            try:
                result = await provider.chat_completion(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                self._record_usage(ptype, result.get('usage', {}))
                self.current_provider = ptype
                return result
                
            except Exception as e:
                last_error = e
                self.usage_stats[ptype]['total_errors'] += 1
                print(f"Provider {ptype} 调用失败: {e}")
                continue
        
        raise Exception(f"所有Provider均失败: {last_error}")
    
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        task_type: str = "general",
        provider_type: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AsyncGenerator[str, None]:
        """流式聊天请求"""
        if provider_type and provider_type in self.providers:
            provider = self.providers[provider_type]
            try:
                async for chunk in provider.stream_chat(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                ):
                    yield chunk
                return
            except Exception as e:
                yield f"错误: {str(e)}"
                return
        
        selected = self._select_provider_by_task(task_type)
        if selected and selected in self.providers:
            provider = self.providers[selected]
            try:
                async for chunk in provider.stream_chat(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                ):
                    yield chunk
            except Exception as e:
                yield f"错误: {str(e)}"
        else:
            yield "错误: 没有可用的Provider"
    
    def _record_usage(self, provider_type: str, usage: Dict[str, int]):
        """记录使用统计"""
        stats = self.usage_stats[provider_type]
        stats['total_requests'] += 1
        stats['total_tokens'] += usage.get('total_tokens', 0)
        stats['prompt_tokens'] += usage.get('prompt_tokens', 0)
        stats['completion_tokens'] += usage.get('completion_tokens', 0)
        
        today = datetime.now().strftime('%Y-%m-%d')
        stats['daily_usage'][today]['requests'] += 1
        stats['daily_usage'][today]['tokens'] += usage.get('total_tokens', 0)
    
    def get_usage_stats(self, days: int = 30) -> Dict[str, Dict[str, Any]]:
        """获取使用统计"""
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        result = {}
        
        for ptype, stats in self.usage_stats.items():
            daily = {}
            for date, data in stats['daily_usage'].items():
                if date >= cutoff_date:
                    daily[date] = data
            
            result[ptype] = {
                'total_requests': stats['total_requests'],
                'total_tokens': stats['total_tokens'],
                'prompt_tokens': stats['prompt_tokens'],
                'completion_tokens': stats['completion_tokens'],
                'total_errors': stats['total_errors'],
                'daily_usage': daily
            }
        
        return result
    
    def set_active_provider(self, provider_type: str):
        """手动设置活动Provider"""
        if provider_type in self.providers:
            self.current_provider = provider_type
        else:
            raise ValueError(f"Provider {provider_type} 未配置")
    
    def get_routing_config(self) -> Dict[str, Any]:
        """获取路由配置"""
        return {
            'current_provider': self.current_provider,
            'routing_strategy': self.routing_strategy,
            'failover_enabled': self.failover_enabled,
            'available_providers': list(self.providers.keys())
        }
    
    def reload_config(self):
        """重新加载配置"""
        self.providers.clear()
        self._load_config()


_llm_router: Optional[LLMRouter] = None


def get_llm_router() -> LLMRouter:
    """获取LLM路由器单例"""
    global _llm_router
    if _llm_router is None:
        _llm_router = LLMRouter()
    return _llm_router


def reset_llm_router():
    """重置LLM路由器（用于配置更新后）"""
    global _llm_router
    _llm_router = None
