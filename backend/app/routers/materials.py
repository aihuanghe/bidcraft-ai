"""企业资料相关API路由"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import os
import uuid

from ..models.database import get_db
from ..models.models import EnterpriseMaterial
from ..config import settings
from ..services.minio_service import minio_service

router = APIRouter(prefix="/api/materials", tags=["企业资料"])


class EnterpriseMaterialCreate(BaseModel):
    """创建资料请求"""
    bid_project_id: Optional[int] = None
    material_type: str
    name: str
    description: Optional[str] = None
    issue_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None


class EnterpriseMaterialResponse(BaseModel):
    """资料响应"""
    id: int
    bid_project_id: Optional[int]
    material_type: str
    name: str
    description: Optional[str]
    file_path: Optional[str]
    minio_object_name: Optional[str]
    file_url: Optional[str]
    issue_date: Optional[datetime]
    expiry_date: Optional[datetime]
    is_expired: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EnterpriseMaterialUpdate(BaseModel):
    """更新资料请求"""
    material_type: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    issue_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None


@router.post("/", response_model=EnterpriseMaterialResponse)
async def create_material(
    material: EnterpriseMaterialCreate,
    db: Session = Depends(get_db)
):
    """创建新资料记录"""
    db_material = EnterpriseMaterial(
        bid_project_id=material.bid_project_id,
        material_type=material.material_type,
        name=material.name,
        description=material.description,
        issue_date=material.issue_date,
        expiry_date=material.expiry_date,
    )
    
    if material.expiry_date and material.expiry_date < datetime.utcnow():
        db_material.is_expired = True
    
    db.add(db_material)
    db.commit()
    db.refresh(db_material)
    return db_material


@router.post("/upload/{material_id}")
async def upload_material_file(
    material_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传资料文件"""
    db_material = db.query(EnterpriseMaterial).filter(
        EnterpriseMaterial.id == material_id
    ).first()
    
    if not db_material:
        raise HTTPException(status_code=404, detail="资料不存在")
    
    # 保存到本地
    file_ext = os.path.splitext(file.filename)[1]
    local_filename = f"{uuid.uuid4()}{file_ext}"
    local_path = os.path.join(settings.upload_dir, "materials", local_filename)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    
    content = await file.read()
    with open(local_path, "wb") as f:
        f.write(content)
    
    db_material.file_path = local_path
    db_material.updated_at = datetime.utcnow()
    db.commit()
    
    # 上传到MinIO（如果可用）
    try:
        object_name = f"materials/{material_id}/{local_filename}"
        minio_url = await minio_service.upload_file(
            file_path=local_path,
            object_name=object_name,
            content_type=file.content_type
        )
        db_material.minio_object_name = object_name
        db_material.file_url = minio_url
        db.commit()
    except Exception as e:
        print(f"MinIO上传失败: {e}")
    
    db.refresh(db_material)
    return {
        "success": True,
        "material": db_material,
        "file_url": db_material.file_url
    }


@router.get("/", response_model=List[EnterpriseMaterialResponse])
async def list_materials(
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[int] = None,
    material_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取资料列表"""
    query = db.query(EnterpriseMaterial).filter(EnterpriseMaterial.is_deleted == False)
    
    if project_id:
        query = query.filter(EnterpriseMaterial.bid_project_id == project_id)
    if material_type:
        query = query.filter(EnterpriseMaterial.material_type == material_type)
    
    materials = query.offset(skip).limit(limit).all()
    return materials


@router.get("/{material_id}", response_model=EnterpriseMaterialResponse)
async def get_material(
    material_id: int,
    db: Session = Depends(get_db)
):
    """获取资料详情"""
    material = db.query(EnterpriseMaterial).filter(
        EnterpriseMaterial.id == material_id,
        EnterpriseMaterial.is_deleted == False
    ).first()
    if not material:
        raise HTTPException(status_code=404, detail="资料不存在")
    return material


@router.put("/{material_id}", response_model=EnterpriseMaterialResponse)
async def update_material(
    material_id: int,
    material: EnterpriseMaterialUpdate,
    db: Session = Depends(get_db)
):
    """更新资料"""
    db_material = db.query(EnterpriseMaterial).filter(
        EnterpriseMaterial.id == material_id
    ).first()
    
    if not db_material:
        raise HTTPException(status_code=404, detail="资料不存在")
    
    update_data = material.model_dump(exclude_unset=True)
    
    if "expiry_date" in update_data and update_data["expiry_date"]:
        update_data["is_expired"] = update_data["expiry_date"] < datetime.utcnow()
    
    for field, value in update_data.items():
        setattr(db_material, field, value)
    
    db_material.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_material)
    return db_material


@router.delete("/{material_id}")
async def delete_material(
    material_id: int,
    db: Session = Depends(get_db)
):
    """删除资料"""
    db_material = db.query(EnterpriseMaterial).filter(
        EnterpriseMaterial.id == material_id
    ).first()
    
    if not db_material:
        raise HTTPException(status_code=404, detail="资料不存在")
    
    db_material.is_deleted = True
    db_material.updated_at = datetime.utcnow()
    db.commit()
    return {"success": True, "message": "资料已删除"}
