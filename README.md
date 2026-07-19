# 🔗 Smart Link Handler / 智能外链下载器

> 🌐 English | [简体中文](./README.md)
> Auto-detect Quark/YouTube/Bilibili links and trigger downloads to local hosts.
> 智能识别夸克网盘、YouTube、B站外链，并推送到 MeTube/Alist/aria2 离线下载。

## ✨ Features / 特性

- 📂 **Quark auto-save** — auto-save via QAS / 夸克网盘自动转存
- 🎥 **Video push** — YouTube/Bilibili download via MeTube / 推送视频到 MeTube
- 📦 **aria2 batch** — episode matching (E01, E02...) + bulk downloads / 剧集批量离线下载

## ⚙️ Prerequisites / 配置

| Variable | Description |
|----------|-------------|
| `QAS_ENDPOINT` | QAS service URL / QAS 服务地址 |
| `QAS_TOKEN` | QAS API token / QAS 鉴权令牌 |
| `ALIST_ENDPOINT` | Alist service URL / Alist 服务地址 |
| `ALIST_TOKEN` | Alist auth token / Alist 管理员令牌 |
| `ARIA2_ENDPOINT` | aria2 RPC URL / aria2 接口地址 |
| `ARIA2_TOKEN` | aria2 RPC token / aria2 远程连接密码 |

## 🚀 Usage / 使用

```bash
# Download specific episodes / 下载指定剧集
python3 scripts/quark-download.py "share_link" E01 E05 E10

# Download all / 下载全部
python3 scripts/quark-download.py "share_link"

# Task management / 任务管理
python3 scripts/quark-download.py --list
python3 scripts/quark-download.py --clear
```

## 📄 License / 许可证

MIT
