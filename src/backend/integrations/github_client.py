"""
GitHub API 클라이언트
GitHub 리포지토리 문서 수집 및 README 생성
"""

import os
import requests
import json
from typing import List, Dict, Any
from langchain_core.documents import Document


class GitHubClient:
    def __init__(self, token: str = None):
        self.token = token or os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {self.token}"
        } if self.token else {"Accept": "application/vnd.github.v3+json"}
        self.org_name = "YBIGTA"
        
    def get_all_repos(self) -> List[Dict[str, Any]]:
        """조직의 모든 공개 리포지토리를 가져옵니다."""
        repos = []
        page = 1
        
        while True:
            url = f"https://api.github.com/orgs/{self.org_name}/repos"
            params = {"type": "public", "page": page, "per_page": 100}
            
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code != 200:
                print(f"❌ GitHub API 오류: {response.status_code}")
                break
                
            data = response.json()
            if not data:
                break
                
            repos.extend(data)
            page += 1
            
        return repos
    
    def get_readme_content(self, repo_full_name: str) -> str:
        """리포지토리의 README 내용을 가져옵니다."""
        url = f"https://api.github.com/repos/{repo_full_name}/readme"
        
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            data = response.json()
            # Base64 디코딩
            import base64
            content = base64.b64decode(data['content']).decode('utf-8')
            return content
        return None
    
    def get_repo_structure(self, repo_full_name: str) -> Dict[str, Any]:
        """리포지토리의 파일 구조를 가져옵니다."""
        url = f"https://api.github.com/repos/{repo_full_name}/contents"
        
        def get_tree(path=""):
            response = requests.get(f"{url}/{path}", headers=self.headers)
            if response.status_code != 200:
                return []
                
            items = response.json()
            structure = []
            
            for item in items:
                if item['type'] == 'file':
                    structure.append({
                        'path': item['path'],
                        'name': item['name'],
                        'size': item.get('size', 0)
                    })
                elif item['type'] == 'dir' and not item['name'].startswith('.'):
                    # 숨김 폴더 제외
                    structure.append({
                        'path': item['path'],
                        'name': item['name'],
                        'type': 'dir'
                    })
            
            return structure
        
        return get_tree()
    
    def generate_readme_content(self, repo_info: Dict[str, Any]) -> str:
        """리포지토리 정보를 바탕으로 README 내용을 생성합니다."""
        content = f"# {repo_info['name']}\\n\\n"
        
        if repo_info.get('description'):
            content += f"{repo_info['description']}\\n\\n"
        
        content += "## 정보\\n\\n"
        content += f"- **조직**: {repo_info['owner']['login']}\\n"
        content += f"- **생성일**: {repo_info['created_at']}\\n"
        content += f"- **언어**: {repo_info.get('language', 'N/A')}\\n"
        content += f"- **라이센스**: {repo_info['license']['name'] if repo_info.get('license') else 'N/A'}\\n"
        
        if repo_info.get('topics'):
            content += f"- **토픽**: {', '.join(repo_info['topics'])}\\n"
        
        content += f"\\n## 링크\\n\\n"
        content += f"- [GitHub]({repo_info['html_url']})\\n"
        
        if repo_info.get('homepage'):
            content += f"- [홈페이지]({repo_info['homepage']})\\n"
        
        return content
    
    def load_all_repos(self) -> List[Document]:
        """모든 리포지토리의 문서를 로드합니다."""
        repos = self.get_all_repos()
        documents = []
        
        print(f"🔍 총 {len(repos)}개의 리포지토리를 발견했습니다.")
        
        for i, repo in enumerate(repos, 1):
            print(f"\\n📦 리포지토리 {i}/{len(repos)}: {repo['name']}")
            
            # README 가져오기
            readme_content = self.get_readme_content(repo['full_name'])
            
            if not readme_content:
                print(f"  ⚠️ README가 없습니다. 자동 생성합니다.")
                readme_content = self.generate_readme_content(repo)
            
            # Document 생성
            doc = Document(
                page_content=readme_content,
                metadata={
                    "source": "github",
                    "page_id": f"github_{repo['name']}",
                    "title": repo['name'],
                    "repo_name": repo['name'],
                    "repo_url": repo['html_url'],
                    "language": repo.get('language', 'Unknown'),
                    "stars": repo.get('stargazers_count', 0),
                    "last_modified": repo.get('updated_at', ''),
                    "created_time": repo.get('created_at', '')
                }
            )
            
            documents.append(doc)
            print(f"  ✅ 문서 로드 완료")
        
        return documents