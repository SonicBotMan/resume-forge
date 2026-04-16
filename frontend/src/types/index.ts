export interface Material {
  id: string
  user_id: string
  name: string
  source_type: string
  file_path: string | null
  file_size: number | null
  text_content: string | null
  analysis_status: 'pending' | 'analyzing' | 'success' | 'failed'
  analysis_error: string | null
  analyzed_at: string | null
  created_at: string
  updated_at: string
}

export interface JD {
  id: string
  user_id: string
  title: string
  company: string | null
  jd_text: string
  is_parsed: boolean
  parsed_data: string | object | null
  created_at: string
  updated_at: string
}

export interface BaseResume {
  id: string
  user_id: string
  content: object | null
  version: number
  generation_status: 'pending' | 'generating' | 'success' | 'failed'
  generation_error?: string | null
  source_material_ids?: string[]
  created_at: string
  updated_at: string
}

export interface TargetedResume {
  id: string
  user_id: string
  jd_id: string
  name?: string
  content?: object
  grade?: 'A' | 'B' | 'C' | 'D' | ''
  recommendation?: string | null
  match_result?: object
  adjustment_report?: {
    summary: string
    adjustments: { area: string; action: string; reason: string; emphasis: string }[]
    packaging: string
    risk_note: string
  } | null
  version?: number
  jd_title?: string
  generation_status?: 'pending' | 'generating' | 'success' | 'failed'
  generation_error?: string | null
  created_at: string
  updated_at: string
}

export interface AnalysisStatus {
  material_id: string
  status: string
  message?: string | null
  error?: string | null
}

export interface Review {
  id: string
  user_id: string
  resume_id: string
  resume_type: 'base' | 'targeted'
  status: 'pending' | 'running' | 'completed' | 'failed'
  results: object | null
  resume_name?: string | null
  jd_title?: string | null
  created_at: string
  updated_at: string
}
