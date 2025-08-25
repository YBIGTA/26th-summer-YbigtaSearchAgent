// 회의 관련 타입 정의

export interface Meeting {
  id: string;
  title: string;
  date: string;
  duration: number;
  speakers: number;
  status: 'completed' | 'processing' | 'error' | 'pending';
  summary?: string;
  job_id?: string;
  progress?: number;
  current_stage?: string;
  error_message?: string;
  audio_file?: string;
}

export interface MeetingAnalysis {
  id: string;
  meeting_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  current_stage: string;
  started_at: string;
  completed_at?: string;
  error?: string;
  
  // 에이전트별 결과
  agenda_miner?: AgendaMinerResult;
  claim_checker?: ClaimCheckerResult;
  counter_arguer?: CounterArguerResult;
  evidence_hunter?: EvidenceHunterResult;
  summarizer?: SummarizerResult;
}

export interface AgendaMinerResult {
  agendas: string[];
  topics: Topic[];
  priority_levels: PriorityLevel[];
  time_estimates: TimeEstimate[];
}

export interface Topic {
  id: string;
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  estimated_duration: number;
  speakers: string[];
  start_time: number;
  end_time: number;
}

export interface PriorityLevel {
  level: 'high' | 'medium' | 'low';
  topics: string[];
  reasoning: string;
}

export interface TimeEstimate {
  topic_id: string;
  estimated_minutes: number;
  actual_minutes: number;
  variance: number;
}

export interface ClaimCheckerResult {
  claims: Claim[];
  evidence_quality: EvidenceQuality[];
  verification_status: VerificationStatus[];
}

export interface Claim {
  id: string;
  statement: string;
  speaker: string;
  timestamp: number;
  confidence: number;
  evidence_sources: string[];
  verification_result: 'verified' | 'unverified' | 'contradicted';
  reasoning: string;
}

export interface EvidenceQuality {
  claim_id: string;
  quality_score: number;
  source_reliability: number;
  supporting_evidence: string[];
  contradicting_evidence: string[];
}

export interface VerificationStatus {
  claim_id: string;
  status: 'pending' | 'verified' | 'unverified' | 'contradicted';
  verification_method: string;
  verified_at?: string;
  verifier?: string;
}

export interface CounterArguerResult {
  counter_arguments: CounterArgument[];
  logical_fallacies: LogicalFallacy[];
  alternative_perspectives: AlternativePerspective[];
}

export interface CounterArgument {
  id: string;
  original_claim: string;
  counter_statement: string;
  reasoning: string;
  strength: 'weak' | 'moderate' | 'strong';
  supporting_evidence: string[];
  speaker_suggestion: string;
}

export interface LogicalFallacy {
  id: string;
  fallacy_type: string;
  description: string;
  example_from_transcript: string;
  correction_suggestion: string;
  severity: 'minor' | 'moderate' | 'major';
}

export interface AlternativePerspective {
  id: string;
  original_viewpoint: string;
  alternative_viewpoint: string;
  reasoning: string;
  supporting_arguments: string[];
  speaker_suggestion: string;
}

export interface EvidenceHunterResult {
  evidence_collection: EvidenceItem[];
  source_analysis: SourceAnalysis[];
  credibility_assessment: CredibilityAssessment[];
}

export interface EvidenceItem {
  id: string;
  content: string;
  source: string;
  source_type: 'notion' | 'github' | 'google_drive' | 'internal';
  relevance_score: number;
  credibility_score: number;
  last_updated: string;
  url?: string;
}

export interface SourceAnalysis {
  source_id: string;
  source_name: string;
  source_type: string;
  document_count: number;
  last_sync: string;
  reliability_score: number;
  coverage_areas: string[];
}

export interface CredibilityAssessment {
  evidence_id: string;
  overall_score: number;
  factors: {
    source_reliability: number;
    recency: number;
    consistency: number;
    expertise: number;
  };
  recommendations: string[];
}

export interface SummarizerResult {
  executive_summary: string;
  key_points: string[];
  action_items: ActionItem[];
  decisions_made: Decision[];
  next_steps: NextStep[];
  risk_assessment: RiskAssessment[];
  report_metadata: ReportMetadata;
}

export interface ActionItem {
  id: string;
  description: string;
  assignee: string;
  due_date: string;
  priority: 'high' | 'medium' | 'low';
  status: 'pending' | 'in_progress' | 'completed';
  dependencies: string[];
  notes: string;
}

export interface Decision {
  id: string;
  decision: string;
  rationale: string;
  decision_maker: string;
  timestamp: number;
  alternatives_considered: string[];
  impact_assessment: string;
}

export interface NextStep {
  id: string;
  description: string;
  timeline: string;
  responsible_party: string;
  prerequisites: string[];
  success_criteria: string[];
}

export interface RiskAssessment {
  id: string;
  risk_description: string;
  probability: 'low' | 'medium' | 'high';
  impact: 'low' | 'medium' | 'high';
  mitigation_strategy: string;
  responsible_party: string;
  timeline: string;
}

export interface ReportMetadata {
  generated_at: string;
  analysis_duration: number;
  agents_used: string[];
  confidence_score: number;
  data_sources: string[];
  version: string;
}
