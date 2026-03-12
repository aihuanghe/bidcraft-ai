"""模板相关API路由"""
import os
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from ..models.database import get_db
from ..models.models import TenderDocument, BidProject, ExtractedTemplate, TemplateDeviation
from ..services.template_service import get_template_service, get_matching_service
from ..services.template_outline_service import (
    get_outline_service, get_content_service, get_deviation_service
)
from ..services.document_export_service import get_export_service

router = APIRouter(prefix="/api/templates", tags=["模板管理"])


class ExtractTemplateRequest(BaseModel):
    """模板提取请求"""
    document_id: int


class TemplateRecommendationResponse(BaseModel):
    """模板推荐响应"""
    templates: List[Dict[str, Any]]
    recommended_template_id: Optional[int] = None
    confidence: float


class OutlineGenerateRequest(BaseModel):
    """大纲生成请求"""
    project_id: int
    template_id: int
    technical_scores: Dict[str, Any] = {}
    project_overview: str = ""


class ContentGenerateRequest(BaseModel):
    """内容生成请求"""
    project_id: int
    chapter: Dict[str, Any]
    project_info: Dict[str, Any] = {}
    enterprise_data: Optional[Dict[str, Any]] = None
    similar_cases: Optional[List[Dict[str, Any]]] = None


class DeviationMappingRequest(BaseModel):
    """偏离表映射请求"""
    project_id: int
    mappings: List[Dict[str, Any]]


class TemplateSelectRequest(BaseModel):
    """模板选择请求"""
    project_id: int
    template_id: int
    template_source: str  # extracted, builtin, custom


@router.post("/extract")
async def extract_template(
    request: ExtractTemplateRequest,
    db: Session = Depends(get_db)
):
    """从招标文件提取模板"""
    try:
        doc = db.query(TenderDocument).filter(
            TenderDocument.id == request.document_id
        ).first()
        
        if not doc:
            raise HTTPException(status_code=404, detail="招标文件不存在")
        
        if not doc.file_path or not doc.file_path.endswith('.docx'):
            raise HTTPException(status_code=400, detail="仅支持Word文档模板提取")
        
        template_service = get_template_service(db)
        
        template_data = template_service.extract_template_from_docx(doc.file_path)
        
        if not template_data or not template_data.get("detected"):
            return {
                "success": False,
                "message": "未检测到投标文件格式章节",
                "confidence": 0.0
            }
        
        matching_service = get_matching_service(db)
        industry = matching_service.detect_industry(
            doc.project_overview or "",
            doc.technical_requirements or ""
        )
        
        template = template_service.save_extracted_template(
            request.document_id,
            template_data,
            industry
        )
        
        template_service.update_document_template_flag(
            request.document_id,
            template.id,
            template_data.get("chapter_info", {}).get("chapter", "")
        )
        
        return {
            "success": True,
            "message": "模板提取成功",
            "template_id": template.id,
            "template_name": template.name,
            "confidence": template.confidence_score,
            "sections_count": len(template_data.get("sections", []))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模板提取失败: {str(e)}")


@router.get("/document/{document_id}/recommendation")
async def get_template_recommendation(
    document_id: int,
    db: Session = Depends(get_db)
):
    """获取模板推荐"""
    try:
        doc = db.query(TenderDocument).filter(
            TenderDocument.id == document_id
        ).first()
        
        if not doc:
            raise HTTPException(status_code=404, detail="招标文件不存在")
        
        matching_service = get_matching_service(db)
        template_service = get_template_service(db)
        
        industry = matching_service.detect_industry(
            doc.project_overview or "",
            doc.technical_requirements or ""
        )
        
        technical_scores = {}
        if doc.technical_requirements:
            import json
            try:
                technical_scores = json.loads(doc.technical_requirements)
            except:
                technical_scores = {"items": []}
        
        templates = []
        
        if doc.extracted_template_id:
            extracted_template = template_service.get_extracted_template(doc.extracted_template_id)
            if extracted_template:
                match_result = matching_service.calculate_match_score(
                    extracted_template, industry, technical_scores
                )
                templates.append({
                    "id": extracted_template.id,
                    "name": extracted_template.name,
                    "type": "extracted",
                    "score": match_result["score"],
                    "reasons": match_result["reasons"],
                    "recommendation": match_result["recommendation"]
                })
        
        builtin_templates = db.query(ExtractedTemplate).filter(
            ExtractedTemplate.template_type == "builtin",
            ExtractedTemplate.is_active == True
        ).all()
        
        for template in builtin_templates:
            match_result = matching_service.calculate_match_score(
                template, industry, technical_scores
            )
            templates.append({
                "id": template.id,
                "name": template.name,
                "type": "builtin",
                "score": match_result["score"],
                "reasons": match_result["reasons"],
                "recommendation": match_result["recommendation"]
            })
        
        templates.sort(key=lambda x: x["score"], reverse=True)
        
        recommended = templates[0] if templates else None
        
        return {
            "templates": templates,
            "recommended_template_id": recommended["id"] if recommended else None,
            "confidence": recommended["score"] if recommended else 0.0,
            "industry": industry
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取推荐失败: {str(e)}")


@router.post("/select")
async def select_template(
    request: TemplateSelectRequest,
    db: Session = Depends(get_db)
):
    """为项目选择模板"""
    try:
        project = db.query(BidProject).filter(
            BidProject.id == request.project_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        template = db.query(ExtractedTemplate).filter(
            ExtractedTemplate.id == request.template_id
        ).first()
        
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        project.template_id = request.template_id
        project.template_source = request.template_source
        
        db.commit()
        
        return {
            "success": True,
            "message": "模板选择成功",
            "project_id": project.id,
            "template_id": template.id,
            "template_name": template.name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模板选择失败: {str(e)}")


@router.post("/outline/generate")
async def generate_outline(
    request: OutlineGenerateRequest,
    db: Session = Depends(get_db)
):
    """基于模板生成大纲"""
    try:
        template = db.query(ExtractedTemplate).filter(
            ExtractedTemplate.id == request.template_id
        ).first()
        
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        outline_service = get_outline_service(db)
        
        outline = await outline_service.generate_outline_with_ai(
            template,
            request.technical_scores,
            request.project_overview
        )
        
        project = db.query(BidProject).filter(
            BidProject.id == request.project_id
        ).first()
        
        if project:
            project.outline_json = outline
            db.commit()
        
        return {
            "success": True,
            "outline": outline
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"大纲生成失败: {str(e)}")


@router.post("/content/generate")
async def generate_content(
    request: ContentGenerateRequest,
    db: Session = Depends(get_db)
):
    """生成章节内容（模板驱动）"""
    try:
        content_service = get_content_service(db)
        
        content = await content_service.generate_chapter_content(
            request.chapter,
            request.project_info,
            request.enterprise_data,
            request.similar_cases
        )
        
        return {
            "success": True,
            "content": content,
            "chapter_id": request.chapter.get("id")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"内容生成失败: {str(e)}")


@router.post("/content/generate-stream")
async def generate_content_stream(
    request: ContentGenerateRequest,
    db: Session = Depends(get_db)
):
    """流式生成章节内容"""
    from fastapi.responses import StreamingResponse
    import json
    
    content_service = get_content_service(db)
    
    async def generate():
        try:
            async for chunk in content_service.generate_chapter_content_stream(
                request.chapter,
                request.project_info,
                request.enterprise_data,
                request.similar_cases
            ):
                yield f"data: {json.dumps({'chunk': chunk}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/deviation/generate")
async def generate_deviation_table(
    project_id: int,
    technical_scores: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """生成偏离表"""
    try:
        project = db.query(BidProject).filter(
            BidProject.id == project_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        deviation_service = get_deviation_service(db)
        
        outline = project.outline_json or {}
        
        deviations = deviation_service.generate_deviation_table(
            technical_scores,
            outline
        )
        
        return {
            "success": True,
            "deviations": deviations,
            "count": len(deviations)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"偏离表生成失败: {str(e)}")


@router.post("/deviation/mappings")
async def save_deviation_mappings(
    request: DeviationMappingRequest,
    db: Session = Depends(get_db)
):
    """保存偏离表映射"""
    try:
        project = db.query(BidProject).filter(
            BidProject.id == request.project_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        db.query(TemplateDeviation).filter(
            TemplateDeviation.bid_project_id == request.project_id
        ).delete()
        
        for mapping in request.mappings:
            deviation = TemplateDeviation(
                bid_project_id=request.project_id,
                deviation_type=mapping.get("deviation_type", "technical"),
                tender_requirement=mapping.get("tender_requirement", ""),
                bid_response=mapping.get("bid_response", ""),
                deviation_status=mapping.get("deviation_status", "none"),
                chapter_path=mapping.get("chapter_path", ""),
                chapter_title=mapping.get("chapter_title", ""),
                is_confirmed=mapping.get("is_confirmed", False)
            )
            db.add(deviation)
        
        db.commit()
        
        return {
            "success": True,
            "message": "偏离表保存成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")


@router.get("/deviation/{project_id}")
async def get_deviation_table(
    project_id: int,
    db: Session = Depends(get_db)
):
    """获取偏离表"""
    try:
        deviations = db.query(TemplateDeviation).filter(
            TemplateDeviation.bid_project_id == project_id
        ).all()
        
        return {
            "success": True,
            "deviations": [
                {
                    "id": d.id,
                    "deviation_type": d.deviation_type,
                    "tender_requirement": d.tender_requirement,
                    "bid_response": d.bid_response,
                    "deviation_status": d.deviation_status,
                    "chapter_path": d.chapter_path,
                    "chapter_title": d.chapter_title,
                    "is_confirmed": d.is_confirmed
                }
                for d in deviations
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取偏离表失败: {str(e)}")


@router.get("/export/{project_id}")
async def export_document(
    project_id: int,
    format: str = "docx",
    db: Session = Depends(get_db)
):
    """导出投标文档"""
    try:
        project = db.query(BidProject).filter(
            BidProject.id == project_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        if not project.outline_json:
            raise HTTPException(status_code=400, detail="请先生成大纲")
        
        outline = project.outline_json
        
        contents = {}
        for chapter in outline.get("chapters", []):
            self._collect_contents(chapter, contents)
        
        template = None
        if project.template_id:
            template = db.query(ExtractedTemplate).filter(
                ExtractedTemplate.id == project.template_id
            ).first()
        
        export_service = get_export_service(db)
        output_path = export_service.export_bid_document(
            project, outline, contents
        )
        
        if format == "pdf":
            import subprocess
            pdf_path = output_path.replace(".docx", ".pdf")
            try:
                subprocess.run([
                    "libreoffice", "--headless", "--convert-to", "pdf",
                    "--outdir", os.path.dirname(output_path),
                    output_path
                ], check=True)
                return {"success": True, "file_path": pdf_path}
            except:
                return {"success": True, "file_path": output_path, "warning": "PDF转换失败，返回DOCX"}
        
        return {
            "success": True,
            "file_path": output_path
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


def _collect_contents(chapter: Dict[str, Any], contents: Dict[str, str]):
    """递归收集章节内容"""
    chapter_id = chapter.get("id", "")
    if chapter.get("content"):
        contents[chapter_id] = chapter["content"]
    
    for child in chapter.get("children", []):
        _collect_contents(child, contents)