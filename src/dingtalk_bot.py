import ssl
import requests
from src.config import DINGTALK_WEBHOOK, DINGTALK_KEYWORD

ssl._create_default_https_context = ssl._create_unverified_context
requests.packages.urllib3.disable_warnings()


def send_dingtalk_message(text):
    if DINGTALK_KEYWORD not in text:
        text = f"{DINGTALK_KEYWORD} {text}"

    payload = {
        "msgtype": "text",
        "text": {"content": text}
    }

    try:
        response = requests.post(DINGTALK_WEBHOOK, json=payload, timeout=10)
        result = response.json()
        if result.get("errcode") == 0:
            return True
        else:
            print(f"钉钉发送失败: {result}")
            return False
    except Exception as e:
        print(f"钉钉请求异常: {e}")
        return False


def send_code_summary(project_name, code_summary, github_url="", change_info=None):
    msg = f"【{project_name}】代码生成完成\n\n"
    msg += f"📋 项目介绍：{code_summary}\n\n"

    if change_info:
        if change_info.get("is_first_time"):
            msg += f"✨ 首次创建\n\n"
        else:
            changed_files = change_info.get("changed_files", [])
            if changed_files:
                msg += f"🔄 修改文件：{', '.join(changed_files)}\n\n"

    if github_url:
        msg += f"🔗 GitHub：{github_url}\n"
    msg += f"💻 修改方式：通过超级智能体重新生成或手动修改\n"
    msg += f"📌 关键词：{DINGTALK_KEYWORD}"

    return send_dingtalk_message(msg)