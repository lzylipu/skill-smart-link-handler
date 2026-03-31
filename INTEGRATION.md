# Smart Link Handler - 集成指南

## 在 OpenClaw 对话中使用

### 方法 1: 直接调用脚本

当用户发送链接时，在回复中调用：

```python
import subprocess

def handle_user_link(link_text: str):
    """处理用户发送的链接"""
    result = subprocess.run(
        ['python3', 'skills/smart-link-handler/smart-link-handler.py', link_text],
        capture_output=True, text=True, timeout=60
    )
    
    if result.returncode == 0:
        return "✅ 好了"
    else:
        return "❌ 错"
```

### 方法 2: 作为 Skill 自动触发

在 `SOUL.md` 或会话规则中添加：

```markdown
## 链接处理规则

当用户发送以下链接时，自动调用 smart-link-handler：

- 夸克分享链接 (`pan.quark.cn/s/*`) → 自动转存
- YouTube 链接 → 自动下载（视频模式，除非用户指定 audio）
- B 站链接 → 自动下载（视频模式）

调用方式：
```bash
python3 skills/smart-link-handler/smart-link-handler.py "<链接>" [audio]
```
```

### 方法 3: 导入为 Python 模块

```python
import sys
sys.path.insert(0, '/vol1/@apphome/trim.openclaw/data/workspace/skills')

from smart_link_handler.smart_link_handler import (
    detect_link_type,
    extract_link,
    process_link,
    QuarkAutoSaveClient,
    MeTubeClient
)

# 直接使用
text = "https://youtube.com/watch?v=xxx"
success = process_link(text)

# 或分别处理
link = extract_link(text)
link_type = detect_link_type(text)

if link_type == "quark":
    client = QuarkAutoSaveClient(...)
    client.process_share(link)
elif link_type in ["youtube", "bilibili"]:
    client = MeTubeClient(...)
    client.process_video(link)
```

## 在 Telegram Bot 中集成

如果你想在原有的 Telegram Bot 中集成这个 Skill：

### 修改 `bot.py`

```python
from smart_link_handler import process_link

@bot.on_message(filters.text & filters.private)
async def handle_text(client, message):
    text = message.text
    
    # 检测是否包含链接
    if any(domain in text for domain in ['pan.quark.cn', 'youtube.com', 'youtu.be', 'bilibili.com', 'b23.tv']):
        # 调用智能处理
        success = process_link(text)
        
        if success:
            await message.reply("好了")
        else:
            await message.reply("错")
```

## 环境变量配置

### Docker 部署

```yaml
# docker-compose.yml
services:
  smart-link-handler:
    image: python:3.11-slim
    volumes:
      - ./skills:/app/skills
    environment:
      - QAS_ENDPOINT=http://YOUR_SERVER_IP:5015
      - QAS_TOKEN=YOUR_QAS_TOKEN
      - QAS_SAVE_ROOT=自动
      - METUBE_ENDPOINT=http://YOUR_SERVER_IP:8081
    working_dir: /app
    command: python3 skills/smart-link-handler/smart-link-handler.py
```

### Systemd 服务

```ini
# /etc/systemd/system/smart-link-handler.service
[Unit]
Description=Smart Link Handler Service
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /vol1/@apphome/trim.openclaw/data/workspace/skills/smart-link-handler/smart-link-handler.py
Environment=QAS_ENDPOINT=http://YOUR_SERVER_IP:5015
Environment=QAS_TOKEN=YOUR_QAS_TOKEN
Environment=METUBE_ENDPOINT=http://YOUR_SERVER_IP:8081
WorkingDirectory=/vol1/@apphome/trim.openclaw/data/workspace

[Install]
WantedBy=multi-user.target
```

## Webhook 集成

如果你想在其他服务中调用：

### FastAPI Webhook

```python
from fastapi import FastAPI
from smart_link_handler import process_link

app = FastAPI()

@app.post("/webhook/link")
async def handle_link(link: str, mode: str = "video"):
    success = process_link(f"{link} {mode}")
    return {"success": success, "message": "好了" if success else "错"}
```

调用：
```bash
curl -X POST http://localhost:8000/webhook/link \
  -H "Content-Type: application/json" \
  -d '{"link": "https://youtube.com/watch?v=xxx", "mode": "audio"}'
```

## 错误处理最佳实践

```python
import subprocess
import json

def safe_process_link(link_text: str):
    """安全的链接处理，带错误处理"""
    try:
        result = subprocess.run(
            ['python3', 'skills/smart-link-handler/smart-link-handler.py', link_text],
            capture_output=True, text=True, timeout=60
        )
        
        # 解析输出
        output = result.stdout
        error = result.stderr
        
        if result.returncode == 0:
            return {
                "success": True,
                "message": "好了",
                "details": output
            }
        else:
            # 尝试从输出中提取错误原因
            error_msg = "错"
            if "404" in error:
                error_msg = "错 - 服务不可用"
            elif "无效链接" in output:
                error_msg = "错 - 链接无效"
            
            return {
                "success": False,
                "message": error_msg,
                "error": error
            }
    
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "message": "错 - 处理超时",
            "error": "Timeout"
        }
    except Exception as e:
        return {
            "success": False,
            "message": "错 - 未知错误",
            "error": str(e)
        }
```

## 日志记录

```python
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    filename='logs/smart-link-handler.log',
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)

def log_link_processing(link: str, link_type: str, success: bool):
    """记录链接处理日志"""
    status = "SUCCESS" if success else "FAILED"
    logging.info(f"[{status}] {link_type}: {link}")
```

## 监控与告警

```python
# 监控脚本
import requests

def check_services():
    """检查后端服务状态"""
    services = {
        "QAS": "http://YOUR_SERVER_IP:5015/health",
        "MeTube": "http://YOUR_SERVER_IP:8081/health"
    }
    
    for name, url in services.items():
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code != 200:
                send_alert(f"{name} 服务异常：{resp.status_code}")
        except Exception as e:
            send_alert(f"{name} 服务不可达：{e}")

def send_alert(message: str):
    """发送告警（邮件/短信/Telegram）"""
    # 实现告警逻辑
    pass
```

---

**最后更新**: 2026-03-30  
**版本**: 1.0
