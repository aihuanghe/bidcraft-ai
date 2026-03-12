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
    
    # 模板提取信息
    has_format_template = Column(Boolean, default=False)  # 是否检测到投标文件格式章节
    format_template_chapter = Column(String(100))  # 格式章节位置，如"第8章"
    extracted_template_id = Column(Integer, ForeignKey("extracted_templates.id"), nullable=True)
    
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
    
    # 模板关联
    template_id = Column(Integer, ForeignKey("extracted_templates.id"), nullable=True)
    template_source = Column(String(20))  # extracted, builtin, custom
    
    # 基于模板生成的大纲
    outline_json = Column(JSON)
    
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
    
    id = Column(Integer, primary_key=True)
    config_key = Column(String(100), unique=True, index=True, nullable=False)
    config_value = Column(Text)
    config_type = Column(String(50))  # string, json, int, float, bool
    
    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ExtractedTemplate(Base):
    """提取的招标文件模板模型"""
    __tablename__ = "extracted_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    source_doc_id = Column(Integer, ForeignKey("tender_documents.id"), nullable=True)
    
    # 模板类型：extracted（提取）vs builtin（内置）vs custom（自定义）
    template_type = Column(String(20), default="extracted")
    
    # 模板名称和描述
    name = Column(String(500))
    description = Column(Text)
    
    # 行业类型
    industry = Column(String(100))  # engineering, it, medical, government等
    
    # 章节树结构（JSON格式）
    structure_json = Column(JSON)
    
    # 样式规则（字体、段落、页面格式）
    style_rules = Column(JSON)
    
    # 原文关键段落备份
    original_snippets = Column(JSON)
    
    # 提取置信度（0-1）
    confidence_score = Column(Float, default=0.0)
    
    # 状态
    is_active = Column(Boolean, default=True)
    
    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联 - 明确指定外键
    source_document = relationship(
        "TenderDocument", 
        backref="extracted_templates",
        foreign_keys=[source_doc_id]
    )


class TemplateDeviation(Base):
    """偏离表映射模型"""
    __tablename__ = "template_deviations"
    
    id = Column(Integer, primary_key=True, index=True)
    bid_project_id = Column(Integer, ForeignKey("bid_projects.id"), nullable=False)
    
    # 偏离表类型
    deviation_type = Column(String(50))  # technical, business
    
    # 招标要求
    tender_requirement = Column(Text)
    
    # 投标响应
    bid_response = Column(Text)
    
    # 偏离类型：none（无偏离）, positive（正偏离）, negative（负偏离）
    deviation_status = Column(String(20), default="none")
    
    # 关联章节号
    chapter_path = Column(String(100))
    chapter_title = Column(String(500))
    
    # 人工确认状态
    is_confirmed = Column(Boolean, default=False)
    
    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    project = relationship("BidProject", backref="deviations")
