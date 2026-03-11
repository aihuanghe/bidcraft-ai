"""Qdrant向量数据库服务"""
from typing import List, Optional, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from qdrant_client.http.exceptions import UnexpectedResponse

from ..config import settings


class QdrantService:
    """Qdrant向量数据库服务封装"""
    
    def __init__(self):
        self._client: Optional[QdrantClient] = None
        self._collection_name = settings.qdrant.collection_name
        self._initialized = False
    
    @property
    def client(self) -> Optional[QdrantClient]:
        """获取Qdrant客户端"""
        if not self._initialized:
            self._init_client()
        return self._client
    
    def _init_client(self):
        """初始化Qdrant客户端"""
        try:
            self._client = QdrantClient(
                url=settings.qdrant.url,
                prefer_grpc=settings.qdrant.prefer_grpc
            )
            self._initialized = True
            # 确保集合存在
            self._ensure_collection()
        except Exception as e:
            print(f"Qdrant初始化失败: {e}")
            self._client = None
            self._initialized = True
    
    def _ensure_collection(self):
        """确保集合存在"""
        if not self.client:
            return
        
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self._collection_name not in collection_names:
                distance = Distance.COSINE
                if settings.qdrant.distance_metric == "Euclidean":
                    distance = Distance.EUCLID
                elif settings.qdrant.distance_metric == "Dot":
                    distance = Distance.DOT
                
                self.client.create_collection(
                    collection_name=self._collection_name,
                    vectors_config=VectorParams(
                        size=settings.qdrant.vector_size,
                        distance=distance
                    )
                )
        except Exception as e:
            print(f"确保集合失败: {e}")
    
    async def add_vectors(
        self,
        vectors: List[List[float]],
        payloads: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """添加向量"""
        if not self.client:
            raise Exception("Qdrant客户端未初始化")
        
        try:
            if ids is None:
                import uuid
                ids = [str(uuid.uuid4()) for _ in vectors]
            
            points = [
                PointStruct(
                    id=id,
                    vector=vector,
                    payload=payload
                )
                for id, vector, payload in zip(ids, vectors, payloads)
            ]
            
            self.client.upsert(
                collection_name=self._collection_name,
                points=points
            )
            
            return ids
        except Exception as e:
            raise Exception(f"添加向量失败: {e}")
    
    async def search(
        self,
        query_vector: List[float],
        limit: int = 5,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """搜索向量"""
        if not self.client:
            raise Exception("Qdrant客户端未初始化")
        
        try:
            search_filter = None
            if filter_conditions:
                must_conditions = []
                for key, value in filter_conditions.items():
                    must_conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
                if must_conditions:
                    search_filter = Filter(must=must_conditions)
            
            results = self.client.search(
                collection_name=self._collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=search_filter
            )
            
            return [
                {
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload
                }
                for result in results
            ]
        except Exception as e:
            raise Exception(f"搜索向量失败: {e}")
    
    async def delete_vectors(self, ids: List[str]):
        """删除向量"""
        if not self.client:
            raise Exception("Qdrant客户端未初始化")
        
        try:
            self.client.delete(
                collection_name=self._collection_name,
                points_selector=ids
            )
        except Exception as e:
            raise Exception(f"删除向量失败: {e}")
    
    async def get_vector(self, id: str) -> Optional[Dict[str, Any]]:
        """获取向量"""
        if not self.client:
            raise Exception("Qdrant客户端未初始化")
        
        try:
            result = self.client.retrieve(
                collection_name=self._collection_name,
                ids=[id]
            )
            
            if result:
                return {
                    "id": result[0].id,
                    "vector": result[0].vector,
                    "payload": result[0].payload
                }
            return None
        except Exception as e:
            raise Exception(f"获取向量失败: {e}")
    
    async def count_vectors(self) -> int:
        """获取向量数量"""
        if not self.client:
            return 0
        
        try:
            return self.client.count(
                collection_name=self._collection_name
            ).count
        except Exception as e:
            print(f"获取向量数量失败: {e}")
            return 0


# 全局单例
qdrant_service = QdrantService()
