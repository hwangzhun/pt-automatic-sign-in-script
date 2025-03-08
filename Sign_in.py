"""
@Author: Hwangzhun
@Date: 2025-03-08
@Description: PT 站点自动签到脚本，仅支持 NexusPHP 框架的站点，支持代理，适用于青龙面板
@Version: v1.3
"""

import os
import time
import requests
from lxml import etree
from notify import send  # 青龙面板通知模块

# 禁用SSL证书警告
requests.packages.urllib3.disable_warnings()

# 环境变量配置
PT_SITES = os.getenv("PT_SITES")  # JSON格式站点配置
PT_PROXY = os.getenv("PT_PROXY")  # 全局代理(可选)
MAX_RETRIES = int(os.getenv("PT_MAX_RETRIES", 3))  # 最大重试次数
RETRY_INTERVAL = int(os.getenv("PT_RETRY_INTERVAL", 30))  # 重试间隔(秒)


def parse_ratio(raw_str):
    """解析分享率数值 (如：'5.175' -> 5.175)"""
    try:
        # 检查 raw_str 是否有 '分享率:' 字符串前缀，如果有则去掉
        if '分享率:' in raw_str:
            return float(raw_str.split(":")[1].strip())
        return float(raw_str.strip())  # 如果已经是数值字符串，直接转化
    except (IndexError, ValueError, AttributeError):
        return "N/A"

def parse_bonus(raw_str):
    """解析魔力值 (如：'魔力值 [使用]: 118,183.1' -> 118183.1)"""
    try:
        return float(raw_str.split(":")[1].strip().replace(",", ""))
    except (IndexError, ValueError, AttributeError):
        return "N/A"

def main():
    if not PT_SITES:
        print("❌ 未找到 PT_SITES 环境变量")
        exit(1)

    try:
        sites = eval(PT_SITES)  # 解析JSON配置
    except Exception as e:
        print(f"❌ 配置解析失败: {str(e)}")
        exit(1)

    global_proxies = {"http": PT_PROXY, "https": PT_PROXY} if PT_PROXY else None
    results = []

    for site in sites:
        site_name = site.get("name", "未知站点")
        sign_url = site.get("url")
        cookie = site.get("cookie")
        site_proxy = site.get("proxy")
        retries = 0
        success = False

        # 代理优先级：站点代理 > 全局代理
        proxies = {"http": site_proxy, "https": site_proxy} if site_proxy else global_proxies

        print(f"\n🚀 开始处理 [{site_name}]")

        while retries < MAX_RETRIES:
            try:
                # 发送请求
                headers = {
                    "Cookie": cookie,
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
                }
                response = requests.get(
                    sign_url,
                    headers=headers,
                    proxies=proxies,
                    timeout=20,
                    verify=False
                )
                response.raise_for_status()
                tree = etree.HTML(response.text)

                # 解析用户信息
                username = tree.xpath('//a[@class="PowerUser_Name" or @class="User_Name"]/b/text()')
                username = username[0].strip() if username else "N/A"

                # 解析数值数据
                bonus_raw = tree.xpath('//a[@href="mybonus.php"]/following-sibling::text()[1]')
                bonus = parse_bonus(bonus_raw[0]) if bonus_raw else "N/A"

                # 解析分享率
                ratio_raw = tree.xpath('//font[@class="color_ratio"]/following-sibling::text()[1]')
                ratio = parse_ratio(ratio_raw[0].strip()) if ratio_raw else "N/A"
                
                # 解析上传量
                upload_raw = tree.xpath('//font[@class="color_uploaded"]/following-sibling::text()[1]')
                upload = upload_raw[0].strip() if ratio_raw else "N/A"

                #解析下载量
                download_raw = tree.xpath('//font[@class="color_downloaded"]/following-sibling::text()[1]')
                download = download_raw[0].strip() if ratio_raw else "N/A"
                
                # 解析签到数据
                sign_data = tree.xpath('//td[@class="text"]//p//b/text()')
                total_sign = sign_data[0] if len(sign_data) > 0 else "N/A"
                continuous_sign = sign_data[1] if len(sign_data) > 1 else "N/A"
                current_bonus = sign_data[2] if len(sign_data) > 2 else "N/A"

                # 构建结果消息
                result_msg = f"""✅ {site_name} 签到成功！
├ 用户名：{username}
├ 当前魔力：{bonus if isinstance(bonus, float) else bonus}
├ 分享比率：{ratio}
├ 上传总量：{upload}
├ 下载总量：{download}
├ 签到统计：第 {total_sign} 次（连续 {continuous_sign} 天）
└ 本次获得：{current_bonus} 魔力"""

                print(result_msg)
                results.append(result_msg)
                success = True
                break

            except requests.exceptions.RequestException as e:
                print(f"⚠️ 网络请求失败: {str(e)}")
            except IndexError as e:
                print(f"⚠️ 解析失败，可能页面结构变更: {str(e)}")
            except Exception as e:
                print(f"⚠️ 发生意外错误: {str(e)}")
            
            retries += 1
            if retries < MAX_RETRIES:
                print(f"⏳ 等待 {RETRY_INTERVAL}秒后重试 ({retries}/{MAX_RETRIES})...")
                time.sleep(RETRY_INTERVAL)

        if not success:
            fail_msg = f"❌ {site_name} 签到失败，已达最大重试次数"
            print(fail_msg)
            results.append(fail_msg)

    # 发送通知
    if results:
        send("PT 站点签到报告", "\n\n".join(results))
    print("\n🎉 所有站点处理完成！")

if __name__ == "__main__":
    main()