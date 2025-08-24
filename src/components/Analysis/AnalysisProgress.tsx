import React from 'react';
import { Card } from '../Common';

interface AnalysisStage {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  startTime?: Date;
  endTime?: Date;
  error?: string;
  agent?: string;
}

interface AnalysisProgressProps {
  stages: AnalysisStage[];
  overallProgress: number;
  currentStage: string;
  estimatedTimeRemaining?: number;
  className?: string;
}

const AnalysisProgress: React.FC<AnalysisProgressProps> = ({
  stages,
  overallProgress,
  currentStage,
  estimatedTimeRemaining,
  className = '',
}) => {
  const getStageIcon = (status: AnalysisStage['status']) => {
    switch (status) {
      case 'completed':
        return '✅';
      case 'running':
        return '🔄';
      case 'failed':
        return '❌';
      default:
        return '⏳';
    }
  };

  const getStageStatusColor = (status: AnalysisStage['status']) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'running':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'failed':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const formatDuration = (minutes: number) => {
    if (minutes < 60) {
      return `${Math.round(minutes)}분`;
    }
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = Math.round(minutes % 60);
    return `${hours}시간 ${remainingMinutes}분`;
  };

  const getAgentIcon = (agent: string) => {
    const icons: Record<string, string> = {
      'agenda_miner': '🔍',
      'claim_checker': '✅',
      'counter_arguer': '🔄',
      'evidence_hunter': '📚',
      'summarizer': '📝',
    };
    return icons[agent] || '🤖';
  };

  return (
    <Card className={`${className}`}>
      {/* Overall Progress */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-semibold text-gray-900">전체 분석 진행률</h3>
          <span className="text-2xl font-bold text-blue-600">{overallProgress}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className={`h-3 rounded-full transition-all duration-300 ${
              overallProgress === 100 ? 'bg-green-500' : 'bg-blue-500'
            }`}
            style={{ width: `${overallProgress}%` }}
          />
        </div>
        {estimatedTimeRemaining && (
          <p className="text-sm text-gray-600 mt-2">
            예상 완료 시간: {formatDuration(estimatedTimeRemaining)}
          </p>
        )}
      </div>

      {/* Current Stage */}
      <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <div className="flex items-center space-x-3">
          <div className="text-2xl">🔄</div>
          <div>
            <h4 className="font-medium text-blue-900">현재 진행 중</h4>
            <p className="text-sm text-blue-700">{currentStage}</p>
          </div>
        </div>
      </div>

      {/* Individual Stages */}
      <div className="space-y-4">
        <h4 className="font-medium text-gray-900">단계별 진행 상황</h4>
        {stages.map((stage) => (
          <div
            key={stage.id}
            className={`p-4 rounded-lg border transition-all duration-200 ${
              stage.status === 'running'
                ? 'border-blue-200 bg-blue-50'
                : stage.status === 'completed'
                ? 'border-green-200 bg-green-50'
                : stage.status === 'failed'
                ? 'border-red-200 bg-red-50'
                : 'border-gray-200 bg-gray-50'
            }`}
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center space-x-3">
                <div className="text-xl">{getStageIcon(stage.status)}</div>
                <div>
                  <h5 className="font-medium text-gray-900">{stage.name}</h5>
                  <p className="text-sm text-gray-600">{stage.description}</p>
                  {stage.agent && (
                    <div className="flex items-center space-x-1 mt-1">
                      <span className="text-sm">{getAgentIcon(stage.agent)}</span>
                      <span className="text-xs text-gray-500">{stage.agent}</span>
                    </div>
                  )}
                </div>
              </div>
              <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getStageStatusColor(stage.status)}`}>
                {stage.status === 'completed' && '완료'}
                {stage.status === 'running' && '진행 중'}
                {stage.status === 'failed' && '실패'}
                {stage.status === 'pending' && '대기 중'}
              </span>
            </div>

            {/* Progress Bar */}
            {stage.status !== 'pending' && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm text-gray-600">
                  <span>진행률</span>
                  <span>{stage.progress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-300 ${
                      stage.status === 'completed'
                        ? 'bg-green-500'
                        : stage.status === 'failed'
                        ? 'bg-red-500'
                        : 'bg-blue-500'
                    }`}
                    style={{ width: `${stage.progress}%` }}
                  />
                </div>
              </div>
            )}

            {/* Timing Information */}
            {stage.startTime && (
              <div className="mt-3 pt-3 border-t border-gray-200">
                <div className="flex justify-between text-xs text-gray-500">
                  <span>시작: {stage.startTime.toLocaleTimeString()}</span>
                  {stage.endTime && (
                    <span>완료: {stage.endTime.toLocaleTimeString()}</span>
                  )}
                </div>
              </div>
            )}

            {/* Error Information */}
            {stage.error && (
              <div className="mt-3 p-3 bg-red-100 rounded border border-red-200">
                <div className="flex items-center space-x-2">
                  <span className="text-red-600">❌</span>
                  <span className="text-sm text-red-800">{stage.error}</span>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Analysis Tips */}
      <div className="mt-6 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
        <div className="flex items-start space-x-3">
          <div className="text-xl">💡</div>
          <div>
            <h4 className="font-medium text-yellow-900">분석 팁</h4>
            <ul className="text-sm text-yellow-800 mt-2 space-y-1">
              <li>• 각 단계는 순차적으로 진행됩니다</li>
              <li>• 화자 분리는 가장 시간이 오래 걸립니다</li>
              <li>• AI 에이전트 분석은 회의 길이에 따라 달라집니다</li>
              <li>• 분석 중에는 브라우저를 닫지 마세요</li>
            </ul>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default AnalysisProgress;

