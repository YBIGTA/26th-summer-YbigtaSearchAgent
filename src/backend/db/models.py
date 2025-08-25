"""
SQLite 데이터베이스 모델
회의록, 설정, 메타데이터 저장
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, JSON, ForeignKey, Boolean
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


# 데이터베이스 초기화
def init_db(db_path: str = "data/db/app.db"):
    """데이터베이스를 초기화합니다."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    return engine


def get_session(engine):
    """데이터베이스 세션을 생성합니다."""
    Session = sessionmaker(bind=engine)
    return Session()