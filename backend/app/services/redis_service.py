"""Redis缓存和消息队列服务"""
import json
from typing import Optional, Any, List
import redis.asyncio as aioredis
from redis.asyncio import Redis

from ..config import settings


class RedisService:
    """Redis服务封装"""
    
    def __init__(self):
        self._client: Optional[Redis] = None
        self._initialized = False
    
    @property
    def client(self) -> Optional[Redis]:
        """获取Redis客户端"""
        if not self._initialized:
            self._init_client()
        return self._client
    
    def _init_client(self):
        """初始化Redis客户端"""
        try:
            self._client = aioredis.from_url(
                settings.redis.url,
                encoding="utf-8",
                decode_responses=settings.redis.decode_responses,
                max_connections=settings.redis.max_connections,
                socket_timeout=settings.redis.socket_timeout,
                socket_connect_timeout=settings.redis.socket_connect_timeout
            )
            self._initialized = True
        except Exception as e:
            print(f"Redis初始化失败: {e}")
            self._client = None
            self._initialized = True
    
    async def get(self, key: str) -> Optional[str]:
        """获取值"""
        if not self.client:
            return None
        try:
            return await self.client.get(key)
        except Exception as e:
            print(f"Redis GET失败: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """设置值"""
        if not self.client:
            return False
        try:
            if ttl:
                await self.client.setex(key, ttl, value)
            else:
                await self.client.set(key, value)
            return True
        except Exception as e:
            print(f"Redis SET失败: {e}")
            return False
    
    async def delete(self, *keys: str) -> int:
        """删除键"""
        if not self.client:
            return 0
        try:
            return await self.client.delete(*keys)
        except Exception as e:
            print(f"Redis DELETE失败: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self.client:
            return False
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            print(f"Redis EXISTS失败: {e}")
            return False
    
    async def cache_get(self, key: str) -> Optional[Any]:
        """获取缓存（自动JSON解析）"""
        value = await self.get(f"{settings.redis.cache_prefix}{key}")
        if value:
            try:
                return json.loads(value)
            except:
                return value
        return None
    
    async def cache_set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """设置缓存（自动JSON序列化）"""
        if ttl is None:
            ttl = settings.redis.cache_ttl
        
        cache_key = f"{settings.redis.cache_prefix}{key}"
        
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        
        return await self.set(cache_key, value, ttl)
    
    async def cache_delete(self, key: str) -> int:
        """删除缓存"""
        return await self.delete(f"{settings.redis.cache_prefix}{key}")
    
    # 消息队列操作
    async def queue_push(self, queue_name: str, value: Any) -> bool:
        """推送消息到队列"""
        if not self.client:
            return False
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            await self.client.rpush(queue_name, value)
            return True
        except Exception as e:
            print(f"Redis队列PUSH失败: {e}")
            return False
    
    async def queue_pop(self, queue_name: str, timeout: int = 0) -> Optional[Any]:
        """从队列弹出消息"""
        if not self.client:
            return None
        try:
            if timeout > 0:
                result = await self.client.blpop(queue_name, timeout=timeout)
                if result:
                    value = result[1]
                else:
                    return None
            else:
                value = await self.client.lpop(queue_name)
            
            if value:
                try:
                    return json.loads(value)
                except:
                    return value
            return None
        except Exception as e:
            print(f"Redis队列POP失败: {e}")
            return None
    
    async def queue_length(self, queue_name: str) -> int:
        """获取队列长度"""
        if not self.client:
            return 0
        try:
            return await self.client.llen(queue_name)
        except Exception as e:
            print(f"Redis队列长度失败: {e}")
            return 0
    
    async def close(self):
        """关闭连接"""
        if self.client:
            await self.client.close()


# 全局单例
redis_service = RedisService()
