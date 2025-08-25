import React, { useState, useEffect } from 'react';

interface Project {
  title: string;
  description: string;
  type: string;
  url?: string;
  last_updated: string;
  source?: string;  // 검색 결과에서 추가되는 속성
  id?: string;      // 고유 식별자
  content_hash?: string;  // 콘텐츠 해시
}

interface ProjectsData {
  projects: {
    github: Project[];
    notion: Project[];
    gdrive: Project[];
  };
}

const DatabaseExplorer: React.FC = () => {
  const [projectsData, setProjectsData] = useState<ProjectsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedSource, setSelectedSource] = useState<'all' | 'github' | 'gdrive' | 'notion'>('all');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [selectedProject, setSelectedProject] = useState<any>(null);
  const [showProjectModal, setShowProjectModal] = useState(false);

  // 실제 ChromaDB 검색
  const performSearch = async (query: string) => {
    if (!query.trim()) {
      setShowSearchResults(false);
      return;
    }

    setIsSearching(true);
    console.log('통합 검색 시작:', query);
    
    try {
      // 프로젝트 데이터에서 직접 검색 (더 정확하고 빠름)
      const filteredProjects = [];
      const searchTerm = query.trim().toLowerCase();
      
      // GitHub 프로젝트에서 검색
      if (projectsData?.projects?.github) {
        const githubResults = projectsData.projects.github.filter(project => 
          project.title.toLowerCase().includes(searchTerm) ||
          project.description.toLowerCase().includes(searchTerm) ||
          project.type.toLowerCase().includes(searchTerm)
        );
        filteredProjects.push(...githubResults.map(p => ({ ...p, source: 'github' })));
      }
      
      // Google Drive 프로젝트에서 검색  
      if (projectsData?.projects?.gdrive) {
        const gdriveResults = projectsData.projects.gdrive.filter(project => 
          project.title.toLowerCase().includes(searchTerm) ||
          project.description.toLowerCase().includes(searchTerm) ||
          project.type.toLowerCase().includes(searchTerm)
        );
        filteredProjects.push(...gdriveResults.map(p => ({ ...p, source: 'gdrive' })));
      }
      
      console.log(`통합 검색 완료: "${searchTerm}"에 대해 ${filteredProjects.length}개 결과 발견`);
      setSearchResults(filteredProjects);
      setShowSearchResults(true);
      
    } catch (error) {
      console.error('통합 검색 오류:', error);
      alert(`검색 오류: ${error}`);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  // 프로젝트 메타데이터 기반 검색 (더 실용적)
  const performVectorSearch = async (query: string) => {
    if (!query.trim()) {
      setShowSearchResults(false);
      return;
    }

    setIsSearching(true);
    console.log('프로젝트 검색 시작:', query);
    
    try {
      // 프로젝트 데이터에서 직접 검색
      const filteredProjects = [];
      const searchTerm = query.trim().toLowerCase();
      
      // GitHub 프로젝트에서 검색
      if (projectsData?.projects?.github) {
        const githubResults = projectsData.projects.github.filter(project => 
          project.title.toLowerCase().includes(searchTerm) ||
          project.description.toLowerCase().includes(searchTerm) ||
          project.type.toLowerCase().includes(searchTerm)
        );
        filteredProjects.push(...githubResults.map(p => ({ ...p, source: 'github' })));
      }
      
      // Google Drive 프로젝트에서 검색
      if (projectsData?.projects?.gdrive) {
        const gdriveResults = projectsData.projects.gdrive.filter(project => 
          project.title.toLowerCase().includes(searchTerm) ||
          project.description.toLowerCase().includes(searchTerm) ||
          project.type.toLowerCase().includes(searchTerm)
        );
        filteredProjects.push(...gdriveResults.map(p => ({ ...p, source: 'gdrive' })));
      }
      
      console.log(`검색 완료: "${searchTerm}"에 대해 ${filteredProjects.length}개 결과 발견`);
      setSearchResults(filteredProjects);
      setShowSearchResults(true);
      
    } catch (error) {
      console.error('프로젝트 검색 오류:', error);
      alert(`검색 오류: ${error}`);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  // 엔터키 검색
  const handleSearchKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      performSearch(searchQuery);
    }
  };

  // 프로젝트 카드 클릭 핸들러
  const handleProjectClick = (project: any) => {
    setSelectedProject(project);
    setShowProjectModal(true);
  };

  // 모달 닫기
  const closeProjectModal = () => {
    setSelectedProject(null);
    setShowProjectModal(false);
  };

  // GitHub 링크 열기
  const openGitHubLink = (project: any) => {
    const githubUrl = `https://github.com/YBIGTA/${project.title}`;
    window.open(githubUrl, '_blank');
  };

  // 프로젝트 데이터 로드
  useEffect(() => {
    const fetchProjects = async () => {
      setIsLoading(true);
      try {
        // 먼저 실제 ChromaDB 데이터 시도
        const realResponse = await fetch(`${process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000'}/api/knowledge/projects/real`);
        if (realResponse.ok) {
          const realData = await realResponse.json();
          // 실제 데이터가 있으면 사용
          if (realData.projects.github.length > 0 || realData.projects.notion.length > 0 || realData.projects.gdrive.length > 0) {
            console.log('✅ ChromaDB에서 실제 데이터 로드 성공');
            setProjectsData(realData);
            return;
          }
        }
        
        // 실제 데이터가 없으면 기존 API 시도
        console.log('⚠️ 실제 데이터 없음, 기존 API 시도');
        const response = await fetch(`${process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000'}/api/knowledge/projects`);
        if (response.ok) {
          const data = await response.json();
          setProjectsData(data);
        } else {
          console.error('프로젝트 데이터 로드 실패');
          setProjectsData(null);
        }
      } catch (error) {
        console.error('프로젝트 데이터 로드 오류:', error);
        setProjectsData(null);
      } finally {
        setIsLoading(false);
      }
    };

    fetchProjects();
  }, []);



  // 소스별 아이콘과 색상
  const getSourceInfo = (source: string) => {
    switch (source) {
      case 'github':
        return { icon: '📁', color: '#333', name: 'GitHub' };
      case 'gdrive':
        return { icon: '📄', color: '#4285f4', name: 'Google Drive' };
      case 'meeting':
        return { icon: '🎤', color: '#e91e63', name: '회의록' };
      default:
        return { icon: '📋', color: '#9e9e9e', name: '기타' };
    }
  };

  // 프로젝트 타입별 색상
  const getTypeColor = (type: string) => {
    switch (type) {
      case 'AI/ML':
        return '#4caf50';
      case 'Web Development':
        return '#2196f3';
      case 'Data Science':
        return '#ff9800';
      case 'Study/Education':
        return '#9c27b0';
      case 'YBIGTA Project':
        return '#f44336';
      default:
        return '#607d8b';
    }
  };

  // 필터링된 프로젝트 목록
  const getFilteredProjects = (): Project[] => {
    if (!projectsData) return [];

    let allProjects: Project[] = [];
    
    if (selectedSource === 'all') {
      allProjects = [
        ...projectsData.projects.github,
        ...projectsData.projects.gdrive,
        ...projectsData.projects.notion
      ];
    } else {
      allProjects = projectsData.projects[selectedSource] || [];
    }

    // 타입 필터링
    if (selectedType !== 'all') {
      allProjects = allProjects.filter(project => project.type === selectedType);
    }

    // 검색 필터링
    if (searchQuery) {
      allProjects = allProjects.filter(project => 
        project.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        project.description.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    return allProjects;
  };

  // 고유한 프로젝트 타입 목록
  const getUniqueTypes = (): string[] => {
    if (!projectsData) return [];
    
    const allProjects = [
      ...projectsData.projects.github,
      ...projectsData.projects.gdrive,
      ...projectsData.projects.notion
    ];
    
    const uniqueTypes = new Set(allProjects.map(project => project.type));
    return Array.from(uniqueTypes);
  };

  if (isLoading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '400px',
        backgroundColor: '#f8f9fa'
      }}>
        <div style={{
          textAlign: 'center',
          color: '#6c757d'
        }}>
          <div style={{
            width: '50px',
            height: '50px',
            border: '4px solid #e9ecef',
            borderTop: '4px solid #007bff',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 16px'
          }} />
          <p>ChromaDB 프로젝트를 로딩하고 있습니다...</p>
        </div>
      </div>
    );
  }

  const filteredProjects = getFilteredProjects();

  return (
    <div style={{ 
      maxWidth: '1400px', 
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
          color: '#495057'
        }}>
          🔍 DB조회 GUI
        </h1>
        <p style={{ color: '#6c757d', fontSize: '18px' }}>
          YBIGTA ChromaDB에 저장된 프로젝트와 문서를 탐색해보세요
        </p>
      </div>

      {/* 통계 카드 */}
      {projectsData && (
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
          gap: '16px',
          marginBottom: '32px'
        }}>
          <div style={{
            padding: '20px',
            backgroundColor: 'white',
            borderRadius: '12px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#495057' }}>
              {(projectsData.projects.github?.length || 0) + (projectsData.projects.gdrive?.length || 0) + (projectsData.projects.notion?.length || 0)}
            </div>
            <div style={{ fontSize: '14px', color: '#6c757d' }}>총 프로젝트</div>
          </div>
          
          <div style={{
            padding: '20px',
            backgroundColor: 'white',
            borderRadius: '12px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#333' }}>
              {projectsData.projects.github?.length || 0}
            </div>
            <div style={{ fontSize: '14px', color: '#6c757d' }}>GitHub 저장소</div>
          </div>
          
          <div style={{
            padding: '20px',
            backgroundColor: 'white',
            borderRadius: '12px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#4285f4' }}>
              {projectsData.projects.gdrive?.length || 0}
            </div>
            <div style={{ fontSize: '14px', color: '#6c757d' }}>Google Drive</div>
          </div>
          
          <div style={{
            padding: '20px',
            backgroundColor: 'white',
            borderRadius: '12px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#e91e63' }}>
              {projectsData.projects.notion?.length || 0}
            </div>
            <div style={{ fontSize: '14px', color: '#6c757d' }}>Notion</div>
          </div>
        </div>
      )}

      {/* 필터 및 검색 */}
      <div style={{
        backgroundColor: 'white',
        padding: '24px',
        borderRadius: '16px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)',
        marginBottom: '32px'
      }}>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
          gap: '16px',
          alignItems: 'end'
        }}>
          {/* 소스 필터 */}
          <div>
            <label style={{ 
              display: 'block', 
              marginBottom: '8px', 
              fontSize: '14px', 
              fontWeight: '600',
              color: '#495057'
            }}>
              소스 필터
            </label>
            <select
              value={selectedSource}
              onChange={(e) => setSelectedSource(e.target.value as any)}
              style={{
                width: '100%',
                padding: '12px',
                border: '2px solid #e9ecef',
                borderRadius: '8px',
                fontSize: '14px',
                backgroundColor: 'white'
              }}
            >
              <option value="all">전체 소스</option>
              <option value="github">GitHub</option>
              <option value="gdrive">Google Drive</option>
              <option value="notion">Notion</option>
            </select>
          </div>

          {/* 타입 필터 */}
          <div>
            <label style={{ 
              display: 'block', 
              marginBottom: '8px', 
              fontSize: '14px', 
              fontWeight: '600',
              color: '#495057'
            }}>
              프로젝트 타입
            </label>
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              style={{
                width: '100%',
                padding: '12px',
                border: '2px solid #e9ecef',
                borderRadius: '8px',
                fontSize: '14px',
                backgroundColor: 'white'
              }}
            >
              <option value="all">전체 타입</option>
              {getUniqueTypes().map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>

          {/* 검색 */}
          <div>
            <label style={{ 
              display: 'block', 
              marginBottom: '8px', 
              fontSize: '14px', 
              fontWeight: '600',
              color: '#495057'
            }}>
              프로젝트 검색
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={handleSearchKeyPress}
                placeholder="ChromaDB에서 검색... (엔터키로 검색)"
                style={{
                  width: '100%',
                  padding: '12px 50px 12px 12px',
                  border: '2px solid #e9ecef',
                  borderRadius: '8px',
                  fontSize: '14px'
                }}
              />
              <div style={{ 
                position: 'absolute',
                right: '8px',
                top: '50%',
                transform: 'translateY(-50%)',
                display: 'flex',
                gap: '4px'
              }}>
                           <button
             onClick={() => performSearch(searchQuery)}
             disabled={isSearching}
             title="통합 검색 (제목, 설명, 타입)"
             style={{
               padding: '8px',
               backgroundColor: '#007bff',
               color: 'white',
               border: 'none',
               borderRadius: '4px',
               cursor: isSearching ? 'not-allowed' : 'pointer',
               fontSize: '12px'
             }}
           >
             {isSearching ? '🔄' : '🔍'}
           </button>
           <button
             onClick={() => performVectorSearch(searchQuery)}
             disabled={isSearching}
             title="고급 검색 (프로젝트 메타데이터)"
             style={{
               padding: '8px',
               backgroundColor: '#28a745',
               color: 'white',
               border: 'none',
               borderRadius: '4px',
               cursor: isSearching ? 'not-allowed' : 'pointer',
               fontSize: '12px'
             }}
           >
             📊
           </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 검색 결과 섹션 */}
      {showSearchResults && (
        <div style={{
          backgroundColor: 'white',
          padding: '24px',
          borderRadius: '16px',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)',
          marginBottom: '32px'
        }}>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            marginBottom: '20px'
          }}>
            <h2 style={{
              fontSize: '24px',
              fontWeight: '600',
              color: '#495057',
              margin: 0
            }}>
              🔍 "{searchQuery}" 검색 결과
            </h2>
            <button
              onClick={() => setShowSearchResults(false)}
              style={{
                padding: '8px 16px',
                backgroundColor: '#f8f9fa',
                border: '1px solid #dee2e6',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              ✕ 닫기
            </button>
          </div>
          
          {searchResults.length > 0 ? (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
              gap: '16px'
            }}>
              {searchResults.map((result, index) => (
                <div
                  key={index}
                  style={{
                    padding: '20px',
                    border: '1px solid #e9ecef',
                    borderRadius: '12px',
                    backgroundColor: '#f8f9fa'
                  }}
                >
                  <div style={{
                    fontSize: '16px',
                    fontWeight: '600',
                    color: '#495057',
                    marginBottom: '8px'
                  }}>
                    {result.metadata?.title || '제목 없음'}
                  </div>
                  <div style={{
                    fontSize: '12px',
                    color: '#6c757d',
                    marginBottom: '12px'
                  }}>
                    출처: {result.metadata?.source || '알 수 없음'}
                  </div>
                  <div style={{
                    fontSize: '14px',
                    color: '#495057',
                    lineHeight: '1.5',
                    maxHeight: '100px',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis'
                  }}>
                    {result.page_content || result.content || '내용 없음'}
                  </div>
                  {result.score && (
                    <div style={{
                      fontSize: '11px',
                      color: '#9e9e9e',
                      marginTop: '8px',
                      textAlign: 'right'
                    }}>
                      관련도: {(result.score * 100).toFixed(1)}%
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div style={{
              textAlign: 'center',
              padding: '40px',
              color: '#6c757d'
            }}>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔍</div>
              <p>검색 결과가 없습니다.</p>
            </div>
          )}
        </div>
      )}

      {/* 프로젝트 카드 그리드 */}
      {!showSearchResults && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
          gap: '20px'
        }}>
                {filteredProjects.map((project) => {
          const sourceInfo = getSourceInfo(project.source || 'unknown');
          const typeColor = getTypeColor(project.type);

          return (
            <div
              key={project.id || project.title}
              onClick={() => handleProjectClick(project)}
              style={{
                backgroundColor: 'white',
                borderRadius: '16px',
                padding: '24px',
                boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                border: '1px solid #e9ecef',
                transition: 'all 0.3s ease',
                cursor: 'pointer'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-4px)';
                e.currentTarget.style.boxShadow = '0 8px 25px rgba(0,0,0,0.15)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
              }}
            >
              {/* 헤더 */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                marginBottom: '16px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span style={{ 
                    fontSize: '28px',
                    color: sourceInfo.color
                  }}>
                    {sourceInfo.icon}
                  </span>
                  <div>
                    <h3 style={{
                      fontSize: '18px',
                      fontWeight: '600',
                      color: '#495057',
                      margin: '0 0 4px 0',
                      lineHeight: '1.2'
                    }}>
                      {project.title.length > 30 
                        ? project.title.substring(0, 30) + '...' 
                        : project.title
                      }
                    </h3>
                    <span style={{
                      fontSize: '12px',
                      color: sourceInfo.color,
                      fontWeight: '500'
                    }}>
                      {sourceInfo.name}
                    </span>
                  </div>
                </div>
                
                <span style={{
                  padding: '4px 8px',
                  backgroundColor: typeColor,
                  color: 'white',
                  borderRadius: '12px',
                  fontSize: '11px',
                  fontWeight: '600',
                  whiteSpace: 'nowrap'
                }}>
                  {project.type}
                </span>
              </div>

              {/* 설명 */}
              <p style={{
                fontSize: '14px',
                color: '#6c757d',
                lineHeight: '1.5',
                marginBottom: '16px',
                minHeight: '42px'
              }}>
                {project.description}
              </p>

              {/* 메타데이터 */}
              <div style={{
                fontSize: '12px',
                color: '#9e9e9e',
                borderTop: '1px solid #f0f0f0',
                paddingTop: '12px'
              }}>
                <div style={{ marginBottom: '4px' }}>
                  <strong>마지막 업데이트:</strong> {' '}
                  {new Date(project.last_updated).toLocaleDateString('ko-KR')}
                </div>
                {project.url && (
                  <div style={{ marginBottom: '4px' }}>
                    <strong>링크:</strong> {' '}
                    <a 
                      href={project.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      style={{ color: '#007bff', textDecoration: 'none' }}
                    >
                      {project.url}
                    </a>
                  </div>
                )}
              </div>
            </div>
          );
        })}
        </div>
      )}

      {/* 결과 없음 메시지 */}
      {!showSearchResults && filteredProjects.length === 0 && !isLoading && (
        <div style={{
          textAlign: 'center',
          padding: '60px 20px',
          backgroundColor: 'white',
          borderRadius: '16px',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)'
        }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔍</div>
          <h3 style={{ fontSize: '24px', marginBottom: '8px', color: '#495057' }}>
            검색 결과가 없습니다
          </h3>
          <p style={{ color: '#6c757d', fontSize: '16px' }}>
            다른 검색어나 필터를 시도해보세요.
          </p>
        </div>
      )}

      {/* CSS 애니메이션 */}
      <style dangerouslySetInnerHTML={{
        __html: `
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `
      }} />

      {/* 프로젝트 상세 정보 모달 */}
      {showProjectModal && selectedProject && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '16px',
            padding: '32px',
            maxWidth: '600px',
            maxHeight: '80vh',
            overflow: 'auto',
            margin: '20px',
            position: 'relative',
            boxShadow: '0 20px 60px rgba(0, 0, 0, 0.2)'
          }}>
            {/* 모달 헤더 */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
              marginBottom: '24px'
            }}>
              <div>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  marginBottom: '8px'
                }}>
                  <span style={{ 
                    fontSize: '32px',
                    color: getSourceInfo(selectedProject.source).color
                  }}>
                    {getSourceInfo(selectedProject.source).icon}
                  </span>
                  <h2 style={{
                    margin: 0,
                    fontSize: '24px',
                    fontWeight: 'bold',
                    color: '#2c3e50'
                  }}>
                    {selectedProject.title}
                  </h2>
                </div>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <span style={{
                    padding: '4px 12px',
                    borderRadius: '20px',
                    backgroundColor: getTypeColor(selectedProject.type),
                    color: 'white',
                    fontSize: '12px',
                    fontWeight: '500'
                  }}>
                    {selectedProject.type}
                  </span>
                  <span style={{
                    fontSize: '14px',
                    color: '#6c757d'
                  }}>
                    {getSourceInfo(selectedProject.source).name}
                  </span>
                </div>
              </div>
              
              <button
                onClick={closeProjectModal}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '24px',
                  cursor: 'pointer',
                  padding: '4px',
                  color: '#6c757d',
                  borderRadius: '50%',
                  width: '40px',
                  height: '40px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f8f9fa'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
              >
                ✕
              </button>
            </div>

            {/* 프로젝트 설명 */}
            <div style={{ marginBottom: '24px' }}>
              <h3 style={{
                fontSize: '16px',
                fontWeight: '600',
                marginBottom: '12px',
                color: '#495057'
              }}>
                프로젝트 설명
              </h3>
              <p style={{
                fontSize: '14px',
                lineHeight: '1.6',
                color: '#6c757d',
                margin: 0
              }}>
                {selectedProject.description}
              </p>
            </div>

            {/* 메타데이터 정보 */}
            <div style={{ marginBottom: '24px' }}>
              <h3 style={{
                fontSize: '16px',
                fontWeight: '600',
                marginBottom: '12px',
                color: '#495057'
              }}>
                프로젝트 정보
              </h3>
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(2, 1fr)',
                gap: '12px'
              }}>
                <div style={{
                  padding: '12px',
                  backgroundColor: '#f8f9fa',
                  borderRadius: '8px'
                }}>
                  <div style={{
                    fontSize: '12px',
                    color: '#6c757d',
                    marginBottom: '4px'
                  }}>
                    마지막 업데이트
                  </div>
                  <div style={{
                    fontSize: '14px',
                    fontWeight: '500',
                    color: '#495057'
                  }}>
                    {new Date(selectedProject.last_updated).toLocaleDateString('ko-KR')}
                  </div>
                </div>
                
                <div style={{
                  padding: '12px',
                  backgroundColor: '#f8f9fa',
                  borderRadius: '8px'
                }}>
                  <div style={{
                    fontSize: '12px',
                    color: '#6c757d',
                    marginBottom: '4px'
                  }}>
                    문서 해시
                  </div>
                  <div style={{
                    fontSize: '14px',
                    fontWeight: '500',
                    color: '#495057',
                    fontFamily: 'monospace'
                  }}>
                    {selectedProject.content_hash?.substring(0, 8)}...
                  </div>
                </div>
              </div>
            </div>

            {/* 액션 버튼들 */}
            <div style={{
              display: 'flex',
              gap: '12px',
              justifyContent: 'flex-end'
            }}>
              {selectedProject.source === 'github' && (
                <button
                  onClick={() => openGitHubLink(selectedProject)}
                  style={{
                    padding: '12px 24px',
                    backgroundColor: '#0d1117',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    fontSize: '14px',
                    fontWeight: '500',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    transition: 'background-color 0.2s ease'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#24292f'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#0d1117'}
                >
                  <span>🔗</span>
                  GitHub에서 보기
                </button>
              )}
              
              <button
                onClick={closeProjectModal}
                style={{
                  padding: '12px 24px',
                  backgroundColor: '#6c757d',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '14px',
                  fontWeight: '500',
                  cursor: 'pointer',
                  transition: 'background-color 0.2s ease'
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#5a6268'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#6c757d'}
              >
                닫기
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DatabaseExplorer;

export {};
