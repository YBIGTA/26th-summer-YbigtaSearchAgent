// 포맷팅 유틸리티 함수들

export const formatDate = (dateString: string | Date): string => {
  const date = typeof dateString === 'string' ? new Date(dateString) : dateString;
  
  if (isNaN(date.getTime())) {
    return '날짜 없음';
  }

  const now = new Date();
  const diffTime = Math.abs(now.getTime() - date.getTime());
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

  if (diffDays === 1) {
    return '어제';
  } else if (diffDays === 0) {
    return '오늘';
  } else if (diffDays < 7) {
    return `${diffDays}일 전`;
  } else if (diffDays < 30) {
    const weeks = Math.floor(diffDays / 7);
    return `${weeks}주 전`;
  } else if (diffDays < 365) {
    const months = Math.floor(diffDays / 30);
    return `${months}개월 전`;
  } else {
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }
};

export const formatDateTime = (dateString: string | Date): string => {
  const date = typeof dateString === 'string' ? new Date(dateString) : dateString;
  
  if (isNaN(date.getTime())) {
    return '날짜 없음';
  }

  const now = new Date();
  const diffTime = Math.abs(now.getTime() - date.getTime());
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

  if (diffDays === 0) {
    return `오늘 ${date.toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit'
    })}`;
  } else if (diffDays === 1) {
    return `어제 ${date.toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit'
    })}`;
  } else {
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
};

export const formatDuration = (seconds: number): string => {
  if (seconds < 60) {
    return `${seconds}초`;
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    if (remainingSeconds === 0) {
      return `${minutes}분`;
    }
    return `${minutes}분 ${remainingSeconds}초`;
  } else {
    const hours = Math.floor(seconds / 3600);
    const remainingMinutes = Math.floor((seconds % 3600) / 60);
    if (remainingMinutes === 0) {
      return `${hours}시간`;
    }
    return `${hours}시간 ${remainingMinutes}분`;
  }
};

export const formatDurationShort = (seconds: number): string => {
  if (seconds < 60) {
    return `${seconds}s`;
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60);
    return `${minutes}m`;
  } else {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (minutes === 0) {
      return `${hours}h`;
    }
    return `${hours}h ${minutes}m`;
  }
};

export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
};

export const formatPercentage = (value: number, total: number): string => {
  if (total === 0) return '0%';
  const percentage = (value / total) * 100;
  return `${percentage.toFixed(1)}%`;
};

export const formatConfidence = (confidence: number): string => {
  if (confidence >= 0.9) return '매우 높음';
  if (confidence >= 0.7) return '높음';
  if (confidence >= 0.5) return '보통';
  if (confidence >= 0.3) return '낮음';
  return '매우 낮음';
};

export const formatPriority = (priority: string): string => {
  const priorityMap: Record<string, string> = {
    'high': '높음',
    'medium': '보통',
    'low': '낮음',
    'urgent': '긴급',
    'normal': '일반'
  };
  return priorityMap[priority] || priority;
};

export const formatStatus = (status: string): string => {
  const statusMap: Record<string, string> = {
    'completed': '완료',
    'processing': '처리 중',
    'pending': '대기 중',
    'failed': '실패',
    'cancelled': '취소됨',
    'error': '오류'
  };
  return statusMap[status] || status;
};

export const formatAgentName = (agent: string): string => {
  const agentMap: Record<string, string> = {
    'agenda_miner': '안건 추출기',
    'claim_checker': '주장 검증기',
    'counter_arguer': '반박 생성기',
    'evidence_hunter': '증거 수집기',
    'summarizer': '요약 생성기'
  };
  return agentMap[agent] || agent;
};

export const formatSourceType = (source: string): string => {
  const sourceMap: Record<string, string> = {
    'notion': 'Notion',
    'github': 'GitHub',
    'google_drive': 'Google Drive',
    'meetings': '회의록',
    'internal': '내부 문서'
  };
  return sourceMap[source] || source;
};

export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

export const capitalizeFirst = (text: string): string => {
  if (!text) return text;
  return text.charAt(0).toUpperCase() + text.slice(1);
};

export const formatTimeRange = (startTime: number, endTime: number): string => {
  const start = Math.floor(startTime / 60);
  const startSeconds = Math.floor(startTime % 60);
  const end = Math.floor(endTime / 60);
  const endSeconds = Math.floor(endTime % 60);
  
  return `${start}:${startSeconds.toString().padStart(2, '0')} - ${end}:${endSeconds.toString().padStart(2, '0')}`;
};

