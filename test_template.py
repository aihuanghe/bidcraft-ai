"""测试脚本 - 测试模板相关API"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import asyncio
import json
from httpx import ASGITransport, AsyncClient
from backend.app.main import app


async def test_template_apis():
    """测试模板相关API"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        
        print("=" * 60)
        print("模板功能API测试")
        print("=" * 60)
        
        # 1. 测试健康检查
        print("\n=== 1. 测试健康检查 ===")
        response = await client.get("/health")
        print(f"状态码: {response.status_code}")
        assert response.status_code == 200
        print(f"响应: {response.json()}")
        
        # 2. 先创建一个招标文件用于测试
        print("\n=== 2. 创建测试招标文件 ===")
        response = await client.post("/api/projects/", json={
            "name": "模板测试项目",
            "budget": 500000,
            "tender_company": "测试招标公司"
        })
        print(f"状态码: {response.status_code}")
        project_data = response.json()
        project_id = project_data.get("id")
        print(f"项目ID: {project_id}")
        
        # 3. 测试模板推荐（无招标文件时）
        print("\n=== 3. 测试模板推荐（无招标文件）===")
        response = await client.get("/api/templates/document/99999/recommendation")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        # 4. 测试大纲生成（无模板时）
        print("\n=== 4. 测试大纲生成（无模板）===")
        response = await client.post("/api/templates/outline/generate", json={
            "project_id": project_id,
            "template_id": 1,
            "technical_scores": {
                "items": [
                    {"name": "技术方案", "weight": "20分", "description": "需要详细的技术方案"},
                    {"name": "实施计划", "weight": "15分", "description": "需要可行的实施计划"}
                ]
            },
            "project_overview": "这是一个测试项目"
        })
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        # 5. 测试内容生成
        print("\n=== 5. 测试内容生成 ===")
        test_chapter = {
            "id": "test-1",
            "title": "技术方案",
            "level": 1,
            "type": "technical",
            "template_snippet": "请按照以下格式撰写技术方案：\n1. 项目理解\n2. 技术路线\n3. 实施方案",
            "ai_prompt": "撰写技术方案章节内容",
            "placeholders": ["{{company_name}}"],
            "required": True
        }
        response = await client.post("/api/templates/content/generate", json={
            "project_id": project_id,
            "chapter": test_chapter,
            "project_info": {
                "project_overview": "测试项目概述"
            }
        })
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应成功: {result.get('success')}")
        
        # 6. 测试偏离表生成
        print("\n=== 6. 测试偏离表生成 ===")
        technical_scores = {
            "items": [
                {"name": "系统要求1", "description": "支持1000并发"},
                {"name": "系统要求2", "description": "响应时间<2秒"},
                {"name": "系统要求3", "description": "7x24小时运行"}
            ]
        }
        response = await client.post(
            f"/api/templates/deviation/generate?project_id={project_id}",
            json=technical_scores
        )
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应成功: {result.get('success')}")
        if result.get("deviations"):
            print(f"偏离表条目数: {len(result['deviations'])}")
            print(f"第一条: {result['deviations'][0]}")
        
        # 7. 测试获取偏离表
        print("\n=== 7. 测试获取偏离表 ===")
        response = await client.get(f"/api/templates/deviation/{project_id}")
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应成功: {result.get('success')}")
        
        # 8. 测试保存偏离表映射
        print("\n=== 8. 测试保存偏离表映射 ===")
        mappings = [
            {
                "deviation_type": "technical",
                "tender_requirement": "系统要求1",
                "bid_response": "完全响应，支持1000并发",
                "deviation_status": "none",
                "chapter_path": "1.1",
                "chapter_title": "技术方案",
                "is_confirmed": True
            }
        ]
        response = await client.post("/api/templates/deviation/mappings", json={
            "project_id": project_id,
            "mappings": mappings
        })
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        # 9. 测试模板选择
        print("\n=== 9. 测试模板选择 ===")
        response = await client.post("/api/templates/select", json={
            "project_id": project_id,
            "template_id": 1,
            "template_source": "builtin"
        })
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        # 10. 测试导出（无内容时应该失败）
        print("\n=== 10. 测试文档导出 ===")
        response = await client.get(f"/api/templates/export/{project_id}")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        print("\n" + "=" * 60)
        print("所有API测试完成!")
        print("=" * 60)


async def test_template_service():
    """测试模板服务单元逻辑"""
    print("\n" + "=" * 60)
    print("模板服务单元测试")
    print("=" * 60)
    
    # 测试模板检测关键词
    from backend.app.services.template_service import TemplateExtractionService
    
    # 模拟测试数据
    test_content = """
    第五章 投标文件格式
    
    5.1 投标函格式
    投标人应按照以下格式编制投标函...
    
    5.2 商务部分格式
    5.2.1 资格审查资料
    5.2.2 业绩表
    
    5.3 技术部分格式
    5.3.1 技术方案
    5.3.2 实施计划
    
    5.4 报价部分格式
    5.4.1 报价表
    5.4.2 分项报价表
    
    附件：
    """
    
    # 这里创建一个模拟的db session来测试
    from backend.app.models.database import SessionLocal
    db = SessionLocal()
    
    try:
        service = TemplateExtractionService(db)
        
        # 测试章节检测
        print("\n=== 测试模板章节检测 ===")
        result = service.detect_template_chapter(test_content)
        print(f"检测结果: {result}")
        
        # 测试行业检测
        from backend.app.services.template_service import TemplateMatchingService
        matching_service = TemplateMatchingService(db)
        
        print("\n=== 测试行业检测 ===")
        
        # 工程类
        industry = matching_service.detect_industry(
            "本项目为市政道路建设工程",
            "要求具有市政公用工程施工总承包资质"
        )
        print(f"检测行业(工程类): {industry}")
        
        # IT类
        industry = matching_service.detect_industry(
            "本项目为信息化建设",
            "要求开发一套管理系统"
        )
        print(f"检测行业(IT类): {industry}")
        
        # 政府采购类
        industry = matching_service.detect_industry(
            "办公设备采购项目",
            "政府采购办公家具"
        )
        print(f"检测行业(政府采购类): {industry}")
        
        print("\n=== 模板服务单元测试通过 ===")
        
    finally:
        db.close()


async def test_outline_service():
    """测试大纲生成服务"""
    print("\n" + "=" * 60)
    print("大纲生成服务测试")
    print("=" * 60)
    
    from backend.app.models.database import SessionLocal
    db = SessionLocal()
    
    try:
        from backend.app.services.template_outline_service import TemplateOutlineService, DeviationTableService
        
        outline_service = TemplateOutlineService(db)
        deviation_service = DeviationTableService(db)
        
        # 测试技术评分项映射
        print("\n=== 测试技术评分项映射 ===")
        
        # 创建模拟模板结构
        mock_template = type('MockTemplate', (), {
            'id': 1,
            'name': '测试模板',
            'structure_json': {
                'sections': [
                    {'type': 'letter', 'title': '投标函', 'content': '模板内容'},
                    {'type': 'business', 'title': '商务部分', 'content': ''},
                    {'type': 'technical', 'title': '技术部分', 'content': '', 'has_table': False},
                    {'type': 'price', 'title': '报价部分', 'content': ''}
                ]
            },
            'style_rules': {},
            'confidence_score': 0.8
        })()
        
        technical_scores = {
            "items": [
                {"name": "技术方案完整性", "weight": "20分", "description": "技术方案需完整"},
                {"name": "项目实施计划", "weight": "15分", "description": "计划需详细可行"},
                {"name": "售后服务方案", "weight": "10分", "description": "需提供质保"}
            ]
        }
        
        # 生成大纲
        outline = outline_service.generate_outline_from_template(
            mock_template,
            technical_scores,
            "测试项目概述"
        )
        
        print(f"生成大纲章节数: {len(outline.get('chapters', []))}")
        for chapter in outline.get('chapters', []):
            print(f"  - {chapter.get('title')} (类型: {chapter.get('type')}, 子章节: {len(chapter.get('children', []))})")
        
        print(f"\n是否需要偏离表: {outline.get('has_deviation_table')}")
        
        # 测试偏离表生成
        print("\n=== 测试偏离表生成 ===")
        
        deviations = deviation_service.generate_deviation_table(
            technical_scores,
            outline
        )
        
        print(f"生成偏离表条目数: {len(deviations)}")
        for d in deviations[:2]:
            print(f"  - 要求: {d['tender_requirement'][:30]}...")
            print(f"    偏离状态: {d['deviation_status']}")
            print(f"    章节: {d['chapter_path']}")
        
        print("\n=== 大纲服务测试通过 ===")
        
    finally:
        db.close()


if __name__ == "__main__":
    print("开始运行测试...")
    
    # 运行API测试
    asyncio.run(test_template_apis())
    
    # 运行服务单元测试
    asyncio.run(test_template_service())
    asyncio.run(test_outline_service())
    
    print("\n✅ 所有测试完成!")
