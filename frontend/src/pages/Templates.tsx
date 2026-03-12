import React, { useState, useEffect } from 'react';
import { 
  PlusIcon, 
  DocumentDuplicateIcon,
  PencilIcon,
  TrashIcon,
  CheckCircleIcon,
  XMarkIcon,
  ArrowDownTrayIcon,
  ArrowUpTrayIcon
} from '@heroicons/react/24/outline';
import api, { templateApi } from '../services/api';
import { ExtractedTemplate } from '../types';

const Templates: React.FC = () => {
  const [templates, setTemplates] = useState<ExtractedTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<ExtractedTemplate | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [createForm, setCreateForm] = useState({
    name: '',
    template_type: 'custom' as 'builtin' | 'custom' | 'extracted',
    description: '',
    industry: ''
  });

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/templates/');
      setTemplates(response.data.data || []);
    } catch (error) {
      console.error('加载模板失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!createForm.name) {
      alert('请输入模板名称');
      return;
    }

    try {
      await api.post('/api/templates/', createForm);
      setShowCreateModal(false);
      setCreateForm({
        name: '',
        template_type: 'custom',
        description: '',
        industry: ''
      });
      loadTemplates();
    } catch (error) {
      console.error('创建模板失败:', error);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('确定要删除这个模板吗？')) return;

    try {
      await api.delete(`/api/templates/${id}`);
      loadTemplates();
    } catch (error) {
      console.error('删除失败:', error);
    }
  };

  const handleExport = async (template: ExtractedTemplate) => {
    try {
      const response = await api.get(`/api/templates/${template.id}/export`);
      const blob = await response.data.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${template.name}.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('导出失败:', error);
    }
  };

  const getTypeBadgeColor = (type: string) => {
    switch (type) {
      case 'builtin': return 'bg-green-100 text-green-700';
      case 'custom': return 'bg-blue-100 text-blue-700';
      case 'extracted': return 'bg-purple-100 text-purple-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* 顶部 */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">模板管理</h1>
          
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            <PlusIcon className="w-5 h-5" />
            新建模板
          </button>
        </div>
      </div>

      {/* 模板列表 */}
      <div className="flex-1 overflow-y-auto p-6">
        {loading ? (
          <div className="text-center py-12 text-gray-500">加载中...</div>
        ) : templates.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            暂无模板，请创建模板
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {templates.map(template => (
              <div
                key={template.id}
                className="bg-white rounded-lg shadow hover:shadow-md transition-shadow"
              >
                <div className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900">{template.name}</h3>
                      <span className={`inline-block mt-2 px-2 py-1 text-xs rounded ${getTypeBadgeColor(template.template_type)}`}>
                        {template.template_type === 'builtin' ? '内置' : template.template_type === 'custom' ? '自定义' : '提取'}
                      </span>
                    </div>
                  </div>
                  
                  {template.description && (
                    <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                      {template.description}
                    </p>
                  )}
                  
                  {template.industry && (
                    <p className="text-xs text-gray-500 mt-2">
                      行业: {template.industry}
                    </p>
                  )}
                  
                  {template.confidence_score && (
                    <div className="mt-3">
                      <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                        <span>匹配度</span>
                        <span>{Math.round(template.confidence_score * 100)}%</span>
                      </div>
                      <div className="w-full h-1.5 bg-gray-200 rounded overflow-hidden">
                        <div
                          className="h-full bg-blue-500"
                          style={{ width: `${template.confidence_score * 100}%` }}
                        />
                      </div>
                    </div>
                  )}
                  
                  <div className="mt-4 flex gap-2">
                    <button
                      onClick={() => {
                        setSelectedTemplate(template);
                        setShowDetailModal(true);
                      }}
                      className="flex-1 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-50"
                    >
                      查看
                    </button>
                    <button
                      onClick={() => handleExport(template)}
                      className="px-3 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-50"
                      title="导出"
                    >
                      <ArrowDownTrayIcon className="w-4 h-4" />
                    </button>
                    {template.template_type === 'custom' && (
                      <button
                        onClick={() => handleDelete(template.id)}
                        className="px-3 py-1.5 text-sm text-red-600 border border-red-200 rounded hover:bg-red-50"
                        title="删除"
                      >
                        <TrashIcon className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 创建弹窗 */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg w-full max-w-md">
            <div className="flex items-center justify-between px-6 py-4 border-b">
              <h2 className="text-lg font-semibold">新建模板</h2>
              <button onClick={() => setShowCreateModal(false)}>
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">模板名称 *</label>
                <input
                  type="text"
                  value={createForm.name}
                  onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded"
                  placeholder="请输入模板名称"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">模板类型</label>
                <select
                  value={createForm.template_type}
                  onChange={(e) => setCreateForm({ ...createForm, template_type: e.target.value as any })}
                  className="w-full px-3 py-2 border border-gray-300 rounded"
                >
                  <option value="custom">自定义模板</option>
                  <option value="builtin">内置模板</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">所属行业</label>
                <input
                  type="text"
                  value={createForm.industry}
                  onChange={(e) => setCreateForm({ ...createForm, industry: e.target.value })}
                  className="width-full px-3 py-2 border border-gray-300 rounded"
                  placeholder="例如: 建筑, 市政, 电力"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">描述</label>
                <textarea
                  value={createForm.description}
                  onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded"
                  rows={3}
                  placeholder="请输入模板描述"
                />
              </div>
            </div>
            
            <div className="flex justify-end gap-3 px-6 py-4 border-t bg-gray-50">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
              >
                取消
              </button>
              <button
                onClick={handleCreate}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                创建
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 详情弹窗 */}
      {showDetailModal && selectedTemplate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b">
              <h2 className="text-lg font-semibold">{selectedTemplate.name}</h2>
              <button onClick={() => setShowDetailModal(false)}>
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-gray-500">类型：</span>
                  <span className={`px-2 py-1 text-xs rounded ${getTypeBadgeColor(selectedTemplate.template_type)}`}>
                    {selectedTemplate.template_type}
                  </span>
                </div>
                {selectedTemplate.industry && (
                  <div>
                    <span className="text-gray-500">行业：</span>
                    <span>{selectedTemplate.industry}</span>
                  </div>
                )}
                {selectedTemplate.confidence_score && (
                  <div>
                    <span className="text-gray-500">匹配度：</span>
                    <span>{Math.round(selectedTemplate.confidence_score * 100)}%</span>
                  </div>
                )}
              </div>
              
              {selectedTemplate.description && (
                <div>
                  <h3 className="font-medium mb-2">描述</h3>
                  <p className="text-gray-600">{selectedTemplate.description}</p>
                </div>
              )}
              
              {selectedTemplate.structure_json?.sections && (
                <div>
                  <h3 className="font-medium mb-2">章节结构</h3>
                  <div className="bg-gray-50 p-4 rounded max-h-60 overflow-y-auto">
                    <pre className="text-sm whitespace-pre-wrap">
                      {JSON.stringify(selectedTemplate.structure_json.sections, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </div>
            
            <div className="flex justify-end gap-3 px-6 py-4 border-t bg-gray-50">
              <button
                onClick={() => setShowDetailModal(false)}
                className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Templates;
