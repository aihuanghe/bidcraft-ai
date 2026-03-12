"""占位符系统服务"""
from typing import Dict, List, Optional, Any
from enum import Enum
from sqlalchemy.orm import Session


class PlaceholderType(str, Enum):
    """占位符类型"""
    MANUAL = "manual"  # 手动输入
    RAG_RETRIEVAL = "rag_retrieval"  # RAG自动检索
    ERP_API = "erp_api"  # ERP系统获取
    HR_API = "hr_api"  # HR系统获取
    FINANCE_API = "finance_api"  # 财务系统获取


class PlaceholderSource(str, Enum):
    """占位符数据来源"""
    MANUAL = "manual"
    RAG = "rag"
    ERP = "erp"
    HR = "hr"
    FINANCE = "finance"


DEFAULT_PLACEHOLDERS = [
    {
        "id": "company_name",
        "type": "manual",
        "label": "公司名称",
        "required": True,
        "source": "manual",
        "category": "basic"
    },
    {
        "id": "company_address",
        "type": "manual",
        "label": "公司地址",
        "required": True,
        "source": "manual",
        "category": "basic"
    },
    {
        "id": "legal_representative",
        "type": "manual",
        "label": "法定代表人",
        "required": True,
        "source": "manual",
        "category": "basic"
    },
    {
        "id": "contact_person",
        "type": "manual",
        "label": "联系人",
        "required": True,
        "source": "manual",
        "category": "basic"
    },
    {
        "id": "contact_phone",
        "type": "manual",
        "label": "联系电话",
        "required": True,
        "source": "manual",
        "category": "basic"
    },
    {
        "id": "bid_amount",
        "type": "finance_api",
        "label": "投标报价",
        "required": True,
        "source": "finance",
        "category": "price"
    },
    {
        "id": "project_manager",
        "type": "hr_api",
        "label": "项目经理",
        "required": True,
        "source": "hr",
        "category": "personnel"
    },
    {
        "id": "team_members",
        "type": "hr_api",
        "label": "项目团队成员",
        "required": True,
        "source": "hr",
        "category": "personnel"
    },
    {
        "id": "qualifications",
        "type": "rag_retrieval",
        "label": "企业资质",
        "required": True,
        "source": "rag",
        "category": "qualification"
    },
    {
        "id": "similar_projects",
        "type": "rag_retrieval",
        "label": "类似业绩",
        "required": True,
        "source": "rag",
        "category": "project"
    },
    {
        "id": "technical_方案",
        "type": "rag_retrieval",
        "label": "技术方案参考",
        "required": False,
        "source": "rag",
        "category": "technical"
    },
    {
        "id": "products",
        "type": "rag_retrieval",
        "label": "产品资料",
        "required": False,
        "source": "rag",
        "category": "product"
    },
]


class PlaceholderService:
    """占位符服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_placeholders_from_template(self, template_structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从模板结构中提取占位符"""
        placeholders = []
        
        sections = template_structure.get("sections", [])
        
        for section in sections:
            section_type = section.get("type", "")
            section_title = section.get("title", "")
            content = section.get("content", "")
            
            if section_type == "letter" or "函" in section_title:
                placeholders.extend(self._extract_letter_placeholders(content))
            
            elif section_type == "business":
                placeholders.extend(self._extract_business_placeholders(content))
            
            elif section_type == "technical":
                placeholders.extend(self._extract_technical_placeholders(content))
            
            elif section_type == "price":
                placeholders.extend(self._extract_price_placeholders(content))
        
        placeholders.extend(DEFAULT_PLACEHOLDERS)
        
        return placeholders
    
    def _extract_letter_placeholders(self, content: str) -> List[Dict[str, Any]]:
        """提取投标函占位符"""
        placeholders = []
        
        if "公司" in content or "投标人" in content:
            placeholders.append({
                "id": "company_name",
                "type": "manual",
                "label": "投标人名称",
                "required": True,
                "source": "manual",
                "category": "letter"
            })
        
        if "项目名称" in content or "标的" in content:
            placeholders.append({
                "id": "project_name",
                "type": "manual",
                "label": "投标项目名称",
                "required": True,
                "source": "manual",
                "category": "letter"
            })
        
        if "报价" in content or "金额" in content:
            placeholders.append({
                "id": "bid_amount",
                "type": "manual",
                "label": "投标报价",
                "required": True,
                "source": "manual",
                "category": "letter"
            })
        
        return placeholders
    
    def _extract_business_placeholders(self, content: str) -> List[Dict[str, Any]]:
        """提取商务部分占位符"""
        placeholders = []
        
        if "资质" in content or "证书" in content:
            placeholders.append({
                "id": "qualifications",
                "type": "rag_retrieval",
                "label": "企业资质证书",
                "required": True,
                "source": "rag",
                "category": "qualification"
            })
        
        if "业绩" in content or "案例" in content:
            placeholders.append({
                "id": "similar_projects",
                "type": "rag_retrieval",
                "label": "类似项目业绩",
                "required": True,
                "source": "rag",
                "category": "project"
            })
        
        if "财务" in content or "审计" in content:
            placeholders.append({
                "id": "financial_info",
                "type": "finance_api",
                "label": "财务资料",
                "required": True,
                "source": "finance",
                "category": "finance"
            })
        
        return placeholders
    
    def _extract_technical_placeholders(self, content: str) -> List[Dict[str, Any]]:
        """提取技术部分占位符"""
        placeholders = []
        
        if "人员" in content or "团队" in content:
            placeholders.append({
                "id": "project_manager",
                "type": "hr_api",
                "label": "项目经理",
                "required": True,
                "source": "hr",
                "category": "personnel"
            })
            placeholders.append({
                "id": "team_members",
                "type": "hr_api",
                "label": "项目团队成员",
                "required": True,
                "source": "hr",
                "category": "personnel"
            })
        
        if "方案" in content or "技术" in content:
            placeholders.append({
                "id": "technical_方案",
                "type": "rag_retrieval",
                "label": "技术方案参考",
                "required": False,
                "source": "rag",
                "category": "technical"
            })
        
        if "产品" in content or "设备" in content:
            placeholders.append({
                "id": "products",
                "type": "rag_retrieval",
                "label": "产品资料",
                "required": False,
                "source": "rag",
                "category": "product"
            })
        
        return placeholders
    
    def _extract_price_placeholders(self, content: str) -> List[Dict[str, Any]]:
        """提取报价部分占位符"""
        return [
            {
                "id": "bid_amount",
                "type": "finance_api",
                "label": "投标总价",
                "required": True,
                "source": "finance",
                "category": "price"
            },
            {
                "id": "price_breakdown",
                "type": "manual",
                "label": "分项报价",
                "required": True,
                "source": "manual",
                "category": "price"
            }
        ]
    
    def get_project_placeholders(self, project_id: int, template_structure: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """获取项目的占位符列表"""
        from ..models.models import BidProject
        
        project = self.db.query(BidProject).filter(BidProject.id == project_id).first()
        if not project:
            return []
        
        placeholders = self.get_placeholders_from_template(template_structure or {})
        
        existing_values = project.placeholder_values or {}
        
        for placeholder in placeholders:
            placeholder_id = placeholder["id"]
            if placeholder_id in existing_values:
                placeholder["value"] = existing_values[placeholder_id].get("value")
                placeholder["status"] = existing_values[placeholder_id].get("status", "filled")
                placeholder["source"] = existing_values[placeholder_id].get("source", "manual")
            else:
                placeholder["value"] = None
                placeholder["status"] = "unfilled"
        
        return placeholders
    
    def fill_placeholder(
        self,
        project_id: int,
        placeholder_id: str,
        value: Any,
        mode: str = "manual",
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """填充占位符"""
        from ..models.models import BidProject
        
        project = self.db.query(BidProject).filter(BidProject.id == project_id).first()
        if not project:
            return {"success": False, "message": "项目不存在"}
        
        placeholder_values = project.placeholder_values or {}
        
        placeholder_values[placeholder_id] = {
            "value": value,
            "mode": mode,
            "source": mode,
            "status": "filled",
            "filled_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        project.placeholder_values = placeholder_values
        self.db.commit()
        
        return {
            "success": True,
            "placeholder_id": placeholder_id,
            "value": value,
            "status": "filled"
        }
    
    def auto_fill_with_rag(
        self,
        project_id: int,
        placeholder_id: str,
        query: str,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """使用RAG自动填充占位符"""
        from ..services.rag_service import get_rag_service
        
        try:
            rag_service = get_rag_service()
            
            material_type = self._get_material_type_by_placeholder(placeholder_id)
            
            results = rag_service.search_materials(
                query=query,
                material_type=material_type,
                top_k=top_k
            )
            
            if not results:
                return {
                    "success": False,
                    "message": "未找到相关素材",
                    "results": []
                }
            
            fill_value = self._format_rag_results(placeholder_id, results)
            
            return self.fill_placeholder(
                project_id=project_id,
                placeholder_id=placeholder_id,
                value=fill_value,
                mode="rag",
                metadata={"query": query, "results_count": len(results)}
            )
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def _get_material_type_by_placeholder(self, placeholder_id: str) -> str:
        """根据占位符ID获取素材类型"""
        mapping = {
            "qualifications": "qualification",
            "similar_projects": "project",
            "technical_方案": "document",
            "products": "product",
            "project_manager": "personnel",
            "team_members": "personnel",
            "financial_info": "finance"
        }
        return mapping.get(placeholder_id, "document")
    
    def _format_rag_results(self, placeholder_id: str, results: List[Dict]) -> Any:
        """格式化RAG检索结果"""
        if placeholder_id in ["qualifications"]:
            return [r["payload"].get("name", "") for r in results if r.get("payload")]
        
        elif placeholder_id in ["similar_projects"]:
            return [
                {
                    "name": r["payload"].get("name", ""),
                    "contract_amount": r["payload"].get("contract_amount"),
                    "completion_date": r["payload"].get("completion_date"),
                    "score": r.get("score", 0)
                }
                for r in results if r.get("payload")
            ]
        
        elif placeholder_id in ["products"]:
            return [
                {
                    "name": r["payload"].get("name", ""),
                    "model_number": r["payload"].get("model_number"),
                    "score": r.get("score", 0)
                }
                for r in results if r.get("payload")
            ]
        
        else:
            return [
                {
                    "content": r["payload"].get("content_text", "")[:500],
                    "source": r["payload"].get("name", ""),
                    "score": r.get("score", 0)
                }
                for r in results if r.get("payload")
            ]


from datetime import datetime


def get_placeholder_service(db: Session) -> PlaceholderService:
    """获取占位符服务实例"""
    return PlaceholderService(db)