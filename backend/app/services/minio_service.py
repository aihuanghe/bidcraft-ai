"""MinIO对象存储服务"""
import os
import uuid
from pathlib import Path
from typing import Optional, List
from minio import Minio
from minio.error import S3Error

from ..config import settings


class MinIOService:
    """MinIO服务封装"""
    
    def __init__(self):
        self._client: Optional[Minio] = None
        self._bucket_name = settings.minio.bucket_name
        self._initialized = False
    
    @property
    def client(self) -> Optional[Minio]:
        """获取MinIO客户端"""
        if not self._initialized:
            self._init_client()
        return self._client
    
    def _init_client(self):
        """初始化MinIO客户端"""
        try:
            self._client = Minio(
                settings.minio.endpoint,
                access_key=settings.minio.access_key,
                secret_key=settings.minio.secret_key,
                secure=settings.minio.secure
            )
            
            # 确保存储桶存在
            if not self._client.bucket_exists(self._bucket_name):
                self._client.make_bucket(self._bucket_name)
            
            self._initialized = True
        except Exception as e:
            print(f"MinIO初始化失败: {e}")
            self._client = None
            self._initialized = True
    
    async def upload_file(
        self,
        file_path: str,
        object_name: str,
        content_type: str = "application/octet-stream"
    ) -> str:
        """上传文件"""
        if not self.client:
            raise Exception("MinIO客户端未初始化")
        
        try:
            self._client.fput_object(
                self._bucket_name,
                object_name,
                file_path,
                content_type=content_type
            )
            return f"{settings.minio.url_base}/{self._bucket_name}/{object_name}"
        except S3Error as e:
            raise Exception(f"上传文件失败: {e}")
    
    async def download_file(self, object_name: str) -> str:
        """下载文件"""
        if not self.client:
            raise Exception("MinIO客户端未初始化")
        
        try:
            # 生成本地临时文件路径
            temp_dir = os.path.join(settings.upload_dir, "temp")
            os.makedirs(temp_dir, exist_ok=True)
            
            local_path = os.path.join(temp_dir, os.path.basename(object_name))
            
            self._client.fget_object(
                self._bucket_name,
                object_name,
                local_path
            )
            return local_path
        except S3Error as e:
            raise Exception(f"下载文件失败: {e}")
    
    async def delete_file(self, object_name: str):
        """删除文件"""
        if not self.client:
            raise Exception("MinIO客户端未初始化")
        
        try:
            self._client.remove_object(self._bucket_name, object_name)
        except S3Error as e:
            raise Exception(f"删除文件失败: {e}")
    
    def get_presigned_url(self, object_name: str, expires: int = 3600) -> str:
        """获取预签名URL"""
        if not self.client:
            raise Exception("MinIO客户端未初始化")
        
        try:
            url = self._client.presigned_get_object(
                self._bucket_name,
                object_name,
                expires=expires
            )
            return url
        except S3Error as e:
            raise Exception(f"获取预签名URL失败: {e}")
    
    async def list_objects(
        self,
        prefix: str = "",
        max_keys: int = 100
    ) -> List[dict]:
        """列出对象"""
        if not self.client:
            raise Exception("MinIO客户端未初始化")
        
        try:
            objects = self._client.list_objects(
                self._bucket_name,
                prefix=prefix,
                max_keys=max_keys
            )
            return [
                {
                    "name": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified.isoformat() if obj.last_modified else None
                }
                for obj in objects
            ]
        except S3Error as e:
            raise Exception(f"列出对象失败: {e}")


# 全局单例
minio_service = MinIOService()
