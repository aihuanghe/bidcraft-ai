import React, { useState, useEffect } from 'react';
import { 
  MagnifyingGlassIcon, 
  PlusIcon, 
  FolderIcon,
  DocumentTextIcon,
  UserIcon,
  CurrencyDollarIcon,
  CubeIcon,
  XMarkIcon,
  ArrowUpTrayIcon,
  EyeIcon,
  PencilIcon,
  TrashIcon
} from '@heroicons/react/24/outline';
import api, { enterpriseApi } from '../services/api';
import { EnterpriseMaterial, MaterialType } from '../types';

const MATERIAL_TABS: { key: MaterialType | 'all'; label: string; icon: React.ReactNode }[] = [
  { key: 'all', label: '全部', icon: <FolderIcon className="w-5 h-5" /> },
  { key: 'case', label: '成功案例', icon: <DocumentTextIcon className="w-5 h-5" /> },
  { key: 'certificate', label: '证书资质', icon: <FolderIcon className="w-5 h-5" /> },
  { key: 'qualification', label: '施工资质', icon: <FolderIcon className="w-5 h-5" /> },
  { key: 'personnel', label: '人员资质', icon: <UserIcon className="w-5 h-5" /> },
  { key: 'finance', label: '财务数据', icon: <CurrencyDollarIcon className="w-5 h-5" /> },
  { key: 'product', label: '产品资料', icon: <CubeIcon className="w-5 h-5" /> },
];

const Materials: React.FC = () => {
  const [activeTab, setActiveTab] = useState<MaterialType | 'all'>('all');
  const [materials, setMaterials] = useState<EnterpriseMaterial[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedMaterial, setSelectedMaterial] = useState<EnterpriseMaterial | null>(null);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  
  const [uploadForm, setUploadForm] = useState({
    name: '',
    material_type: 'case' as MaterialType,
    description: '',
    file: null as File | null,
    contract_amount: undefined as number | undefined,
    completion_date: '',
    client_name: '',
    model_number: '',
    tags: ''
  });

  useEffect(() => {
    loadMaterials();
  }, [activeTab]);

  const loadMaterials = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (activeTab !== 'all') {
        params.material_type = activeTab;
      }
      if (searchQuery) {
        params.query = searchQuery;
      }
      
      const response = await api.get('/api/enterprise/materials/', { params });
      setMaterials(response.data.data || []);
    } catch (error) {
      console.error('加载素材失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    loadMaterials();
  };

  const handleUpload = async () => {
    if (!uploadForm.name || !uploadForm.file) {
      alert('请填写名称并选择文件');
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('name', uploadForm.name);
      formData.append('material_type', uploadForm.material_type);
      formData.append('description', uploadForm.description);
      formData.append('file', uploadForm.file);
      
      if (uploadForm.contract_amount) {
        formData.append('contract_amount', String(uploadForm.contract_amount));
      }
      if (uploadForm.completion_date) {
        formData.append('completion_date', uploadForm.completion_date);
      }
      if (uploadForm.client_name) {
        formData.append('client_name', uploadForm.client_name);
      }
      if (uploadForm.model_number) {
        formData.append('model_number', uploadForm.model_number);
      }
      if (uploadForm.tags) {
        formData.append('tags', uploadForm.tags);
      }

      const response = await api.post('/api/enterprise/materials/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1));
          setUploadProgress(progress);
        }
      });

      if (response.data.success) {
        alert('上传成功');
        setShowUploadModal(false);
        setUploadForm({
          name: '',
          material_type: 'case',
          description: '',
          file: null,
          contract_amount: undefined,
          completion_date: '',
          client_name: '',
          model_number: '',
          tags: ''
        });
        loadMaterials();
      }
    } catch (error) {
      console.error('上传失败:', error);
      alert('上传失败');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('确定要删除这个素材吗？')) return;
    
    try {
      await api.delete(`/api/enterprise/materials/${id}`);
      loadMaterials();
    } catch (error) {
      console.error('删除失败:', error);
    }
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* 顶部搜索栏 */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">企业素材库</h1>
          
          <button
            onClick={() => setShowUploadModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            <ArrowUpTrayIcon className="w-5 h-5" />
            上传素材
          </button>
        </div>
        
        <div className="mt-4 flex gap-4">
          <div className="flex-1 relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="搜索素材名称、内容、标签..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          <input
            type="date"
            className="px-4 py-2 border border-gray-300 rounded-lg"
            placeholder="开始日期"
          />
          <input
            type="date"
            className="px-4 py-2 border border-gray-300 rounded-lg"
            placeholder="结束日期"
          />
          
          <button
            onClick={handleSearch}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            搜索
          </button>
        </div>
      </div>

      {/* 分类标签 */}
      <div className="bg-white border-b border-gray-200 px-6">
        <div className="flex gap-2 overflow-x-auto py-2">
          {MATERIAL_TABS.map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-full whitespace-nowrap ${
                activeTab === tab.key
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* 素材列表 */}
      <div className="flex-1 overflow-y-auto p-6">
        {loading ? (
          <div className="text-center py-12 text-gray-500">加载中...</div>
        ) : materials.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            暂无素材，请上传或调整筛选条件
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {materials.map(material => (
              <div
                key={material.id}
                className="bg-white rounded-lg shadow hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => {
                  setSelectedMaterial(material);
                  setShowDetailModal(true);
                }}
              >
                <div className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900 truncate">{material.name}</h3>
                      <p className="text-sm text-gray-500 mt-1">
                        {MATERIAL_TABS.find(t => t.key === material.material_type)?.label || material.material_type}
                      </p>
                    </div>
                    {material.file_url && (
                      <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded">
                        已上传
                      </span>
                    )}
                  </div>
                  
                  {material.description && (
                    <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                      {material.description}
                    </p>
                  )}
                  
                  <div className="mt-3 flex items-center justify-between text-xs text-gray-500">
                    <span>{new Date(material.created_at).toLocaleDateString()}</span>
                    {material.contract_amount && (
                      <span>¥{material.contract_amount.toLocaleString()}</span>
                    )}
                  </div>
                  
                  <div className="mt-3 flex gap-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedMaterial(material);
                        setShowDetailModal(true);
                      }}
                      className="flex-1 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50"
                    >
                      查看
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(material.id);
                      }}
                      className="px-3 py-1 text-sm text-red-600 border border-red-200 rounded hover:bg-red-50"
                    >
                      删除
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 上传弹窗 */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b">
              <h2 className="text-lg font-semibold">上传素材</h2>
              <button onClick={() => setShowUploadModal(false)}>
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">素材名称 *</label>
                <input
                  type="text"
                  value={uploadForm.name}
                  onChange={(e) => setUploadForm({ ...uploadForm, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded"
                  placeholder="请输入素材名称"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">素材类型 *</label>
                <select
                  value={uploadForm.material_type}
                  onChange={(e) => setUploadForm({ ...uploadForm, material_type: e.target.value as MaterialType })}
                  className="w-full px-3 py-2 border border-gray-300 rounded"
                >
                  {MATERIAL_TABS.filter(t => t.key !== 'all').map(tab => (
                    <option key={tab.key} value={tab.key}>{tab.label}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">描述</label>
                <textarea
                  value={uploadForm.description}
                  onChange={(e) => setUploadForm({ ...uploadForm, description: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded"
                  rows={3}
                  placeholder="请输入素材描述"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">选择文件 *</label>
                <input
                  type="file"
                  onChange={(e) => setUploadForm({ ...uploadForm, file: e.target.files?.[0] || null })}
                  className="w-full px-3 py-2 border border-gray-300 rounded"
                />
              </div>
              
              {uploadForm.material_type === 'case' && (
                <>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-1">合同金额</label>
                      <input
                        type="number"
                        value={uploadForm.contract_amount || ''}
                        onChange={(e) => setUploadForm({ ...uploadForm, contract_amount: Number(e.target.value) || undefined })}
                        className="w-full px-3 py-2 border border-gray-300 rounded"
                        placeholder="请输入金额"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">完工日期</label>
                      <input
                        type="date"
                        value={uploadForm.completion_date}
                        onChange={(e) => setUploadForm({ ...uploadForm, completion_date: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded"
                      />
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium mb-1">客户名称</label>
                    <input
                      type="text"
                      value={uploadForm.client_name}
                      onChange={(e) => setUploadForm({ ...uploadForm, client_name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded"
                      placeholder="请输入客户名称"
                    />
                  </div>
                </>
              )}
              
              {uploadForm.material_type === 'product' && (
                <div>
                  <label className="block text-sm font-medium mb-1">产品型号</label>
                  <input
                    type="text"
                    value={uploadForm.model_number}
                    onChange={(e) => setUploadForm({ ...uploadForm, model_number: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded"
                    placeholder="请输入产品型号"
                  />
                </div>
              )}
              
              <div>
                <label className="block text-sm font-medium mb-1">标签（用逗号分隔）</label>
                <input
                  type="text"
                  value={uploadForm.tags}
                  onChange={(e) => setUploadForm({ ...uploadForm, tags: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded"
                  placeholder="例如: 重点,2024,市政"
                />
              </div>
              
              {uploading && (
                <div>
                  <div className="flex justify-between text-sm text-gray-600 mb-1">
                    <span>上传进度</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <div className="w-full h-2 bg-gray-200 rounded overflow-hidden">
                    <div
                      className="h-full bg-blue-500 transition-all"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
            
            <div className="flex justify-end gap-3 px-6 py-4 border-t bg-gray-50">
              <button
                onClick={() => setShowUploadModal(false)}
                className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
              >
                取消
              </button>
              <button
                onClick={handleUpload}
                disabled={uploading}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {uploading ? '上传中...' : '确认上传'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 详情弹窗 */}
      {showDetailModal && selectedMaterial && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b">
              <h2 className="text-lg font-semibold">{selectedMaterial.name}</h2>
              <button onClick={() => setShowDetailModal(false)}>
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-gray-500">类型：</span>
                  <span>{MATERIAL_TABS.find(t => t.key === selectedMaterial.material_type)?.label}</span>
                </div>
                <div>
                  <span className="text-gray-500">创建时间：</span>
                  <span>{new Date(selectedMaterial.created_at).toLocaleString()}</span>
                </div>
                {selectedMaterial.contract_amount && (
                  <div>
                    <span className="text-gray-500">合同金额：</span>
                    <span>¥{selectedMaterial.contract_amount.toLocaleString()}</span>
                  </div>
                )}
                {selectedMaterial.completion_date && (
                  <div>
                    <span className="text-gray-500">完工日期：</span>
                    <span>{selectedMaterial.completion_date}</span>
                  </div>
                )}
                {selectedMaterial.client_name && (
                  <div className="col-span-2">
                    <span className="text-gray-500">客户名称：</span>
                    <span>{selectedMaterial.client_name}</span>
                  </div>
                )}
              </div>
              
              {selectedMaterial.description && (
                <div>
                  <h3 className="font-medium mb-2">描述</h3>
                  <p className="text-gray-600">{selectedMaterial.description}</p>
                </div>
              )}
              
              {selectedMaterial.content && (
                <div>
                  <h3 className="font-medium mb-2">内容预览</h3>
                  <div className="bg-gray-50 p-4 rounded max-h-60 overflow-y-auto">
                    <pre className="text-sm whitespace-pre-wrap">{selectedMaterial.content}</pre>
                  </div>
                </div>
              )}
              
              {selectedMaterial.tags && selectedMaterial.tags.length > 0 && (
                <div>
                  <span className="text-gray-500">标签：</span>
                  <div className="inline-flex gap-1 mt-1">
                    {selectedMaterial.tags.map((tag, idx) => (
                      <span key={idx} className="px-2 py-1 bg-gray-100 text-sm rounded">
                        {tag}
                      </span>
                    ))}
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

export default Materials;
