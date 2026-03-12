"""企业数据Provider接口定义和Mock实现"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime


class IEnterpriseDataProvider(ABC):
    """企业数据Provider抽象基类"""
    
    @abstractmethod
    def get_company_info(self) -> Dict[str, Any]:
        """获取公司基本信息"""
        pass
    
    @abstractmethod
    def get_qualifications(self, valid_only: bool = True) -> List[Dict[str, Any]]:
        """获取企业资质列表"""
        pass
    
    @abstractmethod
    def get_projects(self, min_amount: float = None, max_amount: float = None) -> List[Dict[str, Any]]:
        """获取企业业绩列表"""
        pass
    
    @abstractmethod
    def get_personnel(self, role: str = None) -> List[Dict[str, Any]]:
        """获取人员列表"""
        pass
    
    @abstractmethod
    def get_products(self, category: str = None) -> List[Dict[str, Any]]:
        """获取产品列表"""
        pass
    
    @abstractmethod
    def get_financial_data(self, year: int = None) -> Dict[str, Any]:
        """获取财务数据"""
        pass


class MockQualificationProvider(IEnterpriseDataProvider):
    """Mock资质Provider"""
    
    def get_company_info(self) -> Dict[str, Any]:
        return {
            "company_name": "示例科技有限公司",
            "company_address": "北京市朝阳区示例大厦",
            "legal_representative": "张三",
            "registered_capital": 50000000,
            "establishment_date": "2010-01-01"
        }
    
    def get_qualifications(self, valid_only: bool = True) -> List[Dict[str, Any]]:
        qualifications = [
            {
                "id": "Q001",
                "name": "ISO9001质量管理体系认证",
                "certificate_no": "ISO9001-2024",
                "issue_date": "2024-01-01",
                "expiry_date": "2027-01-01",
                "status": "valid"
            },
            {
                "id": "Q002",
                "name": "计算机信息系统集成资质一级",
                "certificate_no": "CITSI-2023-001",
                "issue_date": "2023-06-01",
                "expiry_date": "2026-06-01",
                "status": "valid"
            },
            {
                "id": "Q003",
                "name": "CMMI五级认证",
                "certificate_no": "CMMI-2022-5",
                "issue_date": "2022-09-01",
                "expiry_date": "2025-09-01",
                "status": "expired" if not valid_only else None
            }
        ]
        if valid_only:
            return [q for q in qualifications if q.get("status") == "valid"]
        return qualifications
    
    def get_projects(self, min_amount: float = None, max_amount: float = None) -> List[Dict[str, Any]]:
        projects = [
            {
                "id": "P001",
                "name": "某市政府信息化项目",
                "contract_amount": 15000000,
                "completion_date": "2023-12-01",
                "client_name": "某市人民政府",
                "project_type": "government"
            },
            {
                "id": "P002",
                "name": "某企业ERP系统建设",
                "contract_amount": 8000000,
                "completion_date": "2023-06-15",
                "client_name": "某大型企业",
                "project_type": "enterprise"
            },
            {
                "id": "P003",
                "name": "某医院信息系统升级",
                "contract_amount": 12000000,
                "completion_date": "2024-03-01",
                "client_name": "某三甲医院",
                "project_type": "medical"
            }
        ]
        
        filtered = projects
        if min_amount is not None:
            filtered = [p for p in filtered if p.get("contract_amount", 0) >= min_amount]
        if max_amount is not None:
            filtered = [p for p in filtered if p.get("contract_amount", 0) <= max_amount]
        
        return filtered
    
    def get_personnel(self, role: str = None) -> List[Dict[str, Any]]:
        personnel = [
            {
                "id": "PER001",
                "name": "李经理",
                "role": "项目经理",
                "title": "高级项目经理",
                "certifications": ["PMP", "软考高级"],
                "experience_years": 15
            },
            {
                "id": "PER002",
                "name": "王工",
                "role": "技术负责人",
                "title": "技术总监",
                "certifications": ["CCIE", "OCP"],
                "experience_years": 12
            },
            {
                "id": "PER003",
                "name": "赵工",
                "role": "架构师",
                "title": "系统架构师",
                "certifications": ["TOGAF"],
                "experience_years": 10
            }
        ]
        
        if role:
            return [p for p in personnel if p.get("role") == role]
        return personnel
    
    def get_products(self, category: str = None) -> List[Dict[str, Any]]:
        products = [
            {
                "id": "PROD001",
                "name": "企业管理系统",
                "category": "software",
                "model_number": "ES-V3.0",
                "description": "综合企业管理平台"
            },
            {
                "id": "PROD002",
                "name": "智慧园区平台",
                "category": "software",
                "model_number": "SP-V2.5",
                "description": "智慧园区综合管理"
            },
            {
                "id": "PROD003",
                "name": "数据分析平台",
                "category": "software",
                "model_number": "DA-V1.8",
                "description": "大数据分析平台"
            }
        ]
        
        if category:
            return [p for p in products if p.get("category") == category]
        return products
    
    def get_financial_data(self, year: int = None) -> Dict[str, Any]:
        return {
            "year": year or 2024,
            "total_revenue": 500000000,
            "net_profit": 50000000,
            "total_assets": 300000000,
            "current_assets": 150000000,
            "current_liabilities": 80000000
        }


class MockERPProvider(IEnterpriseDataProvider):
    """Mock ERP Provider"""
    
    def get_company_info(self) -> Dict[str, Any]:
        return {
            "company_name": "示例科技有限公司",
            "org_code": "91110000XXXXXXXX",
            "tax_no": "110XXXXXXXXXXXXXX"
        }
    
    def get_qualifications(self, valid_only: bool = True) -> List[Dict[str, Any]]:
        return []
    
    def get_projects(self, min_amount: float = None, max_amount: float = None) -> List[Dict[str, Any]]:
        return [
            {
                "project_code": "ERP-P001",
                "project_name": "ERP实施项目",
                "contract_amount": 5000000,
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            }
        ]
    
    def get_personnel(self, role: str = None) -> List[Dict[str, Any]]:
        return []
    
    def get_products(self, category: str = None) -> List[Dict[str, Any]]:
        return []
    
    def get_financial_data(self, year: int = None) -> Dict[str, Any]:
        return {
            "year": year or 2024,
            "revenue": 500000000,
            "cost": 400000000,
            "profit": 100000000
        }


class MockHRProvider(IEnterpriseDataProvider):
    """Mock HR Provider"""
    
    def get_company_info(self) -> Dict[str, Any]:
        return {}
    
    def get_qualifications(self, valid_only: bool = True) -> List[Dict[str, Any]]:
        return []
    
    def get_projects(self, min_amount: float = None, max_amount: float = None) -> List[Dict[str, Any]]:
        return []
    
    def get_personnel(self, role: str = None) -> List[Dict[str, Any]]:
        personnel = [
            {
                "employee_id": "EMP001",
                "name": "张三",
                "department": "技术部",
                "position": "项目经理",
                "email": "zhangsan@example.com",
                "phone": "13800138000"
            },
            {
                "employee_id": "EMP002",
                "name": "李四",
                "department": "技术部",
                "position": "高级工程师",
                "email": "lisi@example.com",
                "phone": "13800138001"
            },
            {
                "employee_id": "EMP003",
                "name": "王五",
                "department": "技术部",
                "position": "架构师",
                "email": "wangwu@example.com",
                "phone": "13800138002"
            }
        ]
        
        if role:
            return [p for p in personnel if role.lower() in p.get("position", "").lower()]
        return personnel
    
    def get_products(self, category: str = None) -> List[Dict[str, Any]]:
        return []
    
    def get_financial_data(self, year: int = None) -> Dict[str, Any]:
        return {}


class MockFinanceProvider(IEnterpriseDataProvider):
    """Mock Finance Provider"""
    
    def get_company_info(self) -> Dict[str, Any]:
        return {}
    
    def get_qualifications(self, valid_only: bool = True) -> List[Dict[str, Any]]:
        return []
    
    def get_projects(self, min_amount: float = None, max_amount: float = None) -> List[Dict[str, Any]]:
        return []
    
    def get_personnel(self, role: str = None) -> List[Dict[str, Any]]:
        return []
    
    def get_products(self, category: str = None) -> List[Dict[str, Any]]:
        return []
    
    def get_financial_data(self, year: int = None) -> Dict[str, Any]:
        return {
            "year": year or 2024,
            "income_statement": {
                "revenue": 500000000,
                "cost_of_goods_sold": 350000000,
                "gross_profit": 150000000,
                "operating_expenses": 80000000,
                "operating_profit": 70000000,
                "net_profit": 50000000
            },
            "balance_sheet": {
                "total_assets": 300000000,
                "total_liabilities": 150000000,
                "total_equity": 150000000
            }
        }


class ProviderFactory:
    """Provider工厂类"""
    
    _providers = {
        "mock": {
            "qualification": MockQualificationProvider,
            "erp": MockERPProvider,
            "hr": MockHRProvider,
            "finance": MockFinanceProvider
        }
    }
    
    @classmethod
    def get_provider(cls, provider_type: str = "mock") -> Dict[str, IEnterpriseDataProvider]:
        """获取Provider实例"""
        provider_classes = cls._providers.get(provider_type, cls._providers["mock"])
        
        return {
            key: provider_class() 
            for key, provider_class in provider_classes.items()
        }
    
    @classmethod
    def set_provider_type(cls, provider_type: str):
        """设置Provider类型（mock/real）"""
        if provider_type not in cls._providers:
            raise ValueError(f"不支持的Provider类型: {provider_type}")


def get_enterprise_providers(provider_type: str = "mock") -> Dict[str, IEnterpriseDataProvider]:
    """获取企业数据Providers"""
    return ProviderFactory.get_provider(provider_type)