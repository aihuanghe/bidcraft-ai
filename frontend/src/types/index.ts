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