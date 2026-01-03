import os
import requests
import urllib3
from datetime import datetime
from urllib.parse import urlparse, parse_qs

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# === 配置区（手动更新这里！）===
# 替换为当前最新公告的 ID（从链接中提取）
LAST_KNOWN_CN_ID = "1"   # 👈 国服最新公告 ID
LAST_KNOWN_EN_ID = "i9ncluYb82HD"   # 👈 国际服最新公告 ID（若无，可设为空字符串）

CN_NEWSLIST_URL = "https://website.xdcdn.net/form/website/torchlight/news_cn.json"
EN_NEWSLIST_URL = "https://website.xdcdn.net/form/website/torchlight/news.json"

SENDKEY = os.getenv("SENDKEY")
GIST_TOKEN = os.getenv("GIST_TOKEN")

def send_wechat(title, link, prefix=""):
    if not SENDKEY:
        print("❌ 未设置 SENDKEY，跳过微信推送")
        return False
    url = f"https://sctapi.ftqq.com/{SENDKEY}.send"
    data = {
        "title": f"{prefix}【火炬之光 SS11】{title}",
        "desp": f"[查看公告]({link})\n\n> 检测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    }
    try:
        resp = requests.post(url, data=data, timeout=10)
        success = resp.status_code == 200 and resp.json().get("code") == 0
        print(f"✅ 微信推送成功: {title}" if success else f"⚠️ 推送失败: {resp.text}")
        return success
    except Exception as e:
        print(f"⚠️ 微信推送异常: {e}")
        return False


def save_to_gist(title, link, content, region):
    if not GIST_TOKEN:
        print("⚠️ 未设置 GIST_TOKEN，跳过保存快照")
        return False
    headers = {"Authorization": f"token {GIST_TOKEN}"}
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = f"torchlight-{region}-{now.replace(':', '-')}.txt"
    data = {
        "description": f"【{region}】{title}",
        "public": False,
        "files": {
            filename: {
                "content": f"标题: {title}\n链接: {link}\n时间: {now}\n\n---\n\n{content}"
            }
        }
    }
    try:
        resp = requests.post("https://api.github.com/gists", headers=headers, json=data, timeout=15)
        if resp.status_code == 201:
            gist_id = resp.json()["id"]
            print(f"✅ 全文快照已保存至 Gist: https://gist.github.com/{gist_id}")
            return True
        else:
            print(f"⚠️ Gist 保存失败: {resp.text}")
            return False
    except Exception as e:
        print(f"⚠️ Gist 保存异常: {e}")
        return False


def extract_news_id(detail_url: str) -> str:
    parsed = urlparse(detail_url)
    return parse_qs(parsed.query).get("id", [None])[0]


def fetch_news_json(news_id: str, region: str = "cn") -> str:
    if not news_id:
        return "⚠️ 无效公告 ID"
    folder = "news_cn" if region == "cn" else "news/en"
    json_url = f"http://website.xdcdn.net/form/website/torchlight/{folder}/{news_id}.json"
    try:
        print(f"📥 获取公告 JSON: {json_url}")
        resp = requests.get(
            json_url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
            verify=False,
            proxies={"http": None, "https": None}
        )
        resp.raise_for_status()
        data = resp.json()
        content_html = data.get("content", "")
        if not content_html:
            return "⚠️ JSON 中无 content 字段"

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content_html, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        clean_text = "\n\n".join(lines)
        return clean_text[:8000] + ("\n\n...（内容过长，已截断）" if len(clean_text) > 8000 else "")
    except Exception as e:
        return f"⚠️ 获取公告失败: {str(e)}"


def main():
    updated = False

    # === 国服检查 ===
    try:
        cn_resp = requests.get(CN_NEWSLIST_URL, timeout=10, verify=False)
        cn_data = cn_resp.json()
        announcements = cn_data.get("zh-cn", {}).get("announcement", [])
        if announcements:
            latest = announcements[0]
            cn_title = latest["title"]
            cn_link = latest["link"]
            cn_id = extract_news_id(cn_link)

            if cn_id and cn_id != LAST_KNOWN_CN_ID:
                print(f"🆕 发现国服新公告: {cn_title}")
                full_content = fetch_news_json(cn_id, "cn")
                # send_wechat(cn_title, cn_link, "【国服】")
                save_to_gist(cn_title, cn_link, full_content, "国服")
                updated = True
            else:
                print("🔍 国服无新公告")
        else:
            print("⚠️ 国服公告列表为空")
    except Exception as e:
        print(f"⚠️ 国服检查失败: {e}")

    # === 国际服检查 ===
    try:
        en_resp = requests.get(EN_NEWSLIST_URL, timeout=10, verify=False)
        en_data = en_resp.json()
        announcements = en_data.get("en", {}).get("announcement", [])
        if announcements:
            latest = announcements[0]
            en_title = latest["title"]
            en_link = latest["link"]
            en_id = extract_news_id(en_link)

            if en_id and en_id != LAST_KNOWN_EN_ID:
                print(f"🌍 发现国际服新公告: {en_title}")
                full_content = fetch_news_json(en_id, "en")
                # send_wechat(en_title, en_link, "【国际服】")
                save_to_gist(en_title, en_link, full_content, "国际服")
                updated = True
            else:
                print("🔍 国际服无新公告")
        else:
            print("⚠️ 国际服公告列表为空")
    except Exception as e:
        print(f"⚠️ 国际服检查失败: {e}")

    if not updated:
        print("✅ 无新公告")


if __name__ == "__main__":
    main()
