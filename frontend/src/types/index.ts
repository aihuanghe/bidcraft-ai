/**
 * 类型定义
 */

export interface ConfigData {
  api_key: string;
  base_url?: string;
  model_name: string;
}

export interface OutlineItem {
  id: string;
  title: string;
  description: string;
  children?: OutlineItem[];
  content?: string;
}

export interface OutlineData {
  outline: OutlineItem[];
  project_name?: string;
  project_overview?: string;
}

export interface AppState {
  currentStep: number;
  config: ConfigData;
  fileContent: string;
  projectOverview: string;
  techRequirements: string;
  outlineData: OutlineData | null;
  selectedChapter: string;
}

// ========== 模板相关 ==========
export interface ExtractedTemplate {
  id: number;
  name: string;
  template_type: 'extracted' | 'builtin' | 'custom';
  description?: string;
  industry?: string;
  structure_json?: {
    sections: TemplateSection[];
    chapter_info: any;
  };
  style_rules?: any;
  confidence_score?: number;
}

export interface TemplateSection {
  type: 'letter' | 'business' | 'technical' | 'price' | 'other';
  title: string;
  content?: string;
  has_table?: boolean;
  table_format?: any;
  requirements?: string[];
}

export interface TemplateRecommendation {
  templates: {
    id: number;
    name: string;
    type: string;
    score: number;
    reasons: string[];
    recommendation: string;
  }[];
  recommended_template_id?: number;
  confidence: number;
  industry: string;
}

export interface TemplateOutline {
  template_id: number;
  template_name: string;
  generated_at: string;
  chapters: TemplateChapter[];
  has_deviation_table: boolean;
}

export interface TemplateChapter {
  id: string;
  chapter_id: string;
  title: string;
  level: number;
  type: string;
  template_snippet?: string;
  ai_prompt?: string;
  placeholders?: string[];
  required: boolean;
  children?: TemplateChapter[];
  has_table?: boolean;
  table_format?: any;
  content_source?: string;
  content?: string;
}

// ========== 偏离表相关 ==========
export interface DeviationItem {
  id: number;
  deviation_type: 'technical' | 'business';
  tender_requirement: string;
  tender_description?: string;
  bid_response: string;
  deviation_status: 'none' | 'positive' | 'negative';
  chapter_path: string;
  chapter_title: string;
  is_confirmed: boolean;
}

// ========== 企业素材相关 ==========
export type MaterialType = 'case' | 'certificate' | 'qualification' | 'personnel' | 'finance' | 'product' | 'other';

export interface EnterpriseMaterial {
  id: number;
  name: string;
  material_type: MaterialType;
  description?: string;
  content?: string;
  file_url?: string;
  contract_amount?: number;
  completion_date?: string;
  client_name?: string;
  model_number?: string;
  technical_params?: Record<string, any>;
  tags?: string[];
  created_at: string;
  updated_at: string;
  bid_project_id?: number;
}

export interface MaterialSearchParams {
  query?: string;
  material_type?: MaterialType;
  tags?: string[];
  date_from?: string;
  date_to?: string;
  amount_min?: number;
  amount_max?: number;
  page?: number;
  page_size?: number;
}

export interface MaterialUploadRequest {
  name: string;
  material_type: MaterialType;
  description?: string;
  file?: File;
  contract_amount?: number;
  completion_date?: string;
  client_name?: string;
  model_number?: string;
  technical_params?: Record<string, any>;
  tags?: string[];
  bid_project_id?: number;
}

// ========== 占位符相关 ==========
export type PlaceholderType = 'manual' | 'rag' | 'erp' | 'hr' | 'finance';

export interface Placeholder {
  id: string;
  name: string;
  type: PlaceholderType;
  value?: string;
  status: 'pending' | 'filled' | 'failed';
  source?: string;
  confidence?: number;
  suggestions?: string[];
}

export interface PlaceholderFillRequest {
  value: any;
  mode: 'manual' | 'rag' | 'erp' | 'hr' | 'finance';
}

// ========== 项目相关 ==========
export interface BidProject {
  id: number;
  name: string;
  status: 'draft' | 'analyzing' | 'outlining' | 'generating' | 'completed' | 'exported';
  overview?: string;
  requirements?: string;
  template_id?: number;
  created_at: string;
  updated_at: string;
  placeholder_values?: Record<string, any>;
}

// ========== 大纲树相关 ==========
export interface OutlineTreeItem extends OutlineItem {
  level: number;
  isExpanded?: boolean;
  isGenerating?: boolean;
  hasContent?: boolean;
  placeholderCount?: number;
  filledPlaceholderCount?: number;
}

// ========== 生成进度相关 ==========
export interface GenerationProgress {
  total_chapters: number;
  completed_chapters: number;
  current_chapter?: string;
  status: 'idle' | 'generating' | 'completed' | 'failed';
  error?: string;
  tokens_used?: number;
}