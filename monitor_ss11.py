# monitor_ss11.py
import requests
import os
import sys
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# === 配置区 ===
CN_URL = "https://website.xdcdn.net/form/website/torchlight/news_cn.json"
EN_URL = "https://website.xdcdn.net/form/website/torchlight/news.json"

# 最后已知的公告 ID（请定期手动更新！）
LAST_KNOWN_CN_ID = "buYaN1rB"   # 国服 SS10
LAST_KNOWN_EN_ID = "i9ncluYb82HD"  # 国际服 SS10（根据你提供的链接推测）

SENDKEY = os.getenv("SENDKEY")
if not SENDKEY:
    print("❌ 未设置 SENDKEY 环境变量")
    sys.exit(1)

def safe_get(url):
    return requests.get(
        url,
        timeout=10,
        verify=False,
        proxies={"http": None, "https": None}
    )

def send_notification(title, link, source):
    message = f"来源：{source}\n标题：{title}\n\n链接：{link}"
    resp = requests.post(
        f"https://sctapi.ftqq.com/{SENDKEY}.send",
        data={"title": "🔥 火炬之光新公告！", "desp": message},
        proxies={"http": None, "https": None}
    )
    return resp.status_code == 200

try:
    print("🌍 正在检查《火炬之光》国服与国际服公告...")

    # === 检查国服 ===
    try:
        cn_resp = safe_get(CN_URL)
        cn_resp.raise_for_status()
        cn_data = cn_resp.json()
        cn_latest = cn_data["zh-cn"]["announcement"][0]
        cn_id = cn_latest["link"].split("id=")[-1]
        cn_title = cn_latest["title"]
        cn_link = cn_latest["link"]
        print(f"🇨🇳 国服 | ID: {cn_id} | 标题: {cn_title}")

        if cn_id != LAST_KNOWN_CN_ID:
            print("🎉 国服有新公告！")
            if send_notification(cn_title, cn_link, "【国服】"):
                print("✅ 国服公告推送成功！")
            else:
                print("⚠️ 国服推送失败")
            sys.exit(0)  # 任一更新即退出（避免重复推送）
    except Exception as e:
        print(f"❌ 国服检查失败: {e}")

    # === 检查国际服 ===
    try:
        en_resp = safe_get(EN_URL)
        en_resp.raise_for_status()
        en_data = en_resp.json()
        en_latest = en_data["en"]["announcement"][0]
        en_id = en_latest["link"].split("id=")[-1]
        en_title = en_latest["title"]
        en_link = en_latest["link"]
        print(f"🇺🇸 国际服 | ID: {en_id} | 标题: {en_title}")

        if en_id != LAST_KNOWN_EN_ID:
            print("🎉 国际服有新公告！")
            if send_notification(en_title, en_link, "【国际服】"):
                print("✅ 国际服公告推送成功！")
            else:
                print("⚠️ 国际服推送失败")
            sys.exit(0)
    except Exception as e:
        print(f"❌ 国际服检查失败: {e}")

    print("ℹ️ 国服与国际服均无新公告。")

except Exception as e:
    print(f"💥 脚本严重错误: {e}")
    sys.exit(1)
