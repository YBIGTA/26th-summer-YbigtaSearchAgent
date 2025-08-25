"""
SQLite 데이터베이스 모델
회의록, 설정, 메타데이터 저장
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, JSON, ForeignKey, Boolean, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import os

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    api_keys = relationship("APIKey", back_populates="user")
    audio_files = relationship("AudioFile", back_populates="user")
    settings = relationship("UserSetting", back_populates="user")


class APIKey(Base):
    __tablename__ = 'api_keys'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    provider = Column(String(50), nullable=False)  # upstage, openai, notion, github, gdrive
    key_alias = Column(String(100))
    key_encrypted = Column(Text, nullable=False)  # 암호화된 API 키
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")


class AudioFile(Base):
    __tablename__ = 'audio_files'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    duration_seconds = Column(Float)
    file_size = Column(Integer)
    language = Column(String(10), default='ko')
    stt_engine = Column(String(50))  # whisper, returnzero
    status = Column(String(50), default='pending')  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="audio_files")
    transcript = relationship("Transcript", back_populates="audio_file", uselist=False)


class Transcript(Base):
    __tablename__ = 'transcripts'
    
    id = Column(Integer, primary_key=True)
    audio_file_id = Column(Integer, ForeignKey('audio_files.id'))
    title = Column(String(255))
    raw_text = Column(Text)
    language = Column(String(10))
    num_speakers = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    audio_file = relationship("AudioFile", back_populates="transcript")
    speakers = relationship("Speaker", back_populates="transcript")
    utterances = relationship("Utterance", back_populates="transcript")
    agendas = relationship("Agenda", back_populates="transcript")


class Speaker(Base):
    __tablename__ = 'speakers'
    
    id = Column(Integer, primary_key=True)
    transcript_id = Column(Integer, ForeignKey('transcripts.id'))
    speaker_label = Column(String(50))  # Speaker 1, Speaker 2, etc.
    speaker_name = Column(String(100))  # 사용자가 지정한 이름
    confidence = Column(Float)
    total_speaking_time = Column(Float)
    
    # Relationships
    transcript = relationship("Transcript", back_populates="speakers")
    utterances = relationship("Utterance", back_populates="speaker")


class Utterance(Base):
    __tablename__ = 'utterances'
    
    id = Column(Integer, primary_key=True)
    transcript_id = Column(Integer, ForeignKey('transcripts.id'))
    speaker_id = Column(Integer, ForeignKey('speakers.id'))
    start_time = Column(Float, nullable=False)  # 초 단위
    end_time = Column(Float, nullable=False)
    text = Column(Text, nullable=False)
    confidence = Column(Float)
    
    # Relationships
    transcript = relationship("Transcript", back_populates="utterances")
    speaker = relationship("Speaker", back_populates="utterances")


class Agenda(Base):
    __tablename__ = 'agendas'
    
    id = Column(Integer, primary_key=True)
    transcript_id = Column(Integer, ForeignKey('transcripts.id'))
    title = Column(String(255), nullable=False)
    summary = Column(Text)
    start_time = Column(Float)
    end_time = Column(Float)
    status = Column(String(50), default='pending')  # pending, analyzing, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    transcript = relationship("Transcript", back_populates="agendas")
    agent_runs = relationship("AgentRun", back_populates="agenda")


class AgentRun(Base):
    __tablename__ = 'agent_runs'
    
    id = Column(Integer, primary_key=True)
    agenda_id = Column(Integer, ForeignKey('agendas.id'))
    agent_role = Column(String(50))  # agenda_miner, claim_checker, counter_arguer, etc.
    prompt = Column(Text)
    output = Column(Text)
    citations = Column(JSON)  # 인용/증거 정보
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    tokens_used = Column(Integer)
    cost = Column(Float)
    
    # Relationships
    agenda = relationship("Agenda", back_populates="agent_runs")


class Document(Base):
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True)
    source = Column(String(50))  # notion, github, gdrive, meeting
    external_id = Column(String(255))  # 외부 시스템의 ID
    title = Column(String(255))
    url = Column(Text)
    content = Column(Text)
    doc_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    chunks = relationship("Chunk", back_populates="document")


class Chunk(Base):
    __tablename__ = 'chunks'
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('documents.id'))
    chunk_index = Column(Integer)
    text = Column(Text, nullable=False)
    embedding_id = Column(String(255))  # ChromaDB 인덱스 내 ID
    chunk_metadata = Column(JSON)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")


class MeetingReport(Base):
    __tablename__ = 'meeting_reports'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(String(100), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    transcript_id = Column(Integer, ForeignKey('transcripts.id'), nullable=True)
    original_filename = Column(String(255))
    file_size = Column(Integer)
    duration_seconds = Column(Float)
    num_speakers = Column(Integer, default=0)
    
    # 분석 결과 저장
    raw_results = Column(JSON)  # 전체 분석 결과 JSON
    executive_summary = Column(JSON)  # 요약 정보
    agendas = Column(JSON)  # 아젠다 분석 결과
    claims = Column(JSON)  # 주장 분석 결과
    counter_arguments = Column(JSON)  # 반박 분석 결과
    evidence = Column(JSON)  # 증거 분석 결과
    final_report = Column(JSON)  # 최종 보고서
    
    # 상태 정보
    status = Column(String(50), default='pending')  # pending, processing, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    current_stage = Column(String(100))
    error_message = Column(Text)
    
    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transcript = relationship("Transcript", foreign_keys=[transcript_id])


class UserSetting(Base):
    __tablename__ = 'user_settings'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    key = Column(String(100), nullable=False)
    value = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="settings")


class ChatSession(Base):
    __tablename__ = 'chat_sessions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # 익명 사용자 허용
    session_id = Column(String(100), unique=True, nullable=False)  # UUID
    title = Column(String(255))  # 첫 번째 질문으로 자동 생성
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('chat_sessions.id'))
    role = Column(String(20), nullable=False)  # 'user', 'assistant'
    content = Column(Text, nullable=False)
    processing_time = Column(Float)  # 응답 시간 (초)
    search_type = Column(String(20))  # 'hybrid', 'semantic', 'keyword'
    top_k = Column(Integer)  # 검색된 문서 수
    sources_count = Column(Integer)  # 참조된 소스 수
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    sources = relationship("ChatMessageSource", back_populates="message", cascade="all, delete-orphan")


class ChatMessageSource(Base):
    __tablename__ = 'chat_message_sources'
    
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey('chat_messages.id'))
    source_type = Column(String(50))  # 'notion', 'gdrive', 'github', 'file'
    source_id = Column(String(255))  # 원본 문서 ID
    title = Column(String(255))  # 문서 제목
    content_preview = Column(Text)  # 내용 미리보기
    relevance_score = Column(Float)  # 관련성 점수
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    message = relationship("ChatMessage", back_populates="sources")


class ChatbotSetting(Base):
    __tablename__ = 'chatbot_settings'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    default_search_type = Column(String(20), default='hybrid')  # 'hybrid', 'semantic', 'keyword'
    default_top_k = Column(Integer, default=5)
    enable_suggestions = Column(Boolean, default=True)
    enable_source_citation = Column(Boolean, default=True)
    language = Column(String(10), default='ko')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# --- FTS 테이블을 활성화하는 SQLAlchemy 이벤트 리스너 ---
def setup_fts_events(dbapi_connection, connection_record):
    """FTS5 가상 테이블과 자동 동기화 트리거를 설정합니다."""
    # SQLAlchemy event listener provides the raw DBAPI connection object
    
    # Use a cursor to execute SQL statements
    cursor = dbapi_connection.cursor()

    # FTS 테이블 생성 (기존 테이블이 없으면)
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS document_fts
        USING fts5(
            title,
            content,
            content='documents',
            content_rowid='id',
            tokenize = 'porter unicode61'
        );
    """)

    # --- 데이터 동기화를 위한 트리거 설정 ---
    triggers = [
        """
        CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents BEGIN
            INSERT INTO document_fts(rowid, title, content)
            VALUES (new.id, new.title, new.content);
        END;
        """,
        """
        CREATE TRIGGER IF NOT EXISTS documents_ad AFTER DELETE ON documents BEGIN
            INSERT INTO document_fts(document_fts, rowid, title, content)
            VALUES ('delete', old.id, old.title, old.content);
        END;
        """,
        """
        CREATE TRIGGER IF NOT EXISTS documents_au AFTER UPDATE ON documents BEGIN
            INSERT INTO document_fts(document_fts, rowid, title, content)
            VALUES ('delete', old.id, old.title, old.content);
            INSERT INTO document_fts(rowid, title, content)
            VALUES (new.id, new.title, new.content);
        END;
        """
    ]
    for trigger in triggers:
        cursor.execute(trigger)

    cursor.close()


# 데이터베이스 초기화
def init_db(db_path: str = "data/db/app.db"):
    """데이터베이스를 초기화합니다."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    engine = create_engine(f'sqlite:///{db_path}')
    
    # ✅ FTS 이벤트 리스너 등록 (이제 다시 활성화합니다)
    event.listen(engine, 'connect', setup_fts_events)
    
    Base.metadata.create_all(engine)
    return engine


def get_session(engine):
    """데이터베이스 세션을 생성합니다."""
    Session = sessionmaker(bind=engine)
    return Session()


# --- SQLAlchemy 엔진이 처음 연결될 때 위 함수를 실행하도록 설정 ---
# 사용 예시:
# from sqlalchemy import create_engine
# from sqlalchemy import event
# engine = create_engine("sqlite:///./data/db/app.db")
# event.listen(engine, 'connect', setup_fts_events)