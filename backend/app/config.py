try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from typing import Optional, List
import os


class DatabaseSettings(BaseSettings):
    """数据库配置"""
    # SQLite配置（保留原有）
    sqlite_path: str = "data/bidcraft.db"
    sqlite_echo: bool = False
    
    # Alembic配置
    alembic_config_path: str = "alembic.ini"


class RedisSettings(BaseSettings):
    """Redis配置"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    decode_responses: bool = True
    
    # 连接池配置
    max_connections: int = 10
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    
    # 缓存配置
    cache_ttl: int = 3600
    cache_prefix: str = "bidcraft:"
    
    # 消息队列配置
    queue_name: str = "bidcraft:queue"
    
    @property
    def url(self) -> str:
        """Redis连接URL"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class MinIOSettings(BaseSettings):
    """MinIO对象存储配置"""
    endpoint: str = "localhost:9000"
    access_key: str = "minioadmin"
    secret_key: str = "minioadmin"
    secure: bool = False
    bucket_name: str = "bidcraft"
    
    # 文件大小限制
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    
    # 存储路径前缀
    object_prefix: str = "documents/"
    
    @property
    def url_base(self) -> str:
        """MinIO服务URL"""
        protocol = "https" if self.secure else "http"
        return f"{protocol}://{self.endpoint}"


class QdrantSettings(BaseSettings):
    """Qdrant向量数据库配置"""
    host: str = "localhost"
    port: int = 6333
    grpc_port: int = 6334
    prefer_grpc: bool = False
    
    # 集合配置
    collection_name: str = "bid_documents"
    vector_size: int = 1536  # OpenAI ada-002 embedding size
    
    # 距离度量
    distance_metric: str = "Cosine"
    
    @property
    def url(self) -> str:
        """Qdrant服务URL"""
        return f"http://{self.host}:{self.port}"


class Settings(BaseSettings):
    """应用设置"""
    app_name: str = "AI写标书助手"
    app_version: str = "3.0.0"
    debug: bool = False
    
    # CORS设置
    cors_origins: list = [
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:3001", 
        "http://127.0.0.1:3001",
        "http://localhost:3002", 
        "http://127.0.0.1:3002",
        "http://localhost:3003", 
        "http://127.0.0.1:3003",
        "http://localhost:3004", 
        "http://127.0.0.1:3004"
    ]
    
    # 文件上传设置
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    upload_dir: str = "uploads"
    
    # OpenAI默认设置
    default_model: str = "gpt-3.5-turbo"
    
    # 数据库配置
    database: DatabaseSettings = DatabaseSettings()
    
    # Redis配置
    redis: RedisSettings = RedisSettings()
    
    # MinIO配置
    minio: MinIOSettings = MinIOSettings()
    
    # Qdrant配置
    qdrant: QdrantSettings = QdrantSettings()
    
    # Celery配置
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"


# 全局设置实例
settings = Settings()

# 确保上传目录存在
os.makedirs(settings.upload_dir, exist_ok=True)

# 确保数据目录存在
os.makedirs(os.path.dirname(settings.database.sqlite_path) or "data", exist_ok=True)
