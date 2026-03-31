---
name: smart-link-handler
description: 智能链接处理 - 自动识别夸克/YouTube/B 站链接并调用对应服务处理
---

# Smart Link Handler - 智能链接处理

> **Philosophy**: 用户只需发送链接，剩下的交给我。

## 功能

- ✅ **夸克分享链接** → 自动调用 QAS API 转存到网盘
- ✅ **YouTube 链接** → 自动调用 MeTube API 下载视频/音频
- ✅ **B 站链接** → 自动调用 MeTube API 下载视频/音频
- ✅ **智能识别**：自动检测链接类型，无需手动指定
- ✅ **模式选择**：支持视频模式（默认）和音频模式

## 配置

在 `TOOLS.md` 或环境变量中配置：

```markdown
### Smart Link Handler

- **QAS_ENDPOINT**: `http://YOUR_SERVER_IP:5015` - 夸克自动转存服务地址
- **QAS_TOKEN**: `YOUR_QAS_TOKEN` - QAS API Token
- **QAS_SAVE_ROOT**: `自动` - QAS 保存根目录
- **METUBE_ENDPOINT**: `http://YOUR_SERVER_IP:8081` - MeTube 服务地址
```

## 用法

### 方式 1: 命令行

```bash
# 夸克链接（自动转存）
python3 skills/smart-link-handler/smart-link-handler.py https://pan.quark.cn/s/xxx

# YouTube 链接（下载视频，默认）
python3 skills/smart-link-handler/smart-link-handler.py https://youtube.com/watch?v=xxx

# YouTube 链接（下载音频）
python3 skills/smart-link-handler/smart-link-handler.py https://youtube.com/watch?v=xxx audio

# B 站链接
python3 skills/smart-link-handler/smart-link-handler.py https://bilibili.com/video/BVxxx
```

### 方式 2: 在对话中直接使用

用户发送链接时，自动调用：

```python
from skills.smart_link_handler import process_link

# 自动识别并处理
process_link("https://pan.quark.cn/s/xxx")
process_link("https://youtube.com/watch?v=xxx")
process_link("https://youtube.com/watch?v=xxx audio")
```

## 链接识别规则

| 类型 | 匹配模式 | 处理器 |
|------|----------|--------|
| **夸克** | `pan.quark.cn/s/*` | QAS API |
| **YouTube** | `youtube.com/watch?v=*`, `youtu.be/*`, `youtube.com/shorts/*` | MeTube API |
| **B 站** | `bilibili.com/video/BV*`, `bilibili.com/video/av*`, `b23.tv/*` | MeTube API |

## 处理流程

### 夸克分享链接

```
用户发送链接
  ↓
调用 QAS /api/parse 解析分享
  ↓
获取分享目录名
  ↓
调用 QAS /api/tasks 创建任务
  ↓
调用 QAS /api/tasks/{id}/execute 执行
  ↓
调用 QAS /api/tasks/{id} 删除任务（清理）
  ↓
回复"好了"
```

### YouTube/B 站链接

```
用户发送链接
  ↓
识别链接类型（YouTube/B 站）
  ↓
判断模式（视频/音频）
  ↓
调用 MeTube POST /add
  ↓
回复"好了"
```

## API 参考

### QAS API

```bash
# 解析分享链接
POST /api/parse
{
  "url": "https://pan.quark.cn/s/xxx"
}
→ { "folder_name": "分享目录名", ... }

# 创建任务
POST /api/tasks
{
  "url": "https://pan.quark.cn/s/xxx",
  "task_name": "目录名",
  "save_path": "/自动/目录名"
}
→ { "task_id": 123 }

# 执行任务
POST /api/tasks/{task_id}/execute
→ 200 OK

# 删除任务
DELETE /api/tasks/{task_id}
→ 200/204
```

### MeTube API

```bash
# 添加下载任务
POST /add
{
  "url": "https://youtube.com/watch?v=xxx",
  "quality": "best",
  "format": "any",  # any=视频，mp3=音频
  "auto_start": true
}
→ 200 OK
```

## 输出规范

**成功**: `好了`  
**失败**: `错`

可选详细信息：
- 夸克：`好了 - 已转存：分享目录名`
- YouTube: `好了 - 已提交下载：YouTube 视频`

## 错误处理

| 错误 | 可能原因 | 处理方式 |
|------|----------|----------|
| 链接无效 | 格式错误或已失效 | 回复"错 - 链接无效" |
| QAS 不可用 | 服务未启动或网络问题 | 回复"错 - 转存服务不可用" |
| MeTube 不可用 | 服务未启动或网络问题 | 回复"错 - 下载服务不可用" |
| 需要登录 | 夸克分享需要登录 | 回复"错 - 分享需要登录" |

## 依赖

| 依赖 | 用途 |
|------|------|
| `requests` | HTTP 客户端 |
| QAS 服务 | 夸克自动转存后端 |
| MeTube 服务 | 视频下载后端 |

## 示例对话

### 夸克转存

```
用户：https://pan.quark.cn/s/461b6af90a65
AI: 📥 开始处理夸克分享...
    → 解析分享链接...
    ✓ 分享目录：电影 2024
    → 创建转存任务...
    ✓ 任务 ID: 123
    → 执行转存...
    ✓ 转存成功
    → 清理任务记录...
✅ 好了
```

### YouTube 下载（视频）

```
用户：https://youtube.com/watch?v=dQw4w9WgXcQ
AI: 🔗 检测到 youtube 链接
    📺 识别为 YouTube 链接
    → 下载模式：视频
    → 提交到 MeTube...
    ✓ 下载任务已提交
✅ 好了
```

### YouTube 下载（音频）

```
用户：https://youtube.com/watch?v=xxx audio
AI: 🔗 检测到 youtube 链接
    📺 识别为 YouTube 链接
    → 下载模式：音频
    → 提交到 MeTube...
    ✓ 下载任务已提交
✅ 好了 - 已提取音频
```

### B 站下载

```
用户：https://b23.tv/abc123
AI: 🔗 检测到 bilibili 链接
    📺 识别为 B 站链接
    → 下载模式：视频
    → 提交到 MeTube...
    ✓ 下载任务已提交
✅ 好了
```

## 扩展建议

1. **进度通知**: 轮询 QAS/MeTube 状态，推送完成通知
2. **批量处理**: 支持一次发送多个链接
3. **质量选择**: 支持指定视频质量（1080p/720p 等）
4. **历史记录**: 记录处理历史，支持查询
5. **Webhook**: 下载完成后回调通知

---

**版本**: 1.0  
**作者**: OpenClaw AI Assistant  
**创建时间**: 2026-03-30
