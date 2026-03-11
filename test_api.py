"""测试脚本 - 测试新增的API"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import asyncio
from httpx import ASGITransport, AsyncClient
from backend.app.main import app


async def test_apis():
    """测试API"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        
        # 测试健康检查
        print("=== 测试健康检查 ===")
        response = await client.get("/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        # 测试创建项目
        print("\n=== 测试创建项目 ===")
        response = await client.post("/api/projects/", json={
            "name": "测试项目",
            "budget": 100000,
            "tender_company": "测试公司"
        })
        print(f"状态码: {response.status_code}")
        project_data = response.json()
        print(f"响应: {project_data}")
        project_id = project_data.get("id")
        
        # 测试获取项目列表
        print("\n=== 测试获取项目列表 ===")
        response = await client.get("/api/projects/")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        # 测试获取单个项目
        if project_id:
            print(f"\n=== 测试获取项目 {project_id} ===")
            response = await client.get(f"/api/projects/{project_id}")
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.json()}")
        
        # 测试创建资料
        print("\n=== 测试创建资料 ===")
        response = await client.post("/api/materials/", json={
            "material_type": "business_license",
            "name": "营业执照",
            "description": "企业营业执照",
            "bid_project_id": project_id
        })
        print(f"状态码: {response.status_code}")
        material_data = response.json()
        print(f"响应: {material_data}")
        
        # 测试获取资料列表
        print("\n=== 测试获取资料列表 ===")
        response = await client.get("/api/materials/")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        # 测试向后兼容 - 原有的API
        print("\n=== 测试原有API - 配置保存 ===")
        response = await client.post("/api/config/save", json={
            "api_key": "test-key-123",
            "model_name": "gpt-3.5-turbo"
        })
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        print("\n=== 所有测试完成! ===")


if __name__ == "__main__":
    asyncio.run(test_apis())
