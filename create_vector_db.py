# create_vector_db.py

import os
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# 환경 변수 로드
load_dotenv()

# 데이터 로드 및 분할
loader = DirectoryLoader('./data', glob="**/*.md", show_progress=True)
documents = loader.load()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
texts = text_splitter.split_documents(documents)

# 임베딩 및 Vector DB 생성
embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(texts, embeddings)

# 생성된 Vector DB를 로컬에 저장
vectorstore.save_local("faiss_index")

print("Vector DB가 'faiss_index' 폴더에 성공적으로 저장되었습니다.")