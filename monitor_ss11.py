# monitor_ss11.py
import requests
import os
import sys
import urllib3

# 可选：关闭 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

JSON_URL = "https://website.xdcdn.net/form/website/torchlight/news_cn.json"
LAST_KNOWN_ID = "buYaN1rB"

try:
    print("🔍 正在检查《火炬之光》最新公告...")
    
    # 关键修复：1. 禁用 SSL 验证；2. 强制不走代理
    resp = requests.get(
        JSON_URL,
        timeout=10,
        verify=False,
        proxies={"http": None, "https": None}  # 👈 绕过科学上网代理
    )
    resp.raise_for_status()
    data = resp.json()

    latest = data["zh-cn"]["announcement"][0]
    current_id = latest["link"].split("id=")[-1]
    title = latest["title"]
    link = latest["link"]

    print(f"ID: {current_id} | 标题: {title}")

    if current_id != LAST_KNOWN_ID:
        print("🎉 检测到 SS11 赛季公告！")
        message = f"标题：{title}\n\n链接：{link}"
        sendkey = os.getenv("SENDKEY")
        if not sendkey:
            print("❌ 未设置 SENDKEY")
            sys.exit(1)
        push_resp = requests.post(
            f"https://sctapi.ftqq.com/{sendkey}.send",
            data={"title": "🔥 火炬之光 SS11 公告已发布！", "desp": message},
            proxies={"http": None, "https": None}  # 推送也禁用代理（可选）
        )
        print("✅ 微信通知发送成功！" if push_resp.status_code == 200 else f"⚠️ 推送失败: {push_resp.status_code}")
    else:
        print("ℹ️ 未发现新公告。")

except Exception as e:
    print(f"❌ 脚本执行出错: {e}")
    sys.exit(1)
