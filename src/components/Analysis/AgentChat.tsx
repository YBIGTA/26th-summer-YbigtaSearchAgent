import React, { useState, useRef, useEffect } from 'react';
import { Button, Input, Card } from '../Common';

interface AgentMessage {
  id: string;
  agent: string;
  content: string;
  timestamp: Date;
  type: 'user' | 'agent' | 'system';
  metadata?: {
    confidence?: number;
    sources?: string[];
    reasoning?: string;
  };
}

interface AgentChatProps {
  agentName: string;
  agentDescription: string;
  messages: AgentMessage[];
  onSendMessage: (message: string) => void;
  isLoading?: boolean;
  className?: string;
}

const AgentChat: React.FC<AgentChatProps> = ({
  agentName,
  agentDescription,
  messages,
  onSendMessage,
  isLoading = false,
  className = '',
}) => {
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = () => {
    if (inputMessage.trim()) {
      onSendMessage(inputMessage.trim());
      setInputMessage('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const getAgentIcon = (agent: string) => {
    const icons: Record<string, string> = {
      'agenda_miner': '🔍',
      'claim_checker': '✅',
      'counter_arguer': '🔄',
      'evidence_hunter': '📚',
      'summarizer': '📝',
      'user': '👤',
      'system': '⚙️',
    };
    return icons[agent] || '🤖';
  };

  const getMessageStyle = (type: AgentMessage['type']) => {
    switch (type) {
      case 'user':
        return 'bg-blue-100 border-blue-200 ml-12';
      case 'agent':
        return 'bg-gray-100 border-gray-200 mr-12';
      case 'system':
        return 'bg-yellow-100 border-yellow-200 mx-auto max-w-2xl';
      default:
        return 'bg-gray-100 border-gray-200';
    }
  };

  return (
    <Card className={`h-full flex flex-col ${className}`}>
      {/* Header */}
      <div className="border-b border-gray-200 p-4">
        <div className="flex items-center space-x-3">
          <div className="text-2xl">{getAgentIcon(agentName)}</div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{agentName}</h3>
            <p className="text-sm text-gray-600">{agentDescription}</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`p-3 rounded-lg border ${getMessageStyle(message.type)}`}
          >
            <div className="flex items-start space-x-2">
              <div className="text-lg">{getAgentIcon(message.agent)}</div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2 mb-1">
                  <span className="font-medium text-gray-900">
                    {message.agent === 'user' ? '사용자' : 
                     message.agent === 'system' ? '시스템' : agentName}
                  </span>
                  <span className="text-xs text-gray-500">
                    {message.timestamp.toLocaleTimeString()}
                  </span>
                </div>
                <div className="text-gray-800 whitespace-pre-wrap">
                  {message.content}
                </div>
                
                {/* Metadata */}
                {message.metadata && (
                  <div className="mt-2 pt-2 border-t border-gray-200">
                    {message.metadata.confidence !== undefined && (
                      <div className="text-xs text-gray-600">
                        신뢰도: {Math.round(message.metadata.confidence * 100)}%
                      </div>
                    )}
                    {message.metadata.sources && message.metadata.sources.length > 0 && (
                      <div className="text-xs text-gray-600 mt-1">
                        출처: {message.metadata.sources.join(', ')}
                      </div>
                    )}
                    {message.metadata.reasoning && (
                      <details className="mt-1">
                        <summary className="text-xs text-gray-600 cursor-pointer hover:text-gray-800">
                          추론 과정 보기
                        </summary>
                        <div className="text-xs text-gray-700 mt-1 p-2 bg-gray-50 rounded">
                          {message.metadata.reasoning}
                        </div>
                      </details>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex items-center space-x-2 text-gray-600">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
            <span className="text-sm">에이전트가 응답을 생성하고 있습니다...</span>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-4">
        <div className="flex space-x-2">
          <Input
            type="text"
            placeholder="에이전트에게 질문하세요..."
            value={inputMessage}
            onChange={setInputMessage}
            onKeyPress={handleKeyPress}
            className="flex-1"
            disabled={isLoading}
          />
          <Button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isLoading}
            loading={isLoading}
          >
            전송
          </Button>
        </div>
      </div>
    </Card>
  );
};

export default AgentChat;

