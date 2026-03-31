# Smart Link Handler - OpenClaw Skill

智能链接处理技能，自动识别并处理夸克分享、YouTube、B站链接。

## 功能特性

- **夸克分享链接** → 自动调用 QAS API 转存到网盘
- **YouTube 链接** → 自动调用 MeTube API 下载视频/音频
- **B 站链接** → 自动调用 MeTube API 下载视频/音频
- **智能识别** → 自动检测链接类型，无需手动指定
- **模式选择** → 支持视频模式（默认）和音频模式

## 安装

### 1. 安装依赖

```bash
pip install requests
```

### 2. 配置环境变量

```bash
# 夸克自动转存服务配置
export QAS_ENDPOINT="http://YOUR_SERVER_IP:5015"
export QAS_TOKEN="YOUR_QAS_TOKEN"
export QAS_SAVE_ROOT="自动"  # 保存根目录

# MeTube视频下载服务配置
export METUBE_ENDPOINT="http://YOUR_SERVER_IP:8081"
```

### 3. 安装到OpenClaw

将此技能目录复制到OpenClaw的skills目录：

```bash
cp -r smart-link-handler /path/to/openclaw/skills/
```

## 使用方法

### 命令行使用

```bash
# 夸克链接（自动转存）
python3 smart-link-handler.py https://pan.quark.cn/s/xxx

# YouTube链接（下载视频，默认）
python3 smart-link-handler.py https://youtube.com/watch?v=xxx

# YouTube链接（下载音频）
python3 smart-link-handler.py https://youtube.com/watch?v=xxx audio

# B站链接
python3 smart-link-handler.py https://bilibili.com/video/BVxxx
```

### OpenClaw对话中使用

用户只需发送链接，技能会自动识别并处理：

```
用户: https://pan.quark.cn/s/abc123
AI: 正在处理夸克分享链接...
    已转存到：/自动/分享目录名

用户: https://youtube.com/watch?v=xyz789 audio
AI: 正在下载YouTube音频...
    下载完成：Song Title.mp3
```

## 支持的链接类型

| 类型 | 匹配模式 | 处理方式 |
|------|----------|----------|
| **夸克** | `pan.quark.cn/s/*` | QAS API 转存 |
| **YouTube** | `youtube.com/watch?v=*`<br>`youtu.be/*`<br>`youtube.com/shorts/*` | MeTube API 下载 |
| **B站** | `bilibili.com/video/BV*`<br>`bilibili.com/video/av*`<br>`b23.tv/*` | MeTube API 下载 |

## 配置说明

### QAS（夸克自动转存）配置

需要自行部署 [Quark-Auto-Save](https://github.com/your-repo/quark-auto-save) 服务：

- **QAS_ENDPOINT**: QAS服务地址
- **QAS_TOKEN**: API访问令牌
- **QAS_SAVE_ROOT**: 夸克网盘保存根目录

### MeTube配置

需要自行部署 [MeTube](https://github.com/alexta69/metube) 服务：

- **METUBE_ENDPOINT**: MeTube服务地址

## 工作原理

### 夸克分享链接处理流程

1. 解析分享链接获取目录信息
2. 创建转存任务
3. 执行转存操作
4. 清理临时任务
5. 返回转存结果

### YouTube/B站链接处理流程

1. 识别链接类型和模式（视频/音频）
2. 调用MeTube API添加下载任务
3. 等待下载完成
4. 返回下载结果

## 技术实现

- **Python 3** - 主要编程语言
- **requests** - HTTP请求库
- **正则表达式** - 链接类型识别
- **环境变量** - 配置管理

## 注意事项

- 需要先部署QAS和MeTube服务
- 确保网络可访问相关服务
- Telegram通知功能需要配置Bot Token（可选）

## 许可证

MIT License

## 作者

OpenClaw Community

## 相关链接

- [OpenClaw](https://github.com/openclaw/openclaw)
- [MeTube](https://github.com/alexta69/metube)
- [QAS (Quark Auto Save)](https://github.com/your-repo/quark-auto-save)