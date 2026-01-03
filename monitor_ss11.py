# monitor_ss11.py
import requests
import os
import sys
import urllib3
import json
from datetime import datetime
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# === 配置 ===
CN_LIST_URL = "https://website.xdcdn.net/form/website/torchlight/news_cn.json"
EN_LIST_URL = "https://website.xdcdn.net/form/website/torchlight/news.json"

LAST_KNOWN_CN_ID = "buYaN1rB"
LAST_KNOWN_EN_ID = "i9ncluYb82HD"

SENDKEY = os.getenv("SENDKEY")
GIST_TOKEN = os.getenv("GIST_TOKEN")

if not SENDKEY:
    print("❌ 未设置 SENDKEY")
    sys.exit(1)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
PROXIES = {"http": None, "https": None}

def safe_get(url, use_headers=True):
    return requests.get(
        url,
        headers=HEADERS if use_headers else {},
        timeout=15,
        verify=False,
        proxies=PROXIES
    )

def extract_news_content(detail_url):
    """从公告详情页提取纯文本内容"""
    try:
        resp = safe_get(detail_url)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 定位正文容器
        detail_div = soup.find('div', id='news-detail')
        if not detail_div:
            return "⚠️ 未能提取公告正文（结构可能已变更）"
        
        # 移除不需要的元素（如分享按钮）
        for elem in detail_div.select('.social-share, .share-btn, script, style'):
            elem.decompose()
        
        # 获取纯文本，保留段落结构
        text = detail_div.get_text(separator='\n', strip=True)
        # 清理多余空行
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return '\n\n'.join(lines)
    except Exception as e:
        return f"⚠️ 提取正文失败: {str(e)}"

def send_wechat(title, link, source):
    message = f"来源：{source}\n标题：{title}\n\n链接：{link}"
    resp = requests.post(
        f"https://sctapi.ftqq.com/{SENDKEY}.send",
        data={"title": "🔥 火炬之光新公告！", "desp": message},
        proxies=PROXIES
    )
    return resp.status_code == 200

def save_to_gist(title, link, content, source):
    if not GIST_TOKEN:
        print("⚠️ 未设置 GIST_TOKEN，跳过保存快照")
        return False

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = f"{source}_{now.replace(':', '-')}.md"
    
    gist_content = f"""# {title}

- **来源**: {source}
- **检测时间**: {now}
- **原始链接**: {link}

---

{content}
"""

    gist_data = {
        "description": f"火炬之光公告全文快照 - {source} - {title}",
        "public": False,
        "files": {filename: {"content": gist_content}}
    }

    try:
        resp = requests.post(
            "https://api.github.com/gists",
            headers={"Authorization": f"token {GIST_TOKEN}"},
            data=json.dumps(gist_data),
            proxies=PROXIES
        )
        if resp.status_code == 201:
            print(f"✅ 全文快照已保存至 Gist: {resp.json()['html_url']}")
            return True
        else:
            print(f"❌ Gist 创建失败: {resp.status_code}")
            return False
    except Exception as e:
        print(f"💥 保存 Gist 出错: {e}")
        return False

# ===== 主逻辑 =====
try:
    print("🌍 正在检查《火炬之光》国服与国际服公告...")

    # === 国服检查 ===
    try:
        cn_resp = safe_get(CN_LIST_URL, use_headers=False)
        cn_resp.raise_for_status()
        cn_data = cn_resp.json()
        cn_latest = cn_data["zh-cn"]["announcement"][0]
        cn_id = cn_latest["link"].split("id=")[-1]
        cn_title = cn_latest["title"]
        cn_link = cn_latest["link"]
        print(f"🇨🇳 国服 | ID: {cn_id} | 标题: {cn_title}")

        if cn_id != LAST_KNOWN_CN_ID:
            print("🎉 国服有新公告！")
            full_content = extract_news_content(cn_link)
            if send_wechat(cn_title, cn_link, "【国服】"):
                print("✅ 微信通知发送成功！")
            save_to_gist(cn_title, cn_link, full_content, "国服")
            sys.exit(0)
    except Exception as e:
        print(f"❌ 国服检查失败: {e}")

    # === 国际服检查 ===
    try:
        en_resp = safe_get(EN_LIST_URL, use_headers=False)
        en_resp.raise_for_status()
        en_data = en_resp.json()
        en_latest = en_data["en"]["announcement"][0]
        en_id = en_latest["link"].split("id=")[-1]
        en_title = en_latest["title"]
        en_link = en_latest["link"]
        print(f"🇺🇸 国际服 | ID: {en_id} | 标题: {en_title}")

        if en_id != LAST_KNOWN_EN_ID:
            print("🎉 国际服有新公告！")
            full_content = extract_news_content(en_link)
            if send_wechat(en_title, en_link, "【国际服】"):
                print("✅ 微信通知发送成功！")
            save_to_gist(en_title, en_link, full_content, "国际服")
            sys.exit(0)
    except Exception as e:
        print(f"❌ 国际服检查失败: {e}")

    print("ℹ️ 国服与国际服均无新公告。")

except Exception as e:
    print(f"💥 脚本严重错误: {e}")
    sys.exit(1)
