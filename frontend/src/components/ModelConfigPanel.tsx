import React, { useState, useEffect } from 'react';
import { llmApi, LLMConfig, ProviderConfig } from '../services/api';

interface ProviderModels {
  [key: string]: string[];
}

const ModelConfigPanel: React.FC = () => {
  const [providers, setProviders] = useState<Record<string, ProviderConfig>>({
    openai: { api_key: '', model_name: 'gpt-4o', enabled: false },
    kimi: { api_key: '', model_name: 'kimi-flash-128k', enabled: false },
    deepseek: { api_key: '', model_name: 'deepseek-chat', enabled: false },
  });
  const [defaultProvider, setDefaultProvider] = useState<string>('openai');
  const [failoverEnabled, setFailoverEnabled] = useState(true);
  const [routingStrategy, setRoutingStrategy] = useState({
    parsing: ['kimi', 'deepseek', 'openai'],
    generation: ['deepseek', 'kimi', 'openai'],
    embedding: ['openai'],
    general: ['openai', 'kimi', 'deepseek'],
  });
  
  const [availableProviders, setAvailableProviders] = useState<string[]>([]);
  const [currentProvider, setCurrentProvider] = useState<string>('');
  const [providerModels, setProviderModels] = useState<ProviderModels>({});
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [testingProvider, setTestingProvider] = useState<string | null>(null);
  const [usageStats, setUsageStats] = useState<any>(null);

  useEffect(() => {
    loadProviders();
    loadRouting();
    loadUsage();
  }, []);

  const loadProviders = async () => {
    try {
      const response = await llmApi.getProviders();
      if (response.data.success) {
        setAvailableProviders(response.data.providers?.filter((p: any) => p.is_loaded)?.map((p: any) => p.type) || []);
        setCurrentProvider(response.data.current_provider || '');
      }
    } catch (error) {
      console.error('加载Provider失败:', error);
    }
  };

  const loadRouting = async () => {
    try {
      const response = await llmApi.getRouting();
      if (response.data.success) {
        const config = response.data.config;
        if (config.routing_strategy) setRoutingStrategy(config.routing_strategy);
        setFailoverEnabled(config.failover_enabled !== false);
      }
    } catch (error) {
      console.error('加载路由配置失败:', error);
    }
  };

  const loadUsage = async () => {
    try {
      const response = await llmApi.getUsage(30);
      if (response.data.success) {
        setUsageStats(response.data.summary);
      }
    } catch (error) {
      console.error('加载使用统计失败:', error);
    }
  };

  const loadModels = async (providerType: string) => {
    try {
      const response = await llmApi.getModels(providerType);
      if (response.data.success) {
        setProviderModels(prev => ({
          ...prev,
          [providerType]: response.data.models
        }));
      }
    } catch (error) {
      console.error('加载模型列表失败:', error);
    }
  };

  const handleProviderChange = (providerType: string, field: keyof ProviderConfig, value: any) => {
    setProviders(prev => ({
      ...prev,
      [providerType]: {
        ...prev[providerType],
        [field]: value
      }
    }));
    
    if (field === 'model_name' && !providerModels[providerType]) {
      loadModels(providerType);
    }
  };

  const handleTestProvider = async (providerType: string) => {
    const provider = providers[providerType];
    if (!provider.api_key || !provider.model_name) {
      setMessage({ type: 'error', text: '请填写API Key和模型名称' });
      return;
    }

    setTestingProvider(providerType);
    setMessage(null);
    
    try {
      const response = await llmApi.testProvider(
        providerType,
        provider.api_key,
        provider.base_url || '',
        provider.model_name
      );
      
      if (response.data.success) {
        setMessage({ type: 'success', text: `测试成功: ${response.data.response}` });
      } else {
        setMessage({ type: 'error', text: response.data.message });
      }
    } catch (error: any) {
      setMessage({ type: 'error', text: error.response?.data?.detail || '测试失败' });
    } finally {
      setTestingProvider(null);
    }
  };

  const handleSave = async () => {
    setLoading(true);
    setMessage(null);
    
    try {
      const config: LLMConfig = {
        providers,
        default_provider: defaultProvider,
        failover_enabled: failoverEnabled
      };
      
      const response = await llmApi.updateProviderConfig(config);
      
      if (response.data.success) {
        setMessage({ type: 'success', text: '配置保存成功！' });
        loadProviders();
        loadRouting();
      } else {
        setMessage({ type: 'error', text: response.data.message || '保存失败' });
      }
    } catch (error: any) {
      setMessage({ type: 'error', text: error.response?.data?.detail || '保存失败' });
    } finally {
      setLoading(false);
    }
  };

  const providerInfo = [
    { key: 'openai', name: 'OpenAI', color: 'blue', baseUrl: '' },
    { key: 'kimi', name: 'Kimi (Moonshot)', color: 'purple', baseUrl: 'https://api.moonshot.cn/v1' },
    { key: 'deepseek', name: 'DeepSeek', color: 'green', baseUrl: 'https://api.deepseek.com' },
  ];

  return (
    <div className="bg-white shadow-sm border-r border-gray-200 w-96 p-6 overflow-y-auto">
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">🤖 模型配置</h1>
          <hr className="mt-4 border-gray-200" />
        </div>

        {/* 使用统计 */}
        {usageStats && (
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-700 mb-2">📊 30天使用统计</h3>
            <div className="grid grid-cols-3 gap-2 text-center text-sm">
              <div>
                <div className="text-lg font-bold text-primary-600">{usageStats.total_requests}</div>
                <div className="text-gray-500">请求次数</div>
              </div>
              <div>
                <div className="text-lg font-bold text-primary-600">{usageStats.total_tokens?.toLocaleString()}</div>
                <div className="text-gray-500">Token消耗</div>
              </div>
              <div>
                <div className="text-lg font-bold text-red-500">{usageStats.total_errors}</div>
                <div className="text-gray-500">失败次数</div>
              </div>
            </div>
          </div>
        )}

        {/* 当前Provider */}
        <div>
          <h2 className="text-lg font-medium text-gray-900 mb-3">当前使用: {currentProvider || '未选择'}</h2>
        </div>

        {/* Provider配置 */}
        {providerInfo.map(info => (
          <div key={info.key} className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className={`font-medium text-${info.color}-600`}>{info.name}</h3>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={providers[info.key]?.enabled || false}
                  onChange={(e) => handleProviderChange(info.key, 'enabled', e.target.checked)}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="ml-2 text-sm text-gray-600">启用</span>
              </label>
            </div>
            
            <div className="space-y-3">
              <div>
                <label className="block text-xs text-gray-500">API Key</label>
                <input
                  type="password"
                  value={providers[info.key]?.api_key || ''}
                  onChange={(e) => handleProviderChange(info.key, 'api_key', e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 text-sm"
                  placeholder="输入API Key"
                />
              </div>
              
              <div>
                <label className="block text-xs text-gray-500">Base URL</label>
                <input
                  type="text"
                  value={providers[info.key]?.base_url || info.baseUrl}
                  onChange={(e) => handleProviderChange(info.key, 'base_url', e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 text-sm"
                  placeholder={info.baseUrl || '(可选)'}
                />
              </div>
              
              <div>
                <label className="block text-xs text-gray-500">模型</label>
                <div className="flex gap-2">
                  <select
                    value={providers[info.key]?.model_name || ''}
                    onChange={(e) => handleProviderChange(info.key, 'model_name', e.target.value)}
                    className="flex-1 mt-1 block rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 text-sm"
                  >
                    <option value="">选择模型</option>
                    {(providerModels[info.key] || []).map(model => (
                      <option key={model} value={model}>{model}</option>
                    ))}
                  </select>
                  <button
                    onClick={() => loadModels(info.key)}
                    className="mt-1 px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
                    title="获取模型列表"
                  >
                    🔄
                  </button>
                  <button
                    onClick={() => handleTestProvider(info.key)}
                    disabled={testingProvider === info.key || !providers[info.key]?.api_key}
                    className="mt-1 px-3 py-1 text-xs bg-blue-100 hover:bg-blue-200 rounded disabled:opacity-50"
                  >
                    {testingProvider === info.key ? '测试中...' : '测试'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}

        {/* 默认Provider选择 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">默认Provider</label>
          <select
            value={defaultProvider}
            onChange={(e) => setDefaultProvider(e.target.value)}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
          >
            {providerInfo.map(info => (
              <option key={info.key} value={info.key}>{info.name}</option>
            ))}
          </select>
        </div>

        {/* 故障转移 */}
        <div>
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={failoverEnabled}
              onChange={(e) => setFailoverEnabled(e.target.checked)}
              className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <span className="ml-2 text-sm text-gray-700">启用故障转移</span>
          </label>
          <p className="text-xs text-gray-500 mt-1">主Provider失败时自动切换到备用Provider</p>
        </div>

        {/* 路由策略 */}
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-2">路由策略</h3>
          <div className="space-y-2">
            {Object.entries(routingStrategy).map(([taskType, providerList]) => (
              <div key={taskType} className="flex items-center gap-2">
                <span className="text-xs text-gray-500 w-20">{taskType}:</span>
                <div className="flex gap-1 flex-wrap">
                  {providerList.map((p, idx) => (
                    <span key={idx} className="text-xs bg-gray-100 px-2 py-1 rounded">{p}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 保存按钮 */}
        <button
          onClick={handleSave}
          disabled={loading}
          className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:bg-gray-400"
        >
          {loading ? '保存中...' : '💾 保存配置'}
        </button>

        {/* 消息提示 */}
        {message && (
          <div className={`p-3 rounded-md text-sm ${
            message.type === 'success' 
              ? 'bg-green-100 text-green-700 border border-green-200' 
              : 'bg-red-100 text-red-700 border border-red-200'
          }`}>
            {message.text}
          </div>
        )}
      </div>
    </div>
  );
};

export default ModelConfigPanel;
