---
name: smart-link-handler
description: "Smart link handler - auto-detect and download Quark/YouTube/Bilibili links"
version: 13.0.0
author: lzylipu
license: MIT
platforms: [linux]
prerequisites:
  env_vars: [QAS_ENDPOINT, QAS_TOKEN, ALIST_ENDPOINT, ALIST_TOKEN, ARIA2_ENDPOINT, ARIA2_TOKEN]
  services:
    - name: QAS
      description: "Quark Auto Save service"
    - name: Alist
      description: "File listing service"
    - name: aria2
      description: "Download manager RPC"
metadata:
  hermes:
    tags: [quark, youtube, bilibili, download, video, link, 夸克, 下载, 链接]
    related_skills: [daily-morning-brief, vpn-connect]
    homepage: https://github.com/lzylipu/openclaw-skill-smart-link-handler
    category: personal
    skill_type: automation
---

# Smart Link Handler

> v13.0

自动识别夸克网盘分享链接和视频网站链接，调用对应服务下载。

## 夸克转存

### 流程

```
1. 收到夸克分享链接
2. QAS 全量转存
3. Alist 刷新文件列表
4. 按剧集匹配下载（E01, E02...）
5. QAS 清空任务
```

### 使用

```bash
# 指定剧集下载
python3 quark-download.py "链接" E01 E05 E10
python3 quark-download.py "链接" E01-E10

# 全量下载
python3 quark-download.py "链接"

# 任务管理
python3 quark-download.py --list
python3 quark-download.py --clear
```

### 环境变量配置

| 变量 | 说明 |
|------|------|
| QAS_ENDPOINT | QAS 服务地址 |
| QAS_TOKEN | QAS API Token |
| ALIST_ENDPOINT | Alist 服务地址 |
| ALIST_TOKEN | Alist 认证 Token |
| ARIA2_ENDPOINT | aria2 RPC 地址 |
| ARIA2_TOKEN | aria2 RPC Token |

所有凭据通过环境变量传入，不要硬编码到代码中。

## MeTube 视频下载

发链接自动下载最清晰视频，发链接 + 1 下载 MP3 音频。

## 更新日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v13.0 | 2026-06-21 | 清理废弃文件，凭据改为环境变量 |
| v12.0 | 2026-04-04 | 夸克剧集匹配 + MeTube 音频模式 |