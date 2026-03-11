from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from ..models.database import Base


class TenderDocument(Base):
    """招标文件文档模型"""
    __tablename__ = "tender_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_type = Column(String(50))  # docx, pdf
    file_size = Column(Integer)  # 字节
    
    # 文档内容
    content = Column(Text)
    
    # AI分析结果
    project_overview = Column(Text)  # 项目概述
    technical_requirements = Column(Text)  # 技术评分要求
    
    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    
    # 关联
    outlines = relationship("DocumentOutline", back_populates="document", cascade="all, delete-orphan")


class BidProject(Base):
    """投标项目模型"""
    __tablename__ = "bid_projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False)  # 项目名称
    tender_document_id = Column(Integer, ForeignKey("tender_documents.id"), nullable=True)
    
    # 项目信息
    project_overview = Column(Text)  # 项目概述
    budget = Column(Float)  # 预算金额
    deadline = Column(DateTime)  # 投标截止时间
    
    # 招标方信息
    tender_company = Column(String(500))  # 招标单位
    tender_contact = Column(String(200))  # 联系人
    tender_phone = Column(String(50))  # 联系电话
    
    # 状态
    status = Column(String(50), default="draft")  # draft, in_progress, submitted, won, lost
    progress = Column(Integer, default=0)  # 完成进度 0-100
    
    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    
    # 关联
    tender_document = relationship("TenderDocument", backref="projects")
    outlines = relationship("DocumentOutline", back_populates="project", cascade="all, delete-orphan")
    enterprise_materials = relationship("EnterpriseMaterial", back_populates="project")


class EnterpriseMaterial(Base):
    """企业资料模型"""
    __tablename__ = "enterprise_materials"
    
    id = Column(Integer, primary_key=True, index=True)
    bid_project_id = Column(Integer, ForeignKey("bid_projects.id"), nullable=True)
    
    # 资料类型
    material_type = Column(String(100))  # business_license, certificate, qualification, etc.
    
    # 资料信息
    name = Column(String(500), nullable=False)  # 资料名称
    description = Column(Text)  # 资料描述
    
    # 文件存储
    file_path = Column(String(1000))  # 本地路径
    minio_object_name = Column(String(1000))  # MinIO对象名
    file_url = Column(String(2000))  # 文件访问URL
    
    # 过期信息
    issue_date = Column(DateTime)  # 发证日期
    expiry_date = Column(DateTime)  # 过期日期
    is_expired = Column(Boolean, default=False)
    
    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    
    # 关联
    project = relationship("BidProject", back_populates="enterprise_materials")


class DocumentOutline(Base):
    """文档大纲模型"""
    __tablename__ = "document_outlines"
    
    id = Column(Integer, primary_key=True, index=True)
    tender_document_id = Column(Integer, ForeignKey("tender_documents.id"), nullable=True)
    bid_project_id = Column(Integer, ForeignKey("bid_projects.id"), nullable=True)
    
    # 大纲结构（JSON格式存储树形结构）
    outline_data = Column(JSON)
    
    # 版本管理
    version = Column(Integer, default=1)
    is_current = Column(Boolean, default=True)
    
    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    document = relationship("TenderDocument", back_populates="outlines")
    project = relationship("BidProject", back_populates="outlines")
    contents = relationship("DocumentContent", back_populates="outline", cascade="all, delete-orphan")


class DocumentContent(Base):
    """文档内容模型"""
    __tablename__ = "document_contents"
    
    id = Column(Integer, primary_key=True, index=True)
    outline_id = Column(Integer, ForeignKey("document_outlines.id"), nullable=False)
    
    # 章节路径（如 "1.2.3"）
    chapter_path = Column(String(100))
    chapter_title = Column(String(500))
    
    # 内容
    content = Column(Text)
    
    # AI生成信息
    is_ai_generated = Column(Boolean, default=False)
    generation_prompt = Column(Text)
    generation_model = Column(String(100))
    
    # 字数统计
    word_count = Column(Integer, default=0)
    
    # 状态
    is_approved = Column(Boolean, default=False)
    approval_note = Column(Text)
    
    # 向量嵌入ID（用于语义检索）
    vector_id = Column(String(100))
    
    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    outline = relationship("DocumentOutline", back_populates="contents")


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(200), unique=True, index=True)
    hashed_password = Column(String(200), nullable=False)
    
    # 用户信息
    full_name = Column(String(200))
    company = Column(String(500))  # 公司名称
    phone = Column(String(50))
    
    # 状态
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    search_histories = relationship("SearchHistory", back_populates="user")


class SearchHistory(Base):
    """搜索历史模型"""
    __tablename__ = "search_histories"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 搜索内容
    query = Column(Text, nullable=False)
    search_type = Column(String(50))  # web, document, semantic
    
    # 搜索结果摘要
    results_count = Column(Integer, default=0)
    results_summary = Column(JSON)
    
    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联
    user = relationship("User", back_populates="search_histories")


class AppConfig(Base):
    """应用配置模型"""
    __tablename__ = "app_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(100), unique=True, index=True, nullable=False)
    config_value = Column(Text)
    config_type = Column(String(50))  # string, json, int, float, bool
    
    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
