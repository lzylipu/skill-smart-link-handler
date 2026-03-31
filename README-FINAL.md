# Smart Link Handler - 最终版

## 配置（根据用户 Docker 命令）

```bash
# TOOLS.md 配置
QAS_ENDPOINT: http://YOUR_SERVER_IP:5015
QAS_TOKEN: YOUR_QAS_TOKEN
QAS_SAVE_ROOT: 自动
METUBE_ENDPOINT: http://YOUR_SERVER_IP:8081
```

## 文件结构

```
skills/smart-link-handler/
├── smart-link-handler-quark.py    # 夸克转存（已测试通过✅）
├── smart-link-handler-final.py    # YouTube/B站下载（已测试通过✅）
├── SKILL.md                        # Skill 描述
└── README-FINAL.md                 # 本文档
```

## 测试结果

### 夸克转存 ✅
```bash
python3 smart-link-handler-quark.py "https://pan.quark.cn/s/5d927bcc58ad"
# 输出：✅ 处理完成：好了
```

### YouTube 下载 ✅
```bash
python3 smart-link-handler-final.py "https://youtube.com/watch?v=jCCB27xgg9U"
# 输出：✅ 处理完成：好了
```

### B 站下载 ✅
```bash
python3 smart-link-handler-final.py "https://www.bilibili.com/video/BV1MgXYBgErX"
# 输出：✅ 处理完成：好了
```

## API 端点

### QAS (夸克自动转存)
- **地址**: `http://YOUR_SERVER_IP:5015`
- **认证**: `?token=YOUR_QAS_TOKEN`
- **端点**:
  - `GET /data` - 获取任务列表
  - `POST /get_share_detail` - 解析分享链接
  - `POST /api/add_task` - 添加转存任务
  - `POST /run_script_now` - 执行转存

### MeTube (视频下载)
- **地址**: `http://YOUR_SERVER_IP:8081`
- **端点**: `POST /add`
- **参数**: `{"url": "...", "quality": "best", "format": "any/mp3", "auto_start": true}`

## 使用方式

### 1. 命令行
```bash
# 夸克
python3 skills/smart-link-handler/smart-link-handler-quark.py "链接"

# YouTube/B站
python3 skills/smart-link-handler/smart-link-handler-final.py "链接" [audio]
```

### 2. 在对话中自动调用
当用户发送链接时，自动识别并调用对应处理器。

---

**状态**: ✅ 完成并测试通过
**最后更新**: 2026-03-30
