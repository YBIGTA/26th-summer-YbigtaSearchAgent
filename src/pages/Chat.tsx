import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useApi } from '../context/ApiContext';

interface ChatMessage {
  id: string;
  type: 'user' | 'ai';
  content: string;
  timestamp: Date;
  metadata?: {
    sources?: string[];
    confidence?: number;
    processing_time?: number;
  };
}

const Chat: React.FC = () => {
  const { searchDocuments, getChatResponse } = useApi();
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      type: 'ai',
      content: '안녕하세요! 회의록 분석 결과와 YBIGTA DB를 기반으로 질문에 답변드리겠습니다. 무엇을 도와드릴까요?',
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 자동 스크롤
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 메시지 전송
  const handleSendMessage = useCallback(async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      // AI 응답 생성 (시뮬레이션)
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const aiResponse: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: `"${inputValue.trim()}"에 대한 답변입니다. YBIGTA DB와 회의록 분석 결과를 기반으로 답변드렸습니다.`,
        timestamp: new Date(),
        metadata: {
          sources: ['YBIGTA_Project_2024', 'Meeting_Log_001'],
          confidence: 0.92,
          processing_time: 1200
        }
      };

      setMessages(prev => [...prev, aiResponse]);
    } catch (error) {
      console.error('AI 응답 생성 오류:', error);
    } finally {
      setIsLoading(false);
    }
  }, [inputValue, isLoading]);

  // 엔터키 처리
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div style={{ 
      maxWidth: '1200px', 
      margin: '0 auto', 
      padding: '20px',
      backgroundColor: '#f8f9fa',
      minHeight: '100vh'
    }}>
      {/* 헤더 */}
      <div style={{ 
        textAlign: 'center',
        marginBottom: '32px',
        padding: '24px',
        backgroundColor: 'white',
        borderRadius: '16px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)'
      }}>
        <h1 style={{ 
          fontSize: '32px', 
          fontWeight: '700', 
          marginBottom: '12px',
          color: '#667eea'
        }}>
          💬 AI 인사이트 채팅
        </h1>
        <p style={{ color: '#6c757d', fontSize: '18px' }}>
          회의록 분석 결과와 YBIGTA DB를 기반으로 한 지능형 채팅
        </p>
      </div>

      <div style={{ display: 'flex', gap: '24px' }}>
        {/* 채팅 메인 영역 */}
        <div style={{ flex: 1 }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '20px',
            boxShadow: '0 10px 25px rgba(0, 0, 0, 0.1)',
            overflow: 'hidden'
          }}>
            {/* 채팅 헤더 */}
            <div style={{
              padding: '20px',
              borderBottom: '1px solid #e9ecef',
              backgroundColor: '#f8f9fa'
            }}>
              <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#495057' }}>
                💬 AI 채팅
              </h2>
            </div>
            
            {/* 채팅 메시지 영역 */}
            <div style={{ 
              height: '500px',
              overflowY: 'auto',
              padding: '20px',
              backgroundColor: '#fafafa'
            }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {messages.map((message) => (
                  <div
                    key={message.id}
                    style={{
                      display: 'flex',
                      justifyContent: message.type === 'user' ? 'flex-end' : 'flex-start',
                      gap: '12px',
                      alignItems: 'flex-end'
                    }}
                  >
                    {/* AI 아바타 */}
                    {message.type === 'ai' && (
                      <div style={{
                        width: '40px',
                        height: '40px',
                        borderRadius: '50%',
                        backgroundColor: '#667eea',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0
                      }}>
                        <span style={{ color: 'white', fontSize: '16px', fontWeight: 'bold' }}>AI</span>
                      </div>
                    )}
                    
                    {/* 메시지 버블 */}
                    <div
                      style={{
                        maxWidth: '70%',
                        padding: '16px 20px',
                        borderRadius: message.type === 'user' ? '20px 20px 4px 20px' : '20px 20px 20px 4px',
                        backgroundColor: message.type === 'user' ? '#667eea' : 'white',
                        color: message.type === 'user' ? 'white' : '#424242',
                        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                        border: message.type === 'ai' ? '1px solid #e9ecef' : 'none'
                      }}
                    >
                      <div style={{ 
                        whiteSpace: 'pre-wrap', 
                        lineHeight: '1.6',
                        fontSize: '14px'
                      }}>
                        {message.content}
                      </div>
                      
                      <div style={{
                        fontSize: '11px',
                        color: message.type === 'user' ? 'rgba(255,255,255,0.8)' : '#9e9e9e',
                        marginTop: '8px',
                        textAlign: 'right'
                      }}>
                        {message.timestamp.toLocaleTimeString('ko-KR', { 
                          hour: '2-digit', 
                          minute: '2-digit' 
                        })}
                      </div>
                      
                      {/* AI 메시지 메타데이터 */}
                      {message.type === 'ai' && message.metadata && (
                        <div style={{
                          marginTop: '12px',
                          paddingTop: '12px',
                          borderTop: '1px solid #f0f0f0'
                        }}>
                          <div style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            fontSize: '11px',
                            color: '#757575'
                          }}>
                            <span>신뢰도: {(message.metadata.confidence! * 100).toFixed(0)}%</span>
                            <span>처리시간: {message.metadata.processing_time}ms</span>
                          </div>
                        </div>
                      )}
                    </div>
                    
                    {/* 사용자 아바타 */}
                    {message.type === 'user' && (
                      <div style={{
                        width: '40px',
                        height: '40px',
                        borderRadius: '50%',
                        backgroundColor: '#764ba2',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0
                      }}>
                        <span style={{ color: 'white', fontSize: '14px', fontWeight: 'bold' }}>나</span>
                      </div>
                    )}
                  </div>
                ))}
                
                {/* 로딩 인디케이터 */}
                {isLoading && (
                  <div style={{
                    display: 'flex',
                    justifyContent: 'flex-start',
                    gap: '12px',
                    alignItems: 'flex-end'
                  }}>
                    <div style={{
                      width: '40px',
                      height: '40px',
                      borderRadius: '50%',
                      backgroundColor: '#667eea',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <span style={{ color: 'white', fontSize: '16px', fontWeight: 'bold' }}>AI</span>
                    </div>
                    <div style={{
                      padding: '16px 20px',
                      backgroundColor: 'white',
                      borderRadius: '20px 20px 20px 4px',
                      border: '1px solid #e9ecef',
                      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px'
                    }}>
                      <div style={{
                        width: '20px',
                        height: '20px',
                        border: '2px solid #667eea',
                        borderTop: '2px solid transparent',
                        borderRadius: '50%',
                        animation: 'spin 1s linear infinite'
                      }} />
                      <span style={{ color: '#424242', fontSize: '14px' }}>
                        AI가 답변을 생성하고 있습니다...
                      </span>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>
            </div>

            {/* 입력 영역 */}
            <div style={{
              padding: '20px',
              borderTop: '1px solid #e9ecef',
              backgroundColor: 'white'
            }}>
              <div style={{
                display: 'flex',
                gap: '12px',
                alignItems: 'center'
              }}>
                <input
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="질문을 입력하세요..."
                  disabled={isLoading}
                  style={{
                    flex: 1,
                    padding: '16px 20px',
                    border: '2px solid #e9ecef',
                    borderRadius: '25px',
                    fontSize: '16px',
                    outline: 'none',
                    transition: 'all 0.2s ease'
                  }}
                  onFocus={(e) => e.target.style.borderColor = '#667eea'}
                  onBlur={(e) => e.target.style.borderColor = '#e9ecef'}
                />
                <button
                  onClick={handleSendMessage}
                  disabled={!inputValue.trim() || isLoading}
                  style={{
                    padding: '16px 24px',
                    backgroundColor: inputValue.trim() && !isLoading ? '#667eea' : '#e9ecef',
                    color: 'white',
                    border: 'none',
                    borderRadius: '25px',
                    fontSize: '16px',
                    fontWeight: '600',
                    cursor: inputValue.trim() && !isLoading ? 'pointer' : 'not-allowed',
                    transition: 'all 0.2s ease',
                    minWidth: '120px'
                  }}
                >
                  {isLoading ? '전송 중...' : '전송'}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* 사이드바 */}
        <div style={{ width: '300px' }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '16px',
            padding: '20px',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)'
          }}>
            <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px', color: '#495057' }}>
              📝 최근 대화
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {messages.slice(-3).map((message) => (
                <div key={message.id} style={{
                  padding: '8px 12px',
                  backgroundColor: '#f8f9fa',
                  borderRadius: '8px',
                  border: '1px solid #e9ecef'
                }}>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    marginBottom: '4px'
                  }}>
                    <span style={{
                      fontSize: '10px',
                      padding: '2px 6px',
                      borderRadius: '8px',
                      backgroundColor: message.type === 'user' ? '#e3f2fd' : '#f3e5f5',
                      color: message.type === 'user' ? '#1976d2' : '#7b1fa2'
                    }}>
                      {message.type === 'user' ? '사용자' : 'AI'}
                    </span>
                    <span style={{ fontSize: '10px', color: '#9e9e9e' }}>
                      {message.timestamp.toLocaleTimeString('ko-KR', { 
                        hour: '2-digit', 
                        minute: '2-digit' 
                      })}
                    </span>
                  </div>
                  <p style={{
                    fontSize: '11px',
                    color: '#424242',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                  }}>
                    {message.content.length > 30 
                      ? message.content.substring(0, 30) + '...' 
                      : message.content
                    }
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* CSS 애니메이션을 위한 스타일 태그 */}
      <style dangerouslySetInnerHTML={{
        __html: `
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `
      }} />
    </div>
  );
};

export default Chat;

export {};
