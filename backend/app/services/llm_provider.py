"""大模型统一接入层 - Provider实现"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, AsyncGenerator, Optional
import openai
import tiktoken
import asyncio


class BaseLLMProvider(ABC):
    """大模型Provider基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get("api_key", "")
        self.base_url = config.get("base_url", "")
        self.model_name = config.get("model_name", "")
        self.enabled = config.get("enabled", True)
        self.client = None
        
    @abstractmethod
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7, 
        max_tokens: int = 2000,
        **kwargs
    ) -> Dict[str, Any]:
        """发送聊天完成请求，返回完整响应"""
        pass
    
    @abstractmethod
    async def stream_chat(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7, 
        max_tokens: int = 2000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式聊天，返回增量内容"""
        yield ""
    
    def count_tokens(self, text: str) -> int:
        """计算文本token数量（使用tiktoken估算）"""
        try:
            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            return len(encoding.encode(text))
        except:
            return len(text) // 4
    
    def count_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """计算消息列表的总token数"""
        total = 0
        for msg in messages:
            total += self.count_tokens(msg.get("content", ""))
            total += 4
        total += 2
        return total
    
    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置是否有效"""
        pass
    
    def get_context_limit(self) -> int:
        """获取上下文长度限制"""
        return 8192
    
    def get_provider_type(self) -> str:
        """获取Provider类型"""
        return self.__class__.__name__.replace("Provider", "").lower()


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider"""
    
    SUPPORTED_MODELS = [
        "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4",
        "gpt-3.5-turbo", "gpt-3.5-turbo-16k",
        "o1", "o1-mini", "o1-preview",
        "gpt-4o-2024-08-06", "gpt-4o-mini-2024-07-18"
    ]
    
    CONTEXT_LIMITS = {
        "gpt-4o": 128000,
        "gpt-4o-mini": 128000,
        "gpt-4-turbo": 128000,
        "gpt-4": 8192,
        "gpt-3.5-turbo": 16385,
        "gpt-3.5-turbo-16k": 16385,
    }
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._init_client()
    
    def _init_client(self):
        """初始化OpenAI客户端"""
        if self.api_key:
            self.client = openai.AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url if self.base_url else None
            )
    
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7, 
        max_tokens: int = 2000,
        **kwargs
    ) -> Dict[str, Any]:
        if not self.client:
            raise Exception("OpenAI客户端未初始化")
        
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        return {
            "content": response.choices[0].message.content,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            "model": response.model,
            "provider": "openai"
        }
    
    async def stream_chat(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7, 
        max_tokens: int = 2000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        if not self.client:
            raise Exception("OpenAI客户端未初始化")
        
        stream = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
    
    def validate_config(self) -> bool:
        return bool(self.api_key and self.model_name)
    
    def get_context_limit(self) -> int:
        return self.CONTEXT_LIMITS.get(self.model_name, 8192)


class KimiProvider(BaseLLMProvider):
    """Kimi (Moonshot) Provider"""
    
    SUPPORTED_MODELS = [
        "kimi-flash-8k", "kimi-flash-32k", "kimi-flash-128k",
        "kimi-long-8k", "kimi-long-32k", "kimi-long-128k"
    ]
    
    CONTEXT_LIMITS = {
        "kimi-flash-8k": 8000,
        "kimi-flash-32k": 32000,
        "kimi-flash-128k": 128000,
        "kimi-long-8k": 8000,
        "kimi-long-32k": 32000,
        "kimi-long-128k": 128000,
    }
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._init_client()
    
    def _init_client(self):
        if self.api_key:
            base_url = self.base_url or "https://api.moonshot.cn/v1"
            self.client = openai.AsyncOpenAI(
                api_key=self.api_key,
                base_url=base_url
            )
    
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7, 
        max_tokens: int = 2000,
        **kwargs
    ) -> Dict[str, Any]:
        if not self.client:
            raise Exception("Kimi客户端未初始化")
        
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        return {
            "content": response.choices[0].message.content,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            "model": response.model,
            "provider": "kimi"
        }
    
    async def stream_chat(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7, 
        max_tokens: int = 2000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        if not self.client:
            raise Exception("Kimi客户端未初始化")
        
        stream = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
    
    def validate_config(self) -> bool:
        return bool(self.api_key and self.model_name)
    
    def get_context_limit(self) -> int:
        return self.CONTEXT_LIMITS.get(self.model_name, 32000)


class DeepSeekProvider(BaseLLMProvider):
    """DeepSeek Provider"""
    
    SUPPORTED_MODELS = [
        "deepseek-chat",
        "deepseek-coder",
        "deepseek-reasoner"
    ]
    
    CONTEXT_LIMITS = {
        "deepseek-chat": 64000,
        "deepseek-coder": 64000,
        "deepseek-reasoner": 64000,
    }
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._init_client()
    
    def _init_client(self):
        if self.api_key:
            base_url = self.base_url or "https://api.deepseek.com"
            self.client = openai.AsyncOpenAI(
                api_key=self.api_key,
                base_url=base_url
            )
    
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7, 
        max_tokens: int = 2000,
        **kwargs
    ) -> Dict[str, Any]:
        if not self.client:
            raise Exception("DeepSeek客户端未初始化")
        
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        return {
            "content": response.choices[0].message.content,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            "model": response.model,
            "provider": "deepseek"
        }
    
    async def stream_chat(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7, 
        max_tokens: int = 2000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        if not self.client:
            raise Exception("DeepSeek客户端未初始化")
        
        stream = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
    
    def validate_config(self) -> bool:
        return bool(self.api_key and self.model_name)
    
    def get_context_limit(self) -> int:
        return self.CONTEXT_LIMITS.get(self.model_name, 64000)


class ProviderFactory:
    """Provider工厂类"""
    
    _PROVIDERS = {
        "openai": OpenAIProvider,
        "kimi": KimiProvider,
        "deepseek": DeepSeekProvider,
    }
    
    @classmethod
    def create_provider(cls, provider_type: str, config: Dict[str, Any]) -> BaseLLMProvider:
        """创建Provider实例"""
        provider_class = cls._PROVIDERS.get(provider_type.lower())
        if not provider_class:
            raise ValueError(f"不支持的Provider类型: {provider_type}")
        return provider_class(config)
    
    @classmethod
    def get_supported_providers(cls) -> List[str]:
        """获取支持的Provider列表"""
        return list(cls._PROVIDERS.keys())
    
    @classmethod
    def get_provider_models(cls, provider_type: str) -> List[str]:
        """获取Provider支持的模型列表"""
        provider_class = cls._PROVIDERS.get(provider_type.lower())
        if not provider_class:
            return []
        return provider_class.SUPPORTED_MODELS
