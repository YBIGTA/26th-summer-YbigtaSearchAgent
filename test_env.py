import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

print("=== 환경 변수 테스트 ===")
print(f"OPENAI_API_KEY: {'설정됨' if os.getenv('OPENAI_API_KEY') else '설정되지 않음'}")
print(f"NOTION_API_KEY: {'설정됨' if os.getenv('NOTION_API_KEY') else '설정되지 않음'}")
print(f"NOTION_PAGE_ID_1: {'설정됨' if os.getenv('NOTION_PAGE_ID_1') else '설정되지 않음'}")
print(f"GDRIVE_FOLDER_ID: {'설정됨' if os.getenv('GDRIVE_FOLDER_ID') else '설정되지 않음'}")
print(f"GITHUB_PERSONAL_ACCESS_TOKEN: {'설정됨' if os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN') else '설정되지 않음'}")

print("\n=== .env 파일 내용 ===")
try:
    with open('.env', 'r', encoding='utf-8') as f:
        content = f.read()
        if content.strip():
            print(content)
        else:
            print(".env 파일이 비어있습니다.")
except FileNotFoundError:
    print(".env 파일을 찾을 수 없습니다.")
except Exception as e:
    print(f".env 파일 읽기 오류: {e}") 