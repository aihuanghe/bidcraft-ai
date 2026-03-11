"""项目相关API路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..models.database import get_db
from ..models.models import BidProject, TenderDocument

router = APIRouter(prefix="/api/projects", tags=["项目管理"])


class BidProjectCreate(BaseModel):
    """创建项目请求"""
    name: str
    tender_document_id: Optional[int] = None
    project_overview: Optional[str] = None
    budget: Optional[float] = None
    deadline: Optional[datetime] = None
    tender_company: Optional[str] = None
    tender_contact: Optional[str] = None
    tender_phone: Optional[str] = None


class BidProjectResponse(BaseModel):
    """项目响应"""
    id: int
    name: str
    tender_document_id: Optional[int]
    project_overview: Optional[str]
    budget: Optional[float]
    deadline: Optional[datetime]
    tender_company: Optional[str]
    tender_contact: Optional[str]
    tender_phone: Optional[str]
    status: str
    progress: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BidProjectUpdate(BaseModel):
    """更新项目请求"""
    name: Optional[str] = None
    project_overview: Optional[str] = None
    budget: Optional[float] = None
    deadline: Optional[datetime] = None
    tender_company: Optional[str] = None
    tender_contact: Optional[str] = None
    tender_phone: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[int] = None


@router.post("/", response_model=BidProjectResponse)
async def create_project(
    project: BidProjectCreate,
    db: Session = Depends(get_db)
):
    """创建新项目"""
    db_project = BidProject(
        name=project.name,
        tender_document_id=project.tender_document_id,
        project_overview=project.project_overview,
        budget=project.budget,
        deadline=project.deadline,
        tender_company=project.tender_company,
        tender_contact=project.tender_contact,
        tender_phone=project.tender_phone,
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@router.get("/", response_model=List[BidProjectResponse])
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取项目列表"""
    query = db.query(BidProject).filter(BidProject.is_deleted == False)
    if status:
        query = query.filter(BidProject.status == status)
    projects = query.offset(skip).limit(limit).all()
    return projects


@router.get("/{project_id}", response_model=BidProjectResponse)
async def get_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    """获取项目详情"""
    project = db.query(BidProject).filter(
        BidProject.id == project_id,
        BidProject.is_deleted == False
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


@router.put("/{project_id}", response_model=BidProjectResponse)
async def update_project(
    project_id: int,
    project: BidProjectUpdate,
    db: Session = Depends(get_db)
):
    """更新项目"""
    db_project = db.query(BidProject).filter(BidProject.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    update_data = project.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_project, field, value)
    
    db_project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_project)
    return db_project


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    """删除项目"""
    db_project = db.query(BidProject).filter(BidProject.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    db_project.is_deleted = True
    db_project.updated_at = datetime.utcnow()
    db.commit()
    return {"success": True, "message": "项目已删除"}
