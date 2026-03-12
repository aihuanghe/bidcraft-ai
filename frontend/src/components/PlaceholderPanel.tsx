/**
 * 占位符填充面板组件
 */
import React, { useState, useEffect } from 'react';
import { 
  DocumentTextIcon, 
  CheckCircleIcon, 
  ArrowPathIcon,
  MagnifyingGlassIcon,
  PencilIcon,
  XMarkIcon,
  CloudArrowUpIcon
} from '@heroicons/react/24/outline';

interface PlaceholderPanelProps {
  projectId: number;
  projectOverview: string;
}

interface Placeholder {
  id: string;
  type: 'manual' | 'rag_retrieval' | 'erp_api' | 'hr_api' | 'finance_api';
  label: string;
  required: boolean;
  source: string;
  category: string;
  value?: any;
  status: 'filled' | 'unfilled' | 'pending_confirm';
}

const PlaceholderPanel: React.FC<PlaceholderPanelProps> = ({
  projectId,
  projectOverview,
}) => {
  const [placeholders, setPlaceholders] = useState<Placeholder[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');
  const [ragSearching, setRagSearching] = useState<string | null>(null);

  useEffect(() => {
    loadPlaceholders();
  }, [projectId]);

  const loadPlaceholders = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/enterprise/projects/${projectId}/placeholders`);
      const data = await response.json();
      if (data.success) {
        setPlaceholders(data.placeholders);
      }
    } catch (error) {
      console.error('加载占位符失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFillManual = async (placeholder: Placeholder) => {
    if (!editValue.trim()) return;

    try {
      const response = await fetch(
        `/api/enterprise/projects/${projectId}/placeholders/${placeholder.id}/fill`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            value: editValue,
            mode: 'manual'
          })
        }
      );
      const data = await response.json();
      if (data.success) {
        setPlaceholders(prev => 
          prev.map(p => 
            p.id === placeholder.id 
              ? { ...p, value: editValue, status: 'filled' as const }
              : p
          )
        );
        setEditingId(null);
        setEditValue('');
      }
    } catch (error) {
      console.error('填充失败:', error);
    }
  };

  const handleAutoFillRAG = async (placeholder: Placeholder) => {
    try {
      setRagSearching(placeholder.id);
      
      const query = `${placeholder.label} ${projectOverview}`.slice(0, 200);
      
      const response = await fetch(
        `/api/enterprise/projects/${projectId}/placeholders/${placeholder.id}/auto-fill?query=${encodeURIComponent(query)}`,
        { method: 'POST' }
      );
      const data = await response.json();
      
      if (data.success) {
        setPlaceholders(prev => 
          prev.map(p => 
            p.id === placeholder.id 
              ? { ...p, value: data.value, status: 'pending_confirm' as const }
              : p
          )
        );
      } else {
        alert(data.message || '自动填充失败');
      }
    } catch (error) {
      console.error('RAG填充失败:', error);
    } finally {
      setRagSearching(null);
    }
  };

  const handleConfirmRAG = (placeholder: Placeholder) => {
    setPlaceholders(prev => 
      prev.map(p => 
        p.id === placeholder.id 
          ? { ...p, status: 'filled' as const }
          : p
      )
    );
  };

  const handleRejectRAG = (placeholder: Placeholder) => {
    setPlaceholders(prev => 
      prev.map(p => 
        p.id === placeholder.id 
          ? { ...p, value: null, status: 'unfilled' as const }
          : p
      )
    );
  };

  const filteredPlaceholders = placeholders.filter(p => {
    const matchesFilter = filter === 'all' || 
      (filter === 'filled' && p.status === 'filled') ||
      (filter === 'unfilled' && p.status === 'unfilled') ||
      (filter === 'pending' && p.status === 'pending_confirm');
    
    const matchesSearch = !searchQuery || 
      p.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.id.toLowerCase().includes(searchQuery.toLowerCase());
    
    return matchesFilter && matchesSearch;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'filled':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'pending_confirm':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default:
        return 'bg-gray-100 text-gray-600 border-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'filled':
        return <CheckCircleIcon className="w-4 h-4 text-green-500" />;
      case 'pending_confirm':
        return <ArrowPathIcon className="w-4 h-4 text-yellow-500" />;
      default:
        return <XMarkIcon className="w-4 h-4 text-gray-400" />;
    }
  };

  const getCategoryIcon = (category: string) => {
    return <DocumentTextIcon className="w-4 h-4" />;
  };

  const filledCount = placeholders.filter(p => p.status === 'filled').length;
  const totalCount = placeholders.length;
  const progress = totalCount > 0 ? Math.round((filledCount / totalCount) * 100) : 0;

  if (loading) {
    return (
      <div className="p-4 text-center">
        <div className="animate-spin -ml-1 mr-3 h-6 w-6 text-blue-600">
          <ArrowPathIcon className="w-6 h-6" />
        </div>
        <p className="mt-2 text-sm text-gray-500">加载占位符...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* 头部 */}
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <DocumentTextIcon className="w-5 h-5" />
          占位符填充
        </h3>
        
        {/* 进度条 */}
        <div className="mt-3">
          <div className="flex justify-between text-sm text-gray-600 mb-1">
            <span>填充进度</span>
            <span>{filledCount}/{totalCount} ({progress}%)</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* 搜索和筛选 */}
        <div className="mt-3 flex gap-2">
          <input
            type="text"
            placeholder="搜索占位符..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">全部</option>
            <option value="filled">已填充</option>
            <option value="unfilled">未填充</option>
            <option value="pending">待确认</option>
          </select>
        </div>
      </div>

      {/* 占位符列表 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {filteredPlaceholders.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            暂无占位符
          </div>
        ) : (
          filteredPlaceholders.map((placeholder) => (
            <div
              key={placeholder.id}
              className={`p-3 rounded-lg border ${getStatusColor(placeholder.status)}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-2">
                  {getStatusIcon(placeholder.status)}
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm">{placeholder.label}</span>
                      {placeholder.required && (
                        <span className="text-xs text-red-500">*必填</span>
                      )}
                    </div>
                    <div className="text-xs text-gray-500 mt-1 flex items-center gap-2">
                      <span>{getCategoryIcon(placeholder.category)}</span>
                      <span>{placeholder.category}</span>
                      <span>•</span>
                      <span>{placeholder.type}</span>
                    </div>
                    
                    {/* 值显示/编辑 */}
                    <div className="mt-2">
                      {placeholder.status === 'filled' && (
                        <div className="text-sm text-gray-700 bg-white p-2 rounded border">
                          {typeof placeholder.value === 'object' 
                            ? JSON.stringify(placeholder.value).slice(0, 100)
                            : placeholder.value}
                        </div>
                      )}
                      
                      {placeholder.status === 'pending_confirm' && (
                        <div className="space-y-2">
                          <div className="text-sm text-gray-700 bg-white p-2 rounded border">
                            {typeof placeholder.value === 'object' 
                              ? JSON.stringify(placeholder.value).slice(0, 100)
                              : placeholder.value}
                          </div>
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleConfirmRAG(placeholder)}
                              className="px-2 py-1 text-xs bg-green-500 text-white rounded hover:bg-green-600"
                            >
                              确认
                            </button>
                            <button
                              onClick={() => handleRejectRAG(placeholder)}
                              className="px-2 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600"
                            >
                              拒绝
                            </button>
                          </div>
                        </div>
                      )}
                      
                      {placeholder.status === 'unfilled' && editingId !== placeholder.id && (
                        <div className="flex gap-2">
                          {placeholder.type === 'manual' && (
                            <button
                              onClick={() => setEditingId(placeholder.id)}
                              className="px-3 py-1.5 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 flex items-center gap-1"
                            >
                              <PencilIcon className="w-3 h-3" />
                              手动填写
                            </button>
                          )}
                          
                          {(placeholder.type === 'rag_retrieval' || placeholder.source === 'rag') && (
                            <button
                              onClick={() => handleAutoFillRAG(placeholder)}
                              disabled={ragSearching === placeholder.id}
                              className="px-3 py-1.5 text-xs bg-purple-500 text-white rounded hover:bg-purple-600 flex items-center gap-1 disabled:opacity-50"
                            >
                              {ragSearching === placeholder.id ? (
                                <>
                                  <ArrowPathIcon className="w-3 h-3 animate-spin" />
                                  检索中...
                                </>
                              ) : (
                                <>
                                  <MagnifyingGlassIcon className="w-3 h-3" />
                                  自动检索
                                </>
                              )}
                            </button>
                          )}
                        </div>
                      )}
                      
                      {placeholder.status === 'unfilled' && editingId === placeholder.id && (
                        <div className="space-y-2">
                          <textarea
                            value={editValue}
                            onChange={(e) => setEditValue(e.target.value)}
                            placeholder={`请输入${placeholder.label}`}
                            className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                            rows={3}
                          />
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleFillManual(placeholder)}
                              className="px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600"
                            >
                              确认
                            </button>
                            <button
                              onClick={() => {
                                setEditingId(null);
                                setEditValue('');
                              }}
                              className="px-2 py-1 text-xs bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
                            >
                              取消
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default PlaceholderPanel;