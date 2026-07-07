import os
import re
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated
from src.config import OLLAMA_BASE_URL, OLLAMA_MODEL, CODING_PROMPT_TEMPLATE, CODE_SUMMARY_PROMPT_TEMPLATE
from src import database, github_manager, dingtalk_bot


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    project_id: int
    requirement: str
    generated_code: str
    github_url: str
    error: str
    change_info: dict


def parse_code_files(code: str) -> dict:
    files = {}

    pattern = r'(?:#|//)\s*filename:\s*([^\n]+)\s*\n(.*?)(?=(?:#|//)\s*filename:|\Z)'
    matches = re.findall(pattern, code, re.DOTALL)
    if matches:
        for filename, content in matches:
            filename = filename.strip()
            content = content.strip()
            if filename and content:
                filename = re.sub(r'[\\/:*?"<>|\n\r]', '', filename).strip()
                filename = filename[:200] if len(filename) > 200 else filename
                files[filename] = content
        return files

    md_title_pattern = r'###\s*([^\n]+)\s*\n```(\w*)\s*\n(.*?)\n```'
    md_title_matches = re.findall(md_title_pattern, code, re.DOTALL)
    if md_title_matches:
        for title, lang, content in md_title_matches:
            content = content.strip()
            if content:
                match = re.search(r'(\w+\.\w+)', title)
                if match:
                    filename = match.group(1)
                elif lang:
                    filename = f"{title}.{lang}".replace(' ', '_')
                else:
                    filename = f"{title}.py".replace(' ', '_')
                filename = re.sub(r'[\\/:*?"<>|\n\r]', '', filename).strip()
                filename = filename[:200] if len(filename) > 200 else filename
                files[filename] = content
        return files

    md_pattern = r'```(\w*)\s*\n(.*?)\n```'
    md_matches = re.findall(md_pattern, code, re.DOTALL)
    if md_matches:
        index = 1
        for lang, content in md_matches:
            content = content.strip()
            if content:
                filename = f"file{index}.{lang}" if lang else f"file{index}.py"
                filename = re.sub(r'[\\/:*?"<>|\n\r]', '', filename).strip()
                filename = filename[:200] if len(filename) > 200 else filename
                files[filename] = content
                index += 1
        return files

    if code.strip():
        files["main.py"] = code.strip()

    return files


def save_code_to_file(state: AgentState) -> dict:
    project = database.get_project(state["project_id"])
    if not project:
        return {"error": "项目不存在"}

    code = state["generated_code"]
    folder = project["folder_path"]
    files = parse_code_files(code)

    seen_contents = set()
    unique_files = {}
    for filename, content in files.items():
        content_normalized = content.strip().replace('\n', '').replace('\r', '').replace(' ', '')
        if content_normalized and content_normalized not in seen_contents:
            seen_contents.add(content_normalized)
            unique_files[filename] = content

    saved_files = []
    changed_files = []
    is_first_time = not os.path.exists(folder) or len(os.listdir(folder)) == 0

    for filename, content in unique_files.items():
        filepath = os.path.join(folder, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        old_content = ""
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                old_content = f.read()

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        saved_files.append(filename)

        if old_content and old_content != content:
            changed_files.append(filename)

    change_info = {
        "is_first_time": is_first_time,
        "changed_files": changed_files,
        "total_files": saved_files
    }

    return {
        "messages": [AIMessage(content=f"代码已保存到: {', '.join(saved_files)}")],
        "change_info": change_info,
        "generated_code": code
    }


def push_to_github(state: AgentState) -> dict:
    project = database.get_project(state["project_id"])
    if not project:
        return {"error": "项目不存在"}

    try:
        github_url = github_manager.push_code_to_github(
            project["name"],
            project["folder_path"],
            project["description"]
        )
        database.update_project_github(state["project_id"], github_url)

        folder = project["folder_path"]
        is_first_time = not os.path.exists(folder) or len(os.listdir(folder)) == 0

        if state.get("generated_code"):
            code_for_summary = state["generated_code"]
        else:
            code_for_summary = ""
            for root, dirs, files in os.walk(folder):
                for filename in files:
                    if filename.endswith(('.py', '.html', '.css', '.js', '.md')):
                        filepath = os.path.join(root, filename)
                        try:
                            with open(filepath, "r", encoding="utf-8") as f:
                                content = f.read()
                                code_for_summary += f"### {filename}\n{content}\n\n"
                        except:
                            pass

        try:
            llm = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL, temperature=0.3)
            prompt = CODE_SUMMARY_PROMPT_TEMPLATE.format(code=code_for_summary[:2000])
            response = llm.invoke(prompt)
            code_summary = response.content.strip()
        except:
            code_summary = "代码已生成并保存"

        changed_files = []
        if not is_first_time and state.get("generated_code"):
            files = parse_code_files(state["generated_code"])
            for filename, content in files.items():
                filepath = os.path.join(folder, filename)
                if os.path.exists(filepath):
                    with open(filepath, "r", encoding="utf-8") as f:
                        old_content = f.read()
                    if old_content != content:
                        changed_files.append(filename)

        change_info = {"is_first_time": is_first_time, "changed_files": changed_files}

        dingtalk_bot.send_code_summary(project["name"], code_summary, github_url, change_info)

        return {
            "github_url": github_url,
            "messages": [AIMessage(content=f"代码已推送到 GitHub: {github_url}")]
        }
    except Exception as e:
        return {"error": f"GitHub 推送失败: {str(e)}"}


def coding_node(state: AgentState) -> dict:
    llm = ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0.2,
        timeout=120,
        max_tokens=4096
    )

    history = database.get_chat_history(state["project_id"])
    messages = []
    for msg in history[-10:]:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))

    requirement = state["requirement"]
    multi_keywords = ["多文件", "分文件", "多个文件", "分模块", "前后端分离", "分成", "分开写", "分两个"]
    if any(kw in requirement for kw in multi_keywords):
        requirement = requirement + "\n\n重要：这个项目必须分成多个文件编写，每个文件以 # filename: 文件名 开头。"

    prompt = CODING_PROMPT_TEMPLATE.format(requirement=requirement)
    messages.append(HumanMessage(content=prompt))

    response = llm.invoke(messages)
    code = response.content.strip()

    return {
        "generated_code": code,
        "messages": [AIMessage(content=code)]
    }


def is_push_request(state: AgentState) -> str:
    requirement = state["requirement"].lower()
    return "push_only" if any(kw in requirement for kw in ["推送", "上传", "github", "push"]) else "coding"


def push_node(state: AgentState) -> dict:
    return push_to_github(state)


def save_node(state: AgentState) -> dict:
    return save_code_to_file(state)


def build_agent_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("coding", coding_node)
    workflow.add_node("save", save_node)
    workflow.add_node("push", push_node)

    workflow.add_conditional_edges(
        START,
        is_push_request,
        {"coding": "coding", "push_only": "push"}
    )
    workflow.add_edge("coding", "save")
    workflow.add_edge("save", END)
    workflow.add_edge("push", END)

    return workflow.compile()


def run_agent(user_input: str, project_id: int) -> dict:
    graph = build_agent_graph()

    state = AgentState(
        messages=[],
        project_id=project_id,
        requirement=user_input,
        generated_code="",
        github_url="",
        error=""
    )

    result = graph.invoke(state)

    database.save_chat_message(project_id, "user", user_input)
    if result.get("generated_code"):
        database.save_chat_message(project_id, "assistant", result["generated_code"])

    return {
        "generated_code": result.get("generated_code", ""),
        "github_url": result.get("github_url", ""),
        "error": result.get("error", "")
    }