"""企业素材RAG检索服务"""
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from ..models.models import EnterpriseMaterial
from ..services.qdrant_service import qdrant_service
from ..services.openai_service import OpenAIService
from ..config import settings


class TextExtractionService:
    """文本提取服务"""
    
    @staticmethod
    def extract_text_from_file(file_path: str) -> str:
        """从文件中提取文本"""
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.pdf':
            return TextExtractionService._extract_pdf(file_path)
        elif ext in ['.docx', '.doc']:
            return TextExtractionService._extract_docx(file_path)
        elif ext in ['.xlsx', '.xls']:
            return TextExtractionService._extract_excel(file_path)
        elif ext == '.txt':
            return TextExtractionService._extract_txt(file_path)
        else:
            raise ValueError(f"不支持的文件类型: {ext}")
    
    @staticmethod
    def _extract_pdf(file_path: str) -> str:
        """提取PDF文本"""
        try:
            import fitz
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            print(f"PDF提取失败: {e}")
            return ""
    
    @staticmethod
    def _extract_docx(file_path: str) -> str:
        """提取Word文本"""
        try:
            from docx import Document
            doc = Document(file_path)
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            return text
        except Exception as e:
            print(f"Word提取失败: {e}")
            return ""
    
    @staticmethod
    def _extract_excel(file_path: str) -> str:
        """提取Excel文本"""
        try:
            import pandas as pd
            text = ""
            df = pd.read_excel(file_path, sheet_name=None)
            for sheet_name, sheet_df in df.items():
                text += f"\n=== {sheet_name} ===\n"
                text += sheet_df.to_string() + "\n"
            return text
        except Exception as e:
            print(f"Excel提取失败: {e}")
            return ""
    
    @staticmethod
    def _extract_txt(file_path: str) -> str:
        """提取文本文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            with open(file_path, 'r', encoding='gbk') as f:
                return f.read()


class ChunkingService:
    """文本分块服务"""
    
    @staticmethod
    def chunk_by_paragraph(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[Dict[str, Any]]:
        """按段落分块"""
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) <= chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append({
                        "content": current_chunk.strip(),
                        "char_count": len(current_chunk)
                    })
                current_chunk = para + "\n\n"
        
        if current_chunk:
            chunks.append({
                "content": current_chunk.strip(),
                "char_count": len(current_chunk)
            })
        
        return chunks
    
    @staticmethod
    def chunk_by_section(text: str, max_chunk_size: int = 1000) -> List[Dict[str, Any]]:
        """按章节分块"""
        import re
        
        section_pattern = r'(第[一二三四五六七八九十\d]+[章节]|\d+\.|\([一二三四五六七八九十\d]+\))'
        parts = re.split(section_pattern, text)
        
        chunks = []
        current_chunk = ""
        
        for i, part in enumerate(parts):
            if len(current_chunk) + len(part) <= max_chunk_size:
                current_chunk += part
            else:
                if current_chunk.strip():
                    chunks.append({
                        "content": current_chunk.strip(),
                        "char_count": len(current_chunk)
                    })
                current_chunk = part
        
        if current_chunk.strip():
            chunks.append({
                "content": current_chunk.strip(),
                "char_count": len(current_chunk)
            })
        
        return chunks


class EmbeddingService:
    """向量化服务"""
    
    def __init__(self):
        self.openai_service = OpenAIService()
    
    async def generate_embedding(self, text: str) -> List[float]:
        """生成文本向量"""
        try:
            embedding = await self.openai_service.get_embedding(text)
            return embedding
        except Exception as e:
            print(f"生成embedding失败: {e}")
            return []
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """批量生成向量"""
        embeddings = []
        for text in texts:
            embedding = await self.generate_embedding(text)
            if embedding:
                embeddings.append(embedding)
        return embeddings


class RAGService:
    """RAG检索服务"""
    
    COLLECTION_NAME = "enterprise_materials"
    
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService()
        self._ensure_collection()
    
    def _ensure_collection(self):
        """确保集合存在"""
        try:
            if qdrant_service.client:
                collections = qdrant_service.client.get_collections().collections
                collection_names = [c.name for c in collections]
                
                if self.COLLECTION_NAME not in collection_names:
                    from qdrant_client.models import Distance, VectorParams
                    qdrant_service.client.create_collection(
                        collection_name=self.COLLECTION_NAME,
                        vectors_config=VectorParams(
                            size=1536,
                            distance=Distance.COSINE
                        )
                    )
        except Exception as e:
            print(f"确保集合失败: {e}")
    
    async def index_material(self, material_id: int) -> Dict[str, Any]:
        """索引企业素材"""
        material = self.db.query(EnterpriseMaterial).filter(
            EnterpriseMaterial.id == material_id
        ).first()
        
        if not material:
            return {"success": False, "message": "素材不存在"}
        
        if not material.content_text:
            return {"success": False, "message": "素材无文本内容"}
        
        chunks = ChunkingService.chunk_by_paragraph(material.content_text)
        
        if not chunks:
            return {"success": False, "message": "文本分块失败"}
        
        texts = [chunk["content"] for chunk in chunks]
        embeddings = await self.embedding_service.generate_embeddings(texts)
        
        if not embeddings:
            return {"success": False, "message": "向量化失败"}
        
        payloads = []
        for i, chunk in enumerate(chunks):
            payload = {
                "material_id": material.id,
                "material_name": material.name,
                "material_type": material.material_type,
                "content_text": chunk["content"],
                "chunk_index": i,
                "created_at": material.created_at.isoformat() if material.created_at else None
            }
            
            if material.material_type == "qualification":
                payload["expiry_date"] = material.expiry_date.isoformat() if material.expiry_date else None
                payload["is_expired"] = material.is_expired
            elif material.material_type == "project":
                payload["contract_amount"] = material.contract_amount
                payload["completion_date"] = material.completion_date.isoformat() if material.completion_date else None
                payload["client_name"] = material.client_name
            elif material.material_type == "product":
                payload["model_number"] = material.model_number
                payload["technical_params"] = material.technical_params
            
            payloads.append(payload)
        
        try:
            vector_ids = await qdrant_service.add_vectors(
                vectors=embeddings,
                payloads=payloads
            )
            
            material.vector_ids = vector_ids
            material.chunks_json = chunks
            self.db.commit()
            
            return {
                "success": True,
                "material_id": material_id,
                "chunks_count": len(chunks),
                "vector_ids": vector_ids
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def search_materials(
        self,
        query: str,
        material_type: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """检索企业素材"""
        query_embedding = await self.embedding_service.generate_embedding(query)
        
        if not query_embedding:
            return []
        
        filter_conditions = {}
        
        if material_type:
            filter_conditions["material_type"] = material_type
        
        if filters:
            if "min_amount" in filters:
                filter_conditions["gte_contract_amount"] = filters["min_amount"]
            if "max_amount" in filters:
                filter_conditions["lte_contract_amount"] = filters["max_amount"]
        
        try:
            results = await qdrant_service.search(
                query_vector=query_embedding,
                limit=top_k,
                filter_conditions=filter_conditions if filter_conditions else None
            )
            
            filtered_results = []
            for r in results:
                if filters:
                    if "min_amount" in filters:
                        amount = r["payload"].get("contract_amount", 0)
                        if amount < filters["min_amount"]:
                            continue
                    if "max_amount" in filters:
                        amount = r["payload"].get("contract_amount", 0)
                        if amount > filters["max_amount"]:
                            continue
                    
                    if "is_valid" in filters and filters["is_valid"]:
                        if r["payload"].get("is_expired", False):
                            continue
                
                filtered_results.append(r)
            
            return filtered_results
        except Exception as e:
            print(f"检索失败: {e}")
            return []
    
    async def search_qualifications(
        self,
        query: str,
        require_valid: bool = True,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """检索资质"""
        return await self.search_materials(
            query=query,
            material_type="qualification",
            filters={"is_valid": require_valid} if require_valid else None,
            top_k=top_k
        )
    
    async def search_projects(
        self,
        query: str,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """检索业绩"""
        filters = {}
        if min_amount is not None:
            filters["min_amount"] = min_amount
        if max_amount is not None:
            filters["max_amount"] = max_amount
        
        results = await self.search_materials(
            query=query,
            material_type="project",
            filters=filters if filters else None,
            top_k=top_k * 2
        )
        
        results.sort(key=lambda x: x["payload"].get("completion_date", ""), reverse=True)
        
        return results[:top_k]
    
    async def search_products(
        self,
        query: str,
        model_number: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """检索产品"""
        results = await self.search_materials(
            query=query,
            material_type="product",
            top_k=top_k
        )
        
        if model_number:
            results = [r for r in results if model_number.lower() in r["payload"].get("model_number", "").lower()]
        
        return results


def get_rag_service(db: Session = None) -> RAGService:
    """获取RAG服务实例"""
    from ..models.database import SessionLocal
    if db is None:
        db = SessionLocal()
    return RAGService(db)