/**
 * 模板选择面板组件
 */
import React, { useState, useEffect } from 'react';
import { templateApi } from '../services/api';
import { 
  DocumentTextIcon, 
  CheckCircleIcon, 
  ExclamationCircleIcon,
  ChevronRightIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

interface TemplateSelectPanelProps {
  documentId: number;
  projectId?: number;
  projectOverview: string;
  technicalRequirements: string;
  onTemplateSelect: (templateId: number, templateSource: string) => void;
  onNext: () => void;
}

interface TemplateInfo {
  id: number;
  name: string;
  type: string;
  score: number;
  reasons: string[];
  recommendation: string;
}

const TemplateSelectPanel: React.FC<TemplateSelectPanelProps> = ({
  documentId,
  projectId,
  projectOverview,
  technicalRequirements,
  onTemplateSelect,
  onNext,
}) => {
  const [loading, setLoading] = useState(true);
  const [extracting, setExtracting] = useState(false);
  const [templates, setTemplates] = useState<TemplateInfo[]>([]);
  const [recommendedId, setRecommendedId] = useState<number | null>(null);
  const [confidence, setConfidence] = useState(0);
  const [industry, setIndustry] = useState('');
  const [selectedTemplateId, setSelectedTemplateId] = useState<number | null>(null);
  const [hasExtractedTemplate, setHasExtractedTemplate] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadTemplateRecommendation();
  }, [documentId]);

  const loadTemplateRecommendation = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await templateApi.getTemplateRecommendation(documentId);
      const data = response.data;
      
      setTemplates(data.templates);
      if (data.recommended_template_id) {
        setRecommendedId(data.recommended_template_id);
      }
      setConfidence(data.confidence);
      setIndustry(data.industry);
      
      const extracted = data.templates.find((t: TemplateInfo) => t.type === 'extracted');
      setHasExtractedTemplate(!!extracted);
      
      if (data.recommended_template_id) {
        setSelectedTemplateId(data.recommended_template_id);
      }
      
    } catch (err: any) {
      setError(err.response?.data?.detail || '获取模板推荐失败');
    } finally {
      setLoading(false);
    }
  };

  const handleExtractTemplate = async () => {
    try {
      setExtracting(true);
      setError(null);
      
      const response = await templateApi.extractTemplate(documentId);
      const data = response.data;
      
      if (data.success) {
        setHasExtractedTemplate(true);
        await loadTemplateRecommendation();
      } else {
        setError(data.message || '未检测到投标文件格式章节');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || '模板提取失败');
    } finally {
      setExtracting(false);
    }
  };

  const handleConfirmTemplate = () => {
    if (selectedTemplateId) {
      const selected = templates.find(t => t.id === selectedTemplateId);
      if (selected) {
        onTemplateSelect(selectedTemplateId, selected.type);
        onNext();
      }
    }
  };

  const getRecommendationBadge = (recommendation: string) => {
    switch (recommendation) {
      case '直接使用':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">直接使用</span>;
      case '建议确认':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">建议确认</span>;
      case '建议补充':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">建议补充</span>;
      default:
        return null;
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.5) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="text-center">
          <div className="animate-spin -ml-1 mr-3 h-8 w-8 text-blue-600">
            <ArrowPathIcon className="w-8 h-8" />
          </div>
          <p className="mt-4 text-gray-600">正在分析招标文件...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* 模板检测提示 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">📋 模板识别</h2>
        
        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center">
            {hasExtractedTemplate ? (
              <CheckCircleIcon className="w-6 h-6 text-green-500 mr-3" />
            ) : (
              <ExclamationCircleIcon className="w-6 h-6 text-yellow-500 mr-3" />
            )}
            <div>
              <p className="font-medium text-gray-900">
                {hasExtractedTemplate ? '已检测到投标文件格式章节' : '未检测到投标文件格式章节'}
              </p>
              <p className="text-sm text-gray-500">
                {hasExtractedTemplate 
                  ? '可以从招标文件中提取模板格式' 
                  : '可以从招标文件中提取模板格式'}
              </p>
            </div>
          </div>
          
          <button
            onClick={handleExtractTemplate}
            disabled={extracting || hasExtractedTemplate}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {extracting ? (
              <>
                <div className="animate-spin -ml-1 mr-2 h-4 w-4 text-white">
                  <ArrowPathIcon className="w-4 h-4" />
                </div>
                提取中...
              </>
            ) : hasExtractedTemplate ? (
              '已提取'
            ) : (
              '提取模板'
            )}
          </button>
        </div>
        
        {industry && (
          <div className="mt-4 text-sm text-gray-600">
            行业类型：<span className="font-medium">{industry}</span>
          </div>
        )}
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error}
        </div>
      )}

      {/* 模板推荐列表 */}
      {templates.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">🏆 模板推荐</h2>
          
          <div className="space-y-4">
            {templates.map((template) => (
              <div
                key={template.id}
                onClick={() => setSelectedTemplateId(template.id)}
                className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                  selectedTemplateId === template.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start">
                    <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center mr-3 ${
                      selectedTemplateId === template.id
                        ? 'border-blue-500 bg-blue-500'
                        : 'border-gray-300'
                    }`}>
                      {selectedTemplateId === template.id && (
                        <div className="w-2 h-2 bg-white rounded-full" />
                      )}
                    </div>
                    
                    <div>
                      <div className="flex items-center gap-2">
                        <DocumentTextIcon className="w-5 h-5 text-gray-400" />
                        <span className="font-medium text-gray-900">{template.name}</span>
                        <span className="text-xs text-gray-500">
                          ({template.type === 'extracted' ? '提取模板' : 
                            template.type === 'builtin' ? '内置模板' : '自定义模板'})
                        </span>
                      </div>
                      
                      <div className="mt-2 text-sm text-gray-600">
                        <div className="flex items-center gap-2">
                          <span className={`font-medium ${getScoreColor(template.score)}`}>
                            匹配度: {Math.round(template.score * 100)}%
                          </span>
                          {getRecommendationBadge(template.recommendation)}
                        </div>
                      </div>
                      
                      {template.reasons.length > 0 && (
                        <div className="mt-2 text-xs text-gray-500">
                          {template.reasons.map((reason, idx) => (
                            <div key={idx} className="flex items-center gap-1">
                              <ChevronRightIcon className="w-3 h-3" />
                              {reason}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          {/* 置信度提示 */}
          {confidence < 0.5 && (
            <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-yellow-800">
                模板匹配度较低，建议：1) 手动检查模板格式 2) 上传自定义模板 3) 使用通用内置模板
              </p>
            </div>
          )}
          
          {/* 确认按钮 */}
          <div className="mt-6 flex justify-end">
            <button
              onClick={handleConfirmTemplate}
              disabled={!selectedTemplateId}
              className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              使用选定模板
              <ChevronRightIcon className="ml-2 w-5 h-5" />
            </button>
          </div>
        </div>
      )}

      {/* 无模板可用时 */}
      {templates.length === 0 && !loading && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-center py-8">
            <ExclamationCircleIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-4 text-lg font-medium text-gray-900">未找到合适模板</h3>
            <p className="mt-2 text-sm text-gray-500">
              请尝试：1) 上传包含投标文件格式的招标文件 2) 使用内置行业模板 3) 上传自定义模板
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default TemplateSelectPanel;