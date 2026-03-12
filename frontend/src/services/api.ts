/**
 * API服务
 */
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
});

// 响应拦截器
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API请求错误:', error);
    return Promise.reject(error);
  }
);

export interface ConfigData {
  api_key: string;
  base_url?: string;
  model_name: string;
}

export interface ProviderConfig {
  api_key: string;
  base_url?: string;
  model_name: string;
  enabled: boolean;
  fallback?: string[];
}

export interface LLMConfig {
  providers: Record<string, ProviderConfig>;
  default_provider?: string;
  failover_enabled: boolean;
}

export interface FileUploadResponse {
  success: boolean;
  message: string;
  file_content?: string;
  old_outline?: string;
}

export interface AnalysisRequest {
  file_content: string;
  analysis_type: 'overview' | 'requirements';
}

export interface OutlineRequest {
  overview: string;
  requirements: string;
  uploaded_expand?: boolean;
  old_outline?: string;
  old_document?: string;
}

export interface ContentGenerationRequest {
  outline: { outline: any[] };
  project_overview: string;
}

export interface ChapterContentRequest {
  chapter: any;
  parent_chapters?: any[];
  sibling_chapters?: any[];
  project_overview: string;
}

export interface TemplateRecommendation {
  templates: Array<{
    id: number;
    name: string;
    type: string;
    score: number;
    reasons: string[];
    recommendation: string;
  }>;
  recommended_template_id?: number;
  confidence: number;
  industry: string;
}

// 分片上传配置
const CHUNK_SIZE = 5 * 1024 * 1024; // 5MB
const CHUNKED_THRESHOLD = 10 * 1024 * 1024; // 10MB
const MAX_CONCURRENT = 3;

// 配置相关API
export const configApi = {
  saveConfig: (config: ConfigData) =>
    api.post('/api/config/save', config),
  loadConfig: () =>
    api.get('/api/config/load'),
  getModels: (config: ConfigData) =>
    api.post('/api/config/models', config),
};

// 文档相关API
export const documentApi = {
  uploadFile: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<FileUploadResponse>('/api/document/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  analyzeDocumentStream: (data: AnalysisRequest) =>
    fetch(`${API_BASE_URL}/api/document/analyze-stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  exportWord: (data: any) =>
    fetch(`${API_BASE_URL}/api/document/export-word`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),
};

// 分片上传API
export const chunkedUploadApi = {
  // 初始化上传
  initUpload: (filename: string, fileSize: number, contentType: string = 'application/octet-stream') =>
    api.post('/api/upload/chunked/init', {
      filename,
      file_size: fileSize,
      content_type: contentType,
    }),

  // 上传分片
  uploadPart: (uploadId: string, partNumber: number, chunk: Blob) => {
    const formData = new FormData();
    formData.append('file', chunk);
    return api.post(`/api/upload/chunked/part/file?upload_id=${uploadId}&part_number=${partNumber}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  // 完成上传
  completeUpload: (uploadId: string) =>
    api.post('/api/upload/chunked/complete', { upload_id: uploadId }),

  // 获取上传状态
  getUploadStatus: (uploadId: string) =>
    api.get(`/api/upload/chunked/status/${uploadId}`),

  // 取消上传
  cancelUpload: (uploadId: string) =>
    api.delete(`/api/upload/chunked/${uploadId}`),
};

// 智能上传：Word文档大文件使用分片上传，PDF直接上传
export const smartUpload = {
  upload: async (
    file: File,
    onProgress?: (progress: number, uploaded: number, total: number) => void
  ): Promise<{ fileUrl?: string; fileContent?: string }> => {
    const isWordDoc = file.name.match(/\.(docx|doc)$/i);
    const isPdf = file.name.match(/\.pdf$/i);
    
    // PDF文件：直接上传（不支持分片）
    if (isPdf) {
      const formData = new FormData();
      formData.append('file', file);
      const response = await api.post<any>('/api/document/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 300000, // PDF大文件增加超时时间
      });
      return { fileContent: response.data.file_content };
    }
    
    // Word文档小文件：直接上传
    if (isWordDoc && file.size <= CHUNKED_THRESHOLD) {
      const formData = new FormData();
      formData.append('file', file);
      const response = await api.post<any>('/api/document/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return { fileContent: response.data.file_content };
    }
    
    // Word文档大文件(>10MB)：使用分片上传
    const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
    
    // 初始化上传
    const initResponse = await chunkedUploadApi.initUpload(file.name, file.size, file.type);
    const { upload_id, chunk_size } = initResponse.data.data;

    // 获取已上传的分片（断点续传）
    let statusResponse;
    try {
      statusResponse = await chunkedUploadApi.getUploadStatus(upload_id);
      var uploadedParts = statusResponse.data.data.uploaded_chunks || [];
    } catch {
      uploadedParts = [];
    }

    // 上传剩余分片
    const uploadPromises: Promise<any>[] = [];
    let uploadedCount = uploadedParts.length;

    for (let i = 0; i < totalChunks; i++) {
      if (uploadedParts.includes(i + 1)) {
        continue;
      }

      const start = i * chunk_size;
      const end = Math.min(start + chunk_size, file.size);
      const chunk = file.slice(start, end);

      const promise = chunkedUploadApi
        .uploadPart(upload_id, i + 1, chunk)
        .then(() => {
          uploadedCount++;
          if (onProgress) {
            onProgress((uploadedCount / totalChunks) * 100, uploadedCount, totalChunks);
          }
        })
        .catch((error) => {
          console.error(`分片 ${i + 1} 上传失败:`, error);
          throw error;
        });

      uploadPromises.push(promise);

      // 控制并发数
      if (uploadPromises.length >= MAX_CONCURRENT || i === totalChunks - 1) {
        await Promise.all(uploadPromises);
        uploadPromises.length = 0;
      }
    }

    // 完成上传
    const completeResponse = await chunkedUploadApi.completeUpload(upload_id);
    const { file_url, skip_upload } = completeResponse.data.data;

    if (skip_upload) {
      // 秒传成功，需要获取文件内容
      return { fileUrl: file_url };
    }

    // 如果是本地文件，需要处理文本提取
    if (!file_url.startsWith('http')) {
      return { fileUrl: file_url };
    }

    return { fileUrl: file_url };
  },
};

// 目录相关API
export const outlineApi = {
  generateOutline: (data: OutlineRequest) =>
    api.post('/api/outline/generate', data),
  generateOutlineStream: (data: OutlineRequest) =>
    fetch(`${API_BASE_URL}/api/outline/generate-stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),
};

// 内容相关API
export const contentApi = {
  generateChapterContent: (data: ChapterContentRequest) =>
    api.post('/api/content/generate-chapter', data),
  generateChapterContentStream: (data: ChapterContentRequest) =>
    fetch(`${API_BASE_URL}/api/content/generate-chapter-stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),
};

// 方案扩写相关API
export const expandApi = {
  uploadExpandFile: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<FileUploadResponse>('/api/expand/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300000,
    });
  },
};

// 模板相关API
export const templateApi = {
  extractTemplate: (documentId: number) =>
    api.post('/api/templates/extract', { document_id: documentId }),

  getTemplateRecommendation: (documentId: number) =>
    api.get<TemplateRecommendation>(`/api/templates/document/${documentId}/recommendation`),

  selectTemplate: (projectId: number, templateId: number, templateSource: string) =>
    api.post('/api/templates/select', {
      project_id: projectId,
      template_id: templateId,
      template_source: templateSource
    }),

  generateOutline: (projectId: number, templateId: number, technicalScores: any, projectOverview: string) =>
    api.post('/api/templates/outline/generate', {
      project_id: projectId,
      template_id: templateId,
      technical_scores: technicalScores,
      project_overview: projectOverview
    }),

  generateContent: (projectId: number, chapter: any, projectInfo: any, enterpriseData?: any, similarCases?: any[]) =>
    api.post('/api/templates/content/generate', {
      project_id: projectId,
      chapter,
      project_info: projectInfo,
      enterprise_data: enterpriseData,
      similar_cases: similarCases
    }),

  generateContentStream: (projectId: number, chapter: any, projectInfo: any, enterpriseData?: any, similarCases?: any[]) =>
    fetch(`${API_BASE_URL}/api/templates/content/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        project_id: projectId,
        chapter,
        project_info: projectInfo,
        enterprise_data: enterpriseData,
        similar_cases: similarCases
      }),
    }),

  generateDeviationTable: (projectId: number, technicalScores: any) =>
    api.post(`/api/templates/deviation/generate?project_id=${projectId}`, technicalScores),

  saveDeviationMappings: (projectId: number, mappings: any[]) =>
    api.post('/api/templates/deviation/mappings', {
      project_id: projectId,
      mappings
    }),

  getDeviationTable: (projectId: number) =>
    api.get(`/api/templates/deviation/${projectId}`),

  exportDocument: (projectId: number, format: 'docx' | 'pdf' = 'docx') =>
    api.get(`/api/templates/export/${projectId}?format=${format}`),
};

// LLM统一接入层API
export const llmApi = {
  // 获取Provider列表
  getProviders: () => api.get('/api/llm/providers'),
  
  // 获取路由配置
  getRouting: () => api.get('/api/llm/routing'),
  
  // 获取使用统计
  getUsage: (days: number = 30) => api.get(`/api/llm/usage?days=${days}`),
  
  // 更新Provider配置
  updateProviderConfig: (config: LLMConfig) => api.post('/api/llm/config/providers', config),
  
  // 测试Provider连接
  testProvider: (providerType: string, apiKey: string, baseUrl: string, modelName: string) =>
    api.post('/api/llm/providers/test', {
      provider_type: providerType,
      api_key: apiKey,
      base_url: baseUrl,
      model_name: modelName
    }),
  
  // 获取Provider支持的模型
  getModels: (providerType: string) => api.get(`/api/llm/models/${providerType}`),
  
  // 选择Provider
  selectProvider: (providerType: string) => api.post(`/api/llm/router/select?provider_type=${providerType}`),
  
  // 通用聊天
  chat: (messages: any[], taskType: string = 'general', providerType?: string) =>
    api.post('/api/llm/chat', {
      messages,
      task_type: taskType,
      provider_type: providerType
    }),
};

// 企业数据管理API
export const enterpriseApi = {
  // 获取项目占位符
  getProjectPlaceholders: (projectId: number, templateStructure?: string) => 
    api.get(`/api/enterprise/projects/${projectId}/placeholders`, {
      params: templateStructure ? { template_structure: templateStructure } : {}
    }),
  
  // 填充占位符
  fillPlaceholder: (projectId: number, placeholderId: string, value: any, mode: string = 'manual') =>
    api.post(`/api/enterprise/projects/${projectId}/placeholders/${placeholderId}/fill`, {
      value,
      mode
    }),
  
  // RAG自动填充
  autoFillPlaceholder: (projectId: number, placeholderId: string, query: string, topK: number = 3) =>
    api.post(`/api/enterprise/projects/${projectId}/placeholders/${placeholderId}/auto-fill`, {
      query,
      top_k: topK
    }),
  
  // 获取占位符值
  getPlaceholderValues: (projectId: number) =>
    api.get(`/api/enterprise/projects/${projectId}/placeholder-values`),
  
  // RAG检索
  searchMaterials: (query: string, materialType?: string, filters?: any, topK: number = 5) =>
    api.post('/api/enterprise/materials/search', {
      query,
      material_type: materialType,
      filters,
      top_k: topK
    }),
  
  // 获取素材列表
  getMaterials: (params?: any) =>
    api.get('/api/enterprise/materials/', { params }),
  
  // 上传素材
  uploadMaterial: (formData: FormData) =>
    api.post('/api/enterprise/materials/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),
  
  // 获取素材类型
  getMaterialTypes: () =>
    api.get('/api/enterprise/materials/types'),
};

export default api;
