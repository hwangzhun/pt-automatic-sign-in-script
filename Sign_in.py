"""
@Author: Hwangzhun
@Date: 2025-02-01
@Description: PT 站点自动签到脚本，支持多个站点，支持繁体/简体站点，支持代理，适用于青龙面板
@Version: v1.1
"""


import os
import re
import time
import requests
from notify import send  # 青龙面板自带通知模块

# 关闭 SSL 证书警告
requests.packages.urllib3.disable_warnings()

# 读取环境变量
PT_SITES = os.getenv("PT_SITES")  # 站点信息 (JSON 格式)
PT_PROXY = os.getenv("PT_PROXY", "")  # 代理地址 (统一代理)
SERVER_KEY = os.getenv("SERVERCHAN_SENDKEY")  # Server 酱通知推送 Key

# 检查 PT_SITES 变量是否为空
if not PT_SITES:
    print("❌ 未找到 PT_SITES 变量，请在青龙面板中配置！")
    exit(1)

# 解析 JSON 站点列表
try:
    pt_sites = eval(PT_SITES)  # 解析 JSON
except Exception as e:
    print("❌ 解析 PT_SITES 变量失败，请检查格式是否正确！", str(e))
    exit(1)

# 代理配置（如果 PT_PROXY 为空，则不使用代理）
proxies = {"http": PT_PROXY, "https": PT_PROXY} if PT_PROXY else None

# 遍历所有 PT 站点签到
results = []
for site in pt_sites:
    site_name = site.get("name")  # 站点名称
    sign_in_url = site.get("url")  # 签到地址
    cookie = site.get("cookie")  # 站点 Cookie
    max_retries = site.get("max_retries", 3)  # 最大重试次数
    retry_interval = site.get("retry_interval", 20)  # 重试间隔（秒）

    print(f"🚀 开始签到：{site_name}")
    retries = 0
    success = False

    while retries < max_retries:
        try:
            # 发送签到请求
            headers = {
                "Cookie": cookie,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            }
            response = requests.get(sign_in_url, headers=headers, proxies=proxies, timeout=15, verify=False)
            response_text = response.text  # 获取响应内容

            # 解析签到信息（兼容繁体/简体）
            pattern = r'(?:这是您的第|這是您的第) <b>(\d+)</b> (?:次签到|次簽到)，(?:已连续签到|已連續簽到) <b>(\d+)</b> (?:天，本次签到获得|天，本次簽到獲得) <b>(\d+)</b> (?:个魔力值|個魔力值)'
            match = re.search(pattern, response_text)

            if match:
                total_signin = match.group(1)
                consecutive_days = match.group(2)
                earned_points = match.group(3)
                result_msg = f"✅ {site_name} 签到成功！\n- 第 {total_signin} 次签到\n- 连续签到 {consecutive_days} 天\n- 获得魔力值: {earned_points}"
                print(result_msg)
                results.append(result_msg)
                success = True
                break  # 成功签到后跳出循环

            elif "503 Service Temporarily" in response_text or "502 Bad Gateway" in response_text:
                print(f"⚠️ {site_name} 服务器异常，稍后重试...")
            else:
                print(f"❌ {site_name} 签到失败，未能解析签到信息！")
                print(response_text[:500])  # 输出部分响应内容，方便调试

        except Exception as e:
            print(f"⚠️ {site_name} 请求失败: {str(e)}")

        retries += 1
        if retries < max_retries:
            print(f"⏳ 等待 {retry_interval} 秒后重试...")
            time.sleep(retry_interval)
    
    if not success:
        results.append(f"❌ {site_name} 签到失败，达到最大重试次数！")

# 发送签到结果通知
if SERVER_KEY and results:
    send("PT 站签到结果", "\n\n".join(results))

print("🎉 所有站点签到任务完成！")