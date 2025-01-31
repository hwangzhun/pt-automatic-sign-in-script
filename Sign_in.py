# -*- coding: utf-8 -*-
"""
cron: 0 10 0 * * *
new Env('PT_SITE_SIGNIN');
"""

import json
import requests
import re
import os
import time
from notify import send  # 青龙面板自带推送模块
requests.packages.urllib3.disable_warnings()

# 站点信息（环境变量读取）
try:
    pt_sites = json.loads(os.getenv("PT_SITES", "[]"))
    if isinstance(pt_sites, list) and all(isinstance(item, str) for item in pt_sites):
        pt_sites = [json.loads(item) for item in pt_sites]
except json.JSONDecodeError:
    print("❌ PT_SITES 变量格式错误，请检查 JSON 格式！")
    pt_sites = []

def sign_in(site_name, site_url, cookie, max_retries, retry_interval):
    """ 执行签到 """
    retries = 0
    success = False
    msg = f"\n🚀 开始签到站点: {site_name} ({site_url})\n"

    while retries < max_retries:
        try:
            msg += f"🔄 第 {retries + 1} 次尝试签到...\n"
            headers = {
                'Cookie': cookie,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
                'Referer': site_url
            }
            rsp = requests.get(url=site_url, headers=headers, timeout=15, verify=False)

            if rsp.status_code != 200:
                msg += f"❌ 站点 {site_name} 返回 HTTP 状态码 {rsp.status_code}\n"
                retries += 1
                time.sleep(retry_interval)
                continue

            rsp_text = rsp.text
            sign_count = re.search(r"这是您的第 <b>(\d+)</b> 次签到", rsp_text)
            continuous_days = re.search(r"已连续签到 <b>(\d+)</b> 天", rsp_text)
            earned_magic = re.search(r"本次签到获得 <b>(\d+)</b> 个魔力值", rsp_text)
            repair_card = re.search(r"你目前拥有补签卡 <b>(\d+)</b> 张", rsp_text)
            sign_rank = re.search(r"今日签到排名：<b>(\d+)</b> / <b>(\d+)</b>", rsp_text)

            if sign_count and earned_magic:
                msg += f"""
                ✅ 签到成功！
                📅 第 {sign_count.group(1)} 次签到
                🔥 连续签到 {continuous_days.group(1) if continuous_days else '未知'} 天
                ✨ 获得 {earned_magic.group(1)} 魔力值
                🎟️ 补签卡数量: {repair_card.group(1) if repair_card else '未知'}
                🏆 今日排名: {sign_rank.group(1) if sign_rank else '未知'} / {sign_rank.group(2) if sign_rank else '未知'}
                """
                success = True
                break
            else:
                msg += "⚠️ 签到失败，可能是 Cookie 失效或未匹配到签到成功信息。\n"
                retries += 1
                time.sleep(retry_interval)

        except Exception as e:
            msg += f"❌ 发生错误: {str(e)}\n"
            retries += 1
            time.sleep(retry_interval)

    if not success:
        msg += f"🚫 站点 {site_name} 签到失败，已跳过。\n"

    print(msg)
    return msg

if __name__ == "__main__":
    results = []

    if not pt_sites:
        print("❌ 未配置任何 PT 站点，请检查环境变量 PT_SITES。")
    else:
        for site in pt_sites:
            site_name = site.get("name")
            site_url = site.get("url")
            cookie = site.get("cookie")
            max_retries = site.get("max_retries", 3)  # 默认 3 次重试
            retry_interval = site.get("retry_interval", 20)  # 默认 20 秒重试间隔

            if not site_name or not site_url or not cookie:
                print(f"⚠️ 站点 {site_name} 配置不完整，已跳过。")
                continue

            result = sign_in(site_name, site_url, cookie, max_retries, retry_interval)
            results.append(result)

    # 发送通知（签到结果推送到 Server 酱）
    final_msg = "\n".join(results)
    send("📢 PT 站点签到结果", final_msg)
