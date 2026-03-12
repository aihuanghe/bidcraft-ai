"""基于模板的大纲生成服务"""
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session

from ..models.models import BidProject, ExtractedTemplate, DocumentOutline
from ..services.openai_service import OpenAIService
from ..utils.config_manager import config_manager


class TemplateOutlineService:
    """基于模板的大纲生成服务"""
    
    CHAPTER_TEMPLATE_MAPPING = {
        "letter": "投标函",
        "business": "商务部分",
        "technical": "技术部分",
        "price": "报价部分"
    }
    
    def __init__(self, db: Session):
        self.db = db
        self.openai_service = OpenAIService()
    
    def generate_outline_from_template(
        self,
        template: ExtractedTemplate,
        technical_scores: Dict[str, Any],
        project_overview: str = ""
    ) -> Dict[str, Any]:
        """基于模板生成大纲
        
        Args:
            template: 提取的模板
            technical_scores: 技术评分要求（从招标文件解析得到）
            project_overview: 项目概述
        
        Returns:
            大纲JSON结构
        """
        structure = template.structure_json or {}
        sections = structure.get("sections", [])
        
        outline = {
            "template_id": template.id,
            "template_name": template.name,
            "generated_at": datetime.now().isoformat(),
            "chapters": []
        }
        
        for section in sections:
            chapter = self._build_chapter_from_section(
                section,
                technical_scores,
                project_overview
            )
            if chapter:
                outline["chapters"].append(chapter)
        
        outline["has_deviation_table"] = self._check_deviation_requirement(technical_scores)
        
        return outline
    
    def _build_chapter_from_section(
        self,
        section: Dict[str, Any],
        technical_scores: Dict[str, Any],
        project_overview: str
    ) -> Optional[Dict[str, Any]]:
        """根据模板章节构建大纲项"""
        section_type = section.get("type", "other")
        title = section.get("title", "")
        
        chapter = {
            "id": str(uuid.uuid4())[:8],
            "chapter_id": "",
            "title": title or self.CHAPTER_TEMPLATE_MAPPING.get(section_type, "其他章节"),
            "level": 1,
            "type": section_type,
            "template_snippet": section.get("content", ""),
            "ai_prompt": "",
            "placeholders": self._extract_placeholders(section),
            "required": True,
            "children": []
        }
        
        if section_type == "technical":
            tech_items = technical_scores.get("items", [])
            for idx, item in enumerate(tech_items):
                child_chapter = {
                    "id": str(uuid.uuid4())[:8],
                    "chapter_id": f"{chapter['id']}.{idx + 1}",
                    "title": item.get("name", f"技术要求{idx + 1}"),
                    "level": 2,
                    "type": "technical_item",
                    "template_snippet": "",
                    "ai_prompt": self._build_technical_item_prompt(item, project_overview),
                    "placeholders": [],
                    "required": True,
                    "content_source": "ai_generated"
                }
                chapter["children"].append(child_chapter)
        
        if section.get("has_table"):
            chapter["has_table"] = True
            chapter["table_format"] = self._infer_table_format(section)
        
        return chapter
    
    def _extract_placeholders(self, section: Dict[str, Any]) -> List[str]:
        """从模板章节提取占位符"""
        placeholders = []
        content = section.get("content", "")
        
        common_placeholders = [
            "{{company_name}}", "{{project_name}}", "{{bid_amount}}",
            "{{bid_date}}", "{{contact_person}}", "{{contact_phone}}",
            "{{authorized_signatory}}"
        ]
        
        for ph in common_placeholders:
            if ph.replace("{{", "").replace("}}", "") in content.lower():
                placeholders.append(ph)
        
        return placeholders
    
    def _build_technical_item_prompt(self, item: Dict[str, Any], project_overview: str) -> str:
        """构建技术评分项的AI生成提示"""
        prompt = f"请根据以下招标要求撰写技术响应内容：\n\n"
        
        if project_overview:
            prompt += f"项目概述：{project_overview}\n\n"
        
        prompt += f"招标要求：{item.get('name', '')}\n"
        if item.get("weight"):
            prompt += f"评分权重：{item.get('weight')}\n"
        if item.get("description"):
            prompt += f"详细要求：{item.get('description')}\n"
        
        prompt += "\n请确保内容专业、详实，符合投标文件格式要求。"
        
        return prompt
    
    def _infer_table_format(self, section: Dict[str, Any]) -> Dict[str, Any]:
        """推断表格格式"""
        content = section.get("content", "")
        
        table_format = {
            "columns": [],
            "required_fields": [],
            "sample_data": []
        }
        
        if "业绩" in content or "业绩表" in content:
            table_format["columns"] = ["序号", "项目名称", "合同金额", "完成时间", "业主单位"]
            table_format["required_fields"] = ["项目名称", "合同金额", "完成时间"]
        
        elif "财务" in content or "财务表" in content:
            table_format["columns"] = ["指标", "数值", "说明"]
            table_format["required_fields"] = ["指标", "数值"]
        
        elif "报价" in content or "报价表" in content:
            table_format["columns"] = ["序号", "项目名称", "单位", "数量", "单价", "总价"]
            table_format["required_fields"] = ["项目名称", "单价", "总价"]
        
        return table_format
    
    def _check_deviation_requirement(self, technical_scores: Dict[str, Any]) -> bool:
        """检测是否需要偏离表"""
        text = json.dumps(technical_scores)
        deviation_keywords = ["偏离表", "技术偏离", "商务偏离", "点对点应答", "响应表"]
        
        return any(kw in text for kw in deviation_keywords)
    
    async def generate_outline_with_ai(
        self,
        template: ExtractedTemplate,
        technical_scores: Dict[str, Any],
        project_overview: str
    ) -> Dict[str, Any]:
        """使用AI增强大纲生成"""
        config = config_manager.load_config()
        if not config.get('api_key'):
            return self.generate_outline_from_template(
                template, technical_scores, project_overview
            )
        
        structure = template.structure_json or {}
        sections = structure.get("sections", [])
        
        system_prompt = """你是一名专业投标方案撰写专家。根据以下模板结构和技术评分要求，生成符合招标文件格式的大纲。
请严格按照模板章节顺序，确保技术评分项正确映射到对应章节。"""
        
        user_prompt = f"""请基于以下模板结构生成大纲：

模板章节结构：
{json.dumps(sections, ensure_ascii=False)}

技术评分要求：
{json.dumps(technical_scores, ensure_ascii=False)}

项目概述：
{project_overview}

请返回JSON格式的大纲，包含：
1. 完整的章节树结构
2. 每个章节的模板片段（来自招标文件）
3. 需要AI生成的内容标记
4. 占位符列表"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            full_content = ""
            async for chunk in self.openai_service.stream_chat_completion(
                messages, 
                temperature=0.7,
                response_format={"type": "json_object"}
            ):
                full_content += chunk
            
            ai_outline = json.loads(full_content)
            return ai_outline
        except Exception as e:
            print(f"AI增强大纲生成失败，使用基础模板: {e}")
            return self.generate_outline_from_template(
                template, technical_scores, project_overview
            )


class ContentGenerationService:
    """模板驱动的内容生成服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.openai_service = OpenAIService()
    
    async def generate_chapter_content(
        self,
        chapter: Dict[str, Any],
        project_info: Dict[str, Any],
        enterprise_data: Dict[str, Any] = None,
        similar_cases: List[Dict[str, Any]] = None
    ) -> str:
        """生成章节内容
        
        Args:
            chapter: 章节信息（包含模板片段、AI提示等）
            project_info: 项目信息
            enterprise_data: 企业数据（资质、业绩等）
            similar_cases: 相似案例（RAG检索结果）
        
        Returns:
            生成的章节内容
        """
        config = config_manager.load_config()
        if not config.get('api_key'):
            return self._generate_fallback_content(chapter, project_info)
        
        system_prompt = self._build_system_prompt(chapter)
        user_prompt = self._build_user_prompt(
            chapter, project_info, enterprise_data, similar_cases
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            content = await self.openai_service.chat_completion(
                messages,
                temperature=0.7
            )
            return content
        except Exception as e:
            print(f"内容生成失败: {e}")
            return self._generate_fallback_content(chapter, project_info)
    
    async def generate_chapter_content_stream(
        self,
        chapter: Dict[str, Any],
        project_info: Dict[str, Any],
        enterprise_data: Dict[str, Any] = None,
        similar_cases: List[Dict[str, Any]] = None
    ):
        """流式生成章节内容"""
        config = config_manager.load_config()
        if not config.get('api_key'):
            content = self._generate_fallback_content(chapter, project_info)
            yield content
            return
        
        system_prompt = self._build_system_prompt(chapter)
        user_prompt = self._build_user_prompt(
            chapter, project_info, enterprise_data, similar_cases
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        async for chunk in self.openai_service.stream_chat_completion(
            messages,
            temperature=0.7
        ):
            yield chunk
    
    def _build_system_prompt(self, chapter: Dict[str, Any]) -> str:
        """构建系统提示"""
        template_snippet = chapter.get("template_snippet", "")
        
        prompt = "你是一名专业投标方案撰写专家。严格按照给定格式撰写内容。\n"
        
        if template_snippet:
            prompt += f"\n请参考以下模板格式：\n{template_snippet[:500]}"
        
        if chapter.get("type") == "letter":
            prompt += "\n投标函需包含：致函单位、项目名称、投标报价、投标承诺、签署信息。"
        elif chapter.get("type") == "technical":
            prompt += "\n技术部分需详细响应招标要求，突出企业优势。"
        
        return prompt
    
    def _build_user_prompt(
        self,
        chapter: Dict[str, Any],
        project_info: Dict[str, Any],
        enterprise_data: Dict[str, Any],
        similar_cases: List[Dict[str, Any]]
    ) -> str:
        """构建用户提示"""
        prompt = f"请生成以下章节内容：\n\n"
        
        prompt += f"章节标题：{chapter.get('title', '')}\n"
        
        if chapter.get("ai_prompt"):
            prompt += f"\n生成要求：{chapter['ai_prompt']}\n"
        
        if project_info.get("project_overview"):
            prompt += f"\n项目概述：{project_info['project_overview'][:500]}\n"
        
        if enterprise_data:
            prompt += f"\n企业信息：\n"
            if enterprise_data.get("qualifications"):
                prompt += f"资质：{', '.join(enterprise_data['qualifications'][:5])}\n"
            if enterprise_data.get("projects"):
                prompt += f"相关业绩：{len(enterprise_data['projects'])}个\n"
        
        if similar_cases:
            prompt += f"\n相似案例参考：\n"
            for case in similar_cases[:3]:
                prompt += f"- {case.get('title', '')}: {case.get('summary', '')[:100]}\n"
        
        placeholders = chapter.get("placeholders", [])
        if placeholders:
            prompt += f"\n请注意以下占位符需要在最终文档中替换：\n"
            for ph in placeholders:
                prompt += f"- {ph}\n"
        
        return prompt
    
    def _generate_fallback_content(self, chapter: Dict[str, Any], project_info: Dict[str, Any]) -> str:
        """生成备用内容（无API时）"""
        title = chapter.get("title", "")
        
        fallback = f"# {title}\n\n"
        fallback += f"（此内容为自动生成，请根据实际情况修改）\n\n"
        
        if chapter.get("template_snippet"):
            fallback += f"## 格式参考\n{chapter['template_snippet'][:300]}\n\n"
        
        fallback += f"## 待生成内容\n"
        fallback += f"请根据招标要求和项目信息填充具体内容。"
        
        return fallback


class DeviationTableService:
    """偏离表生成服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_deviation_table(
        self,
        technical_scores: Dict[str, Any],
        outline: Dict[str, Any],
        enterprise_data: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """生成偏离表
        
        Args:
            technical_scores: 技术评分要求
            outline: 生成的大纲
            enterprise_data: 企业数据
        
        Returns:
            偏离表数据列表
        """
        deviations = []
        
        tech_items = technical_scores.get("items", [])
        
        for idx, item in enumerate(tech_items):
            requirement = item.get("name", "")
            description = item.get("description", "")
            
            chapter_match = self._find_matching_chapter(requirement, outline)
            
            deviation_status = self._evaluate_deviation(
                requirement,
                description,
                enterprise_data
            )
            
            deviation = {
                "id": idx + 1,
                "tender_requirement": requirement,
                "tender_description": description,
                "bid_response": self._generate_bid_response(
                    requirement,
                    deviation_status,
                    enterprise_data
                ),
                "deviation_status": deviation_status,
                "chapter_path": chapter_match.get("chapter_path", ""),
                "chapter_title": chapter_match.get("title", ""),
                "is_confirmed": deviation_status == "none"
            }
            
            deviations.append(deviation)
        
        return deviations
    
    def _find_matching_chapter(
        self,
        requirement: str,
        outline: Dict[str, Any]
    ) -> Dict[str, Any]:
        """查找匹配的大纲章节"""
        chapters = outline.get("chapters", [])
        
        for chapter in chapters:
            if chapter.get("type") == "technical":
                for child in chapter.get("children", []):
                    if requirement.lower() in child.get("title", "").lower():
                        return {
                            "chapter_path": child.get("chapter_id", ""),
                            "title": child.get("title", "")
                        }
        
        return {"chapter_path": "", "title": ""}
    
    def _evaluate_deviation(
        self,
        requirement: str,
        description: str,
        enterprise_data: Dict[str, Any]
    ) -> str:
        """评估偏离类型"""
        if not enterprise_data:
            return "none"
        
        requirement_lower = requirement.lower()
        
        required_keywords = ["要求", "必须", "应", "需"]
        if not any(kw in requirement_lower for kw in required_keywords):
            return "none"
        
        return "none"
    
    def _generate_bid_response(
        self,
        requirement: str,
        deviation_status: str,
        enterprise_data: Dict[str, Any]
    ) -> str:
        """生成投标响应"""
        if deviation_status == "negative":
            return "部分响应，具体内容待补充"
        elif deviation_status == "positive":
            return "完全响应，且高于招标要求"
        else:
            return "完全响应招标要求"


def get_outline_service(db: Session) -> TemplateOutlineService:
    """获取大纲生成服务实例"""
    return TemplateOutlineService(db)


def get_content_service(db: Session) -> ContentGenerationService:
    """获取内容生成服务实例"""
    return ContentGenerationService(db)


def get_deviation_service(db: Session) -> DeviationTableService:
    """获取偏离表服务实例"""
    return DeviationTableService(db)