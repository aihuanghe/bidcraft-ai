"""占位符和企业数据相关API路由"""
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from ..models.database import get_db
from ..models.models import BidProject, EnterpriseMaterial
from ..services.placeholder_service import get_placeholder_service
from ..services.rag_service import get_rag_service, TextExtractionService
from ..services.enterprise_data_provider import get_enterprise_providers
from ..config import settings

router = APIRouter(prefix="/api/enterprise", tags=["企业数据管理"])


class PlaceholderFillRequest(BaseModel):
    """占位符填充请求"""
    value: Any
    mode: str = "manual"


class RAGSearchRequest(BaseModel):
    """RAG检索请求"""
    query: str
    material_type: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    top_k: int = 5


class MaterialUploadRequest(BaseModel):
    """素材上传请求"""
    bid_project_id: Optional[int] = None
    material_type: str
    name: str
    description: Optional[str] = None
    contract_amount: Optional[float] = None
    completion_date: Optional[str] = None
    client_name: Optional[str] = None
    model_number: Optional[str] = None
    technical_params: Optional[Dict[str, Any]] = None


@router.get("/projects/{project_id}/placeholders")
async def get_project_placeholders(
    project_id: int,
    template_structure: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取项目占位符列表"""
    import json
    
    project = db.query(BidProject).filter(BidProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    template_struct = {}
    if template_structure:
        try:
            template_struct = json.loads(template_structure)
        except:
            pass
    
    placeholder_service = get_placeholder_service(db)
    placeholders = placeholder_service.get_project_placeholders(project_id, template_struct)
    
    return {
        "success": True,
        "placeholders": placeholders,
        "filled_count": sum(1 for p in placeholders if p.get("status") == "filled"),
        "total_count": len(placeholders)
    }


@router.post("/projects/{project_id}/placeholders/{placeholder_id}/fill")
async def fill_placeholder(
    project_id: int,
    placeholder_id: str,
    request: PlaceholderFillRequest,
    db: Session = Depends(get_db)
):
    """填充占位符"""
    placeholder_service = get_placeholder_service(db)
    
    result = placeholder_service.fill_placeholder(
        project_id=project_id,
        placeholder_id=placeholder_id,
        value=request.value,
        mode=request.mode
    )
    
    return result


@router.post("/projects/{project_id}/placeholders/{placeholder_id}/auto-fill")
async def auto_fill_placeholder(
    project_id: int,
    placeholder_id: str,
    query: str,
    top_k: int = 3,
    db: Session = Depends(get_db)
):
    """使用RAG自动填充占位符"""
    placeholder_service = get_placeholder_service(db)
    
    result = placeholder_service.auto_fill_with_rag(
        project_id=project_id,
        placeholder_id=placeholder_id,
        query=query,
        top_k=top_k
    )
    
    return result


@router.get("/projects/{project_id}/placeholder-values")
async def get_placeholder_values(
    project_id: int,
    db: Session = Depends(get_db)
):
    """获取项目占位符值"""
    project = db.query(BidProject).filter(BidProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    return {
        "success": True,
        "placeholder_values": project.placeholder_values or {}
    }


@router.post("/materials/search")
async def search_materials(
    request: RAGSearchRequest,
    db: Session = Depends(get_db)
):
    """RAG检索企业素材"""
    rag_service = get_rag_service(db)
    
    results = await rag_service.search_materials(
        query=request.query,
        material_type=request.material_type,
        filters=request.filters,
        top_k=request.top_k
    )
    
    return {
        "success": True,
        "results": results,
        "count": len(results)
    }


@router.post("/materials/search/qualifications")
async def search_qualifications(
    query: str,
    require_valid: bool = True,
    top_k: int = 5,
    db: Session = Depends(get_db)
):
    """检索资质"""
    rag_service = get_rag_service(db)
    
    results = await rag_service.search_qualifications(
        query=query,
        require_valid=require_valid,
        top_k=top_k
    )
    
    return {
        "success": True,
        "results": results,
        "count": len(results)
    }


@router.post("/materials/search/projects")
async def search_projects(
    query: str,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    top_k: int = 5,
    db: Session = Depends(get_db)
):
    """检索业绩"""
    rag_service = get_rag_service(db)
    
    results = await rag_service.search_projects(
        query=query,
        min_amount=min_amount,
        max_amount=max_amount,
        top_k=top_k
    )
    
    return {
        "success": True,
        "results": results,
        "count": len(results)
    }


@router.post("/materials/search/products")
async def search_products(
    query: str,
    model_number: Optional[str] = None,
    top_k: int = 5,
    db: Session = Depends(get_db)
):
    """检索产品"""
    rag_service = get_rag_service(db)
    
    results = await rag_service.search_products(
        query=query,
        model_number=model_number,
        top_k=top_k
    )
    
    return {
        "success": True,
        "results": results,
        "count": len(results)
    }


@router.post("/materials/with-upload")
async def upload_and_index_material(
    request: MaterialUploadRequest,
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """上传素材并索引"""
    material = EnterpriseMaterial(
        bid_project_id=request.bid_project_id,
        material_type=request.material_type,
        name=request.name,
        description=request.description,
        contract_amount=request.contract_amount,
        client_name=request.client_name,
        model_number=request.model_number,
        technical_params=request.technical_params
    )
    
    if request.completion_date:
        try:
            material.completion_date = datetime.fromisoformat(request.completion_date)
        except:
            pass
    
    if file:
        file_ext = os.path.splitext(file.filename)[1]
        local_filename = f"{uuid.uuid4()}{file_ext}"
        local_path = os.path.join(settings.upload_dir, "materials", local_filename)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        content = await file.read()
        with open(local_path, "wb") as f:
            f.write(content)
        
        material.file_path = local_path
        material.file_type = file_ext[1:]
        
        try:
            text = TextExtractionService.extract_text_from_file(local_path)
            material.content_text = text
        except Exception as e:
            print(f"文本提取失败: {e}")
    
    db.add(material)
    db.commit()
    db.refresh(material)
    
    if material.content_text:
        rag_service = get_rag_service(db)
        index_result = await rag_service.index_material(material.id)
    
    return {
        "success": True,
        "material_id": material.id,
        "message": "素材上传成功" + ("，已建立索引" if material.content_text else "")
    }


@router.get("/providers/qualifications")
async def get_qualifications_from_provider(
    valid_only: bool = True
):
    """从Provider获取资质列表"""
    providers = get_enterprise_providers()
    qualification_provider = providers.get("qualification")
    
    if not qualification_provider:
        raise HTTPException(status_code=500, detail="Provider未配置")
    
    qualifications = qualification_provider.get_qualifications(valid_only)
    
    return {
        "success": True,
        "qualifications": qualifications,
        "count": len(qualifications)
    }


@router.get("/providers/projects")
async def get_projects_from_provider(
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None
):
    """从Provider获取业绩列表"""
    providers = get_enterprise_providers()
    qualification_provider = providers.get("qualification")
    
    if not qualification_provider:
        raise HTTPException(status_code=500, detail="Provider未配置")
    
    projects = qualification_provider.get_projects(min_amount, max_amount)
    
    return {
        "success": True,
        "projects": projects,
        "count": len(projects)
    }


@router.get("/providers/personnel")
async def get_personnel_from_provider(
    role: Optional[str] = None
):
    """从Provider获取人员列表"""
    providers = get_enterprise_providers()
    hr_provider = providers.get("hr")
    
    if not hr_provider:
        raise HTTPException(status_code=500, detail="Provider未配置")
    
    personnel = hr_provider.get_personnel(role)
    
    return {
        "success": True,
        "personnel": personnel,
        "count": len(personnel)
    }


@router.get("/providers/financial-data")
async def get_financial_data_from_provider(
    year: Optional[int] = None
):
    """从Provider获取财务数据"""
    providers = get_enterprise_providers()
    finance_provider = providers.get("finance")
    
    if not finance_provider:
        raise HTTPException(status_code=500, detail="Provider未配置")
    
    financial_data = finance_provider.get_financial_data(year)
    
    return {
        "success": True,
        "financial_data": financial_data
    }


@router.get("/providers/company-info")
async def get_company_info_from_provider():
    """从Provider获取公司信息"""
    providers = get_enterprise_providers()
    qualification_provider = providers.get("qualification")
    
    if not qualification_provider:
        raise HTTPException(status_code=500, detail="Provider未配置")
    
    company_info = qualification_provider.get_company_info()
    
    return {
        "success": True,
        "company_info": company_info
    }