"""配置管理工具"""
import json
import os
from typing import Dict, Optional, List


class ConfigManager:
    """用户配置管理器"""
    
    def __init__(self):
        self.config_dir = os.path.join(os.path.expanduser("~"), ".ai_write_helper")
        self.config_file = os.path.join(self.config_dir, "user_config.json")
        os.makedirs(self.config_dir, exist_ok=True)
    
    def load_config(self) -> Dict:
        """从本地JSON文件加载配置"""
        default_config = {
            'api_key': '',
            'base_url': '',
            'model_name': 'gpt-3.5-turbo',
            'providers': {},
            'default_provider': 'openai',
            'failover_enabled': True,
            'routing_strategy': {
                'parsing': ['kimi', 'deepseek', 'openai'],
                'generation': ['deepseek', 'kimi', 'openai'],
                'embedding': ['openai'],
                'general': ['openai', 'kimi', 'deepseek']
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception:
                pass
        
        return default_config
    
    def save_config(self, api_key: str, base_url: str, model_name: str) -> bool:
        """保存配置到本地JSON文件（兼容旧版本）"""
        config = {
            'api_key': api_key,
            'base_url': base_url,
            'model_name': model_name
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    def save_full_config(self, config: Dict) -> bool:
        """保存完整配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    def get_provider_config(self, provider_type: str) -> Optional[Dict]:
        """获取指定Provider的配置"""
        config = self.load_config()
        providers = config.get('providers', {})
        return providers.get(provider_type)
    
    def set_provider_config(self, provider_type: str, provider_config: Dict) -> bool:
        """设置指定Provider的配置"""
        config = self.load_config()
        if 'providers' not in config:
            config['providers'] = {}
        config['providers'][provider_type] = provider_config
        return self.save_full_config(config)
    
    def get_routing_strategy(self) -> Dict[str, List[str]]:
        """获取路由策略"""
        config = self.load_config()
        return config.get('routing_strategy', {})
    
    def set_routing_strategy(self, strategy: Dict[str, List[str]]) -> bool:
        """设置路由策略"""
        config = self.load_config()
        config['routing_strategy'] = strategy
        return self.save_full_config(config)


config_manager = ConfigManager()