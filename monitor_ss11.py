import requests
import os
import sys

# 配置
JSON_URL = "https://website.xdcdn.net/form/website/torchlight/news_cn.json"
LAST_KNOWN_ID = "buYaN1rB"  # SS10 公告 ID

try:
    print("🔍 正在检查《火炬之光》最新公告...")
    resp = requests.get(JSON_URL, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    latest = data["zh-cn"]["announcement"][0]
    current_id = latest["link"].split("id=")[-1]
    title = latest["title"]
    link = latest["link"]

    print(f"ID: {current_id} | 标题: {title}")

    if current_id != LAST_KNOWN_ID and ("SS11" in title or "渴瘾症" in title):
        print("🎉 检测到 SS11 赛季公告！")
        message = f"标题：{title}\n\n链接：{link}"
        sendkey = os.getenv("SENDKEY")
        if not sendkey:
            print("❌ 错误：未设置 SENDKEY 环境变量")
            sys.exit(1)
        push_url = f"https://sctapi.ftqq.com/{sendkey}.send"
        result = requests.post(push_url, data={
            "title": "🔥 火炬之光 SS11 公告已发布！",
            "desp": message
        })
        if result.status_code == 200:
            print("✅ 微信通知发送成功！")
        else:
            print(f"⚠️ 推送失败，状态码: {result.status_code}")
    else:
        print("ℹ️ 未发现新公告。")

except Exception as e:
    print(f"❌ 脚本执行出错: {e}")
    sys.exit(1)
