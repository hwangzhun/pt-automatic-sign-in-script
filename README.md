# pt-automatic-sign-in-script
## 自用签到脚本

1. 使用前需要在环境变量添加 *PT_SITES*
   
   ``` jason
    [
        {
        "name": "站点1",
        "url": "https://xxx.com/attendance.php",
        "cookie": "你的cookie",
        "max_retries": 5, // 最大重复次数
        "retry_interval": 10  // 重复最大等待时间 单位；秒
        },
        {
        "name": "站点2",
        "url": "https://yyy.com/attendance.php",
        "cookie": "你的cookie",
        "max_retries": 5, // 最大重复次数
        "retry_interval": 10  // 重复最大等待时间 单位；秒
        }
    ]
   ```

2. 如果需要使用代理的，请添加 PT_PROXY 

    ``` jason
    http://127.0.0.1:8080
    ```

3. 在青龙面板添加订阅:
   https://raw.githubusercontent.com/hwangzhun/pt-automatic-sign-in-script/refs/heads/main/Sign_in.py

4. 因为解析数据用到了 Xpath 注意青龙面板里需要添加依赖才能正常工作

## 感谢
参考 [icc2022-sign-in](https://github.com/KunCheng-He/icc2022-sign-in)


