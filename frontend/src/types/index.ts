// TypeScript types for the CRDB Tuning Report Generator API

export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  created_at: string;
}

export interface Report {
  id: string;
  cluster_id: string;
  title: string;
  description?: string;
  status: 'draft' | 'in_review' | 'published' | 'archived';
  generated_at?: string;
  version: number;
  metadata?: Record<string, any>;
  created_by: string;
  status_changed_by?: string;
  status_changed_at?: string;
  created_at: string;
  updated_at: string;
  findings?: Finding[];
  comments?: Comment[];
  status_history?: ReportStatusHistory[];
}

export interface Finding {
  id: string;
  report_id: string;
  category: 'performance' | 'configuration' | 'security' | 'reliability' | 'monitoring';
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  details?: Record<string, any>;
  status: 'open' | 'acknowledged' | 'resolved' | 'false_positive';
  tags?: string[];
  created_by: string;
  created_at: string;
  updated_at: string;
  actions?: RecommendedAction[];
}

export interface RecommendedAction {
  id: string;
  finding_id: string;
  title: string;
  description: string;
  action_type: 'configuration_change' | 'query_optimization' | 'index_creation' | 'hardware_upgrade' | 'monitoring_setup' | 'backup_strategy' | 'security_hardening';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  estimated_effort: 'low' | 'medium' | 'high';
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  due_date?: string;
  completed_at?: string;
  implementation_notes?: string;
  created_by: string;
  status_changed_by?: string;
  status_changed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface Comment {
  id: string;
  report_id: string;
  parent_comment_id?: string;
  author_id: string;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface ReportStatusHistory {
  id: string;
  report_id: string;
  old_status?: string;
  new_status: string;
  changed_by: string;
  change_reason?: string;
  created_at: string;
}

export interface FindingStatusHistory {
  id: string;
  finding_id: string;
  old_status?: string;
  new_status: string;
  changed_by: string;
  change_reason?: string;
  created_at: string;
}

export interface ActionStatusHistory {
  id: string;
  action_id: string;
  old_status?: string;
  new_status: string;
  changed_by: string;
  change_reason?: string;
  created_at: string;
}

// Request types for creating/updating entities
export interface CreateReportRequest {
  cluster_id: string;
  title: string;
  description?: string;
}

export interface UpdateReportRequest {
  title?: string;
  description?: string;
  status?: 'draft' | 'in_review' | 'published' | 'archived';
}

export interface CreateFindingRequest {
  category: 'performance' | 'configuration' | 'security' | 'reliability' | 'monitoring';
  severity?: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  tags?: string[];
}

export interface UpdateFindingRequest {
  category?: 'performance' | 'configuration' | 'security' | 'reliability' | 'monitoring';
  severity?: 'low' | 'medium' | 'high' | 'critical';
  title?: string;
  description?: string;
  status?: 'open' | 'acknowledged' | 'resolved' | 'false_positive';
  tags?: string[];
}

export interface CreateActionRequest {
  title: string;
  description: string;
  action_type: 'configuration_change' | 'query_optimization' | 'index_creation' | 'hardware_upgrade' | 'monitoring_setup' | 'backup_strategy' | 'security_hardening';
  priority?: 'low' | 'medium' | 'high' | 'urgent';
  estimated_effort?: 'low' | 'medium' | 'high';
  due_date?: string;
}

export interface UpdateActionRequest {
  title?: string;
  description?: string;
  action_type?: 'configuration_change' | 'query_optimization' | 'index_creation' | 'hardware_upgrade' | 'monitoring_setup' | 'backup_strategy' | 'security_hardening';
  priority?: 'low' | 'medium' | 'high' | 'urgent';
  estimated_effort?: 'low' | 'medium' | 'high';
  status?: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  due_date?: string;
  implementation_notes?: string;
}

export interface CreateCommentRequest {
  content: string;
  parent_comment_id?: string;
}

// API Response types
export interface ApiResponse<T> {
  data?: T;
  message?: string;
  error?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}
