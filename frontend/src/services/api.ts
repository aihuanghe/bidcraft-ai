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

// 智能上传：自动选择普通或分片上传
export const smartUpload = {
  upload: async (
    file: File,
    onProgress?: (progress: number, uploaded: number, total: number) => void
  ): Promise<{ fileUrl?: string; fileContent?: string }> => {
    // 小文件直接上传
    if (file.size <= CHUNKED_THRESHOLD) {
      const formData = new FormData();
      formData.append('file', file);
      const response = await api.post<any>('/api/document/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return { fileContent: response.data.file_content };
    }

    // 大文件分片上传
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

export default api;
