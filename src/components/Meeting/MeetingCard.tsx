import React from 'react';
import { Meeting } from '../../types/meeting';
import { Card } from '../Common';
import { formatDuration, formatDate } from '../../utils/format';

interface MeetingCardProps {
  meeting: Meeting;
  onClick?: () => void;
  showActions?: boolean;
  onAnalyze?: () => void;
  onView?: () => void;
}

const MeetingCard: React.FC<MeetingCardProps> = ({
  meeting,
  onClick,
  showActions = true,
  onAnalyze,
  onView,
}) => {
  const getStatusColor = (status: Meeting['status']) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'processing':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'error':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusText = (status: Meeting['status']) => {
    switch (status) {
      case 'completed':
        return '완료';
      case 'processing':
        return '분석 중';
      case 'error':
        return '오류';
      default:
        return '대기 중';
    }
  };

  return (
    <Card
      className="h-full"
      onClick={onClick}
      hoverable={!!onClick}
    >
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-gray-900 truncate">
              {meeting.title}
            </h3>
            <p className="text-sm text-gray-500 mt-1">
              {formatDate(meeting.date)}
            </p>
          </div>
          <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getStatusColor(meeting.status)}`}>
            {getStatusText(meeting.status)}
          </span>
        </div>

        {/* Details */}
        <div className="flex-1 space-y-2">
          <div className="flex items-center text-sm text-gray-600">
            <span className="mr-2">⏱️</span>
            <span>{formatDuration(meeting.duration)}</span>
          </div>
          <div className="flex items-center text-sm text-gray-600">
            <span className="mr-2">👥</span>
            <span>참석자 {meeting.speakers}명</span>
          </div>
          {meeting.progress !== undefined && meeting.status === 'processing' && (
            <div className="space-y-1">
              <div className="flex justify-between text-sm text-gray-600">
                <span>진행률</span>
                <span>{meeting.progress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${meeting.progress}%` }}
                />
              </div>
            </div>
          )}
          {meeting.current_stage && meeting.status === 'processing' && (
            <div className="text-sm text-gray-600">
              <span className="mr-2">🔄</span>
              <span>{meeting.current_stage}</span>
            </div>
          )}
          {meeting.summary && (
            <div className="text-sm text-gray-700 bg-gray-50 p-2 rounded">
              {meeting.summary}
            </div>
          )}
        </div>

        {/* Actions */}
        {showActions && (
          <div className="flex items-center justify-between mt-4 pt-3 border-t border-gray-200">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onView?.();
              }}
              className="text-sm text-blue-600 hover:text-blue-800 transition-colors"
            >
              상세보기
            </button>
            {meeting.status === 'completed' && onAnalyze && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onAnalyze?.();
                }}
                className="text-sm text-green-600 hover:text-green-800 transition-colors"
              >
                재분석
              </button>
            )}
          </div>
        )}
      </div>
    </Card>
  );
};

export default MeetingCard;

