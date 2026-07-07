import os
import ssl
import base64
import requests
from src.config import GITHUB_USERNAME, GITHUB_TOKEN

ssl._create_default_https_context = ssl._create_unverified_context
requests.packages.urllib3.disable_warnings()

BASE_URL = "https://api.github.com"


def create_repository(project_name, description=""):
    url = f"{BASE_URL}/user/repos"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "name": project_name,
        "description": description,
        "private": False,
        "auto_init": True
    }
    response = requests.post(url, json=data, headers=headers, verify=False)
    response.raise_for_status()
    return response.json()


def get_repository(project_name):
    url = f"{BASE_URL}/repos/{GITHUB_USERNAME}/{project_name}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers, verify=False)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def create_file(repo_name, path, content, message="Add file"):
    url = f"{BASE_URL}/repos/{GITHUB_USERNAME}/{repo_name}/contents/{path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8")
    }
    response = requests.put(url, json=data, headers=headers, verify=False)
    response.raise_for_status()
    return response.json()


def update_file(repo_name, path, content, sha, message="Update file"):
    url = f"{BASE_URL}/repos/{GITHUB_USERNAME}/{repo_name}/contents/{path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "sha": sha
    }
    response = requests.put(url, json=data, headers=headers, verify=False)
    response.raise_for_status()
    return response.json()


def get_file_sha(repo_name, path):
    url = f"{BASE_URL}/repos/{GITHUB_USERNAME}/{repo_name}/contents/{path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers, verify=False)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()["sha"]


def push_code_to_github(project_name, folder_path, description=""):
    repo_name = project_name.replace(" ", "-")
    repo = get_repository(repo_name)
    if not repo:
        repo = create_repository(repo_name, description)

    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            file_path = os.path.join(root, filename)
            relative_path = os.path.relpath(file_path, folder_path).replace("\\", "/")

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            sha = get_file_sha(repo_name, relative_path)
            if sha:
                update_file(repo_name, relative_path, content, sha, f"Update {relative_path}")
            else:
                create_file(repo_name, relative_path, content, f"Add {relative_path}")

    return f"https://github.com/{GITHUB_USERNAME}/{repo_name}"


def delete_repository(project_name):
    url = f"{BASE_URL}/repos/{GITHUB_USERNAME}/{project_name}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.delete(url, headers=headers, verify=False)
    if response.status_code == 404:
        return False, "仓库不存在"
    response.raise_for_status()
    return True, f"仓库 {project_name} 已删除"