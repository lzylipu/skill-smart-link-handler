# YouTube 链接智能下载 - 自动识别音乐

## 功能特性

### 1. 自动识别 YouTube 视频标题
- 使用 YouTube oEmbed API 获取视频标题
- 根据标题内容智能判断下载视频还是音频

### 2. 音频识别规则

**自动下载音频的情况**：
1. 标题包含音乐关键词
2. 标题格式为 "艺术家 - 歌曲名"

**音频关键词列表**：
- 英文：`music`, `mv`, `official music`, `audio`, `song`, `album`, `single`, `ost`, `soundtrack`, `remix`, `cover`, `lyrics`
- 中文：`音乐`, `歌曲`, `专辑`, `单曲`, `演唱会`, `live`, `纯音乐`, `伴奏`, `主题曲`, `插曲`

### 3. 强制模式
- 添加 `audio` 参数强制下载音频
- 添加 `video` 参数强制下载视频

---

## 使用示例

### 示例 1：音乐视频（自动识别为音频）

```bash
python3 smart-link-handler-final.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

**输出**：
```
📺 识别为 YouTube 链接
  → 获取视频标题...
  ✓ 标题：Rick Astley - Never Gonna Give You Up (Official Video)
  → 下载模式：音频 (标题包含音乐关键词，自动选择音频)
  → 提交到 MeTube...
  ✓ 下载任务已提交
✅ 处理完成：好了
```

**识别逻辑**：
- 标题包含 " - "（艺术家 - 歌曲名格式）
- 自动选择 **MP3 音频** 格式下载

---

### 示例 2：教程视频（默认视频）

```bash
python3 smart-link-handler-final.py "https://www.youtube.com/watch?v=jCCB27xgg9U"
```

**输出**：
```
📺 识别为 YouTube 链接
  → 获取视频标题...
  ✓ 标题：自制一个飞牛版 iStoreOS 旁路由+fndesk 图标快捷跳转...
  → 下载模式：视频 (默认视频模式)
  → 提交到 MeTube...
  ✓ 下载任务已提交
✅ 处理完成：好了
```

**识别逻辑**：
- 标题不包含音乐关键词
- 自动选择 **视频** 格式下载

---

### 示例 3：强制下载音频

```bash
python3 smart-link-handler-final.py "https://www.youtube.com/watch?v=jCCB27xgg9U" audio
```

**输出**：
```
📺 识别为 YouTube 链接
  → 获取视频标题...
  ✓ 标题：自制一个飞牛版 iStoreOS 旁路由+fndesk 图标快捷跳转...
  → 下载模式：音频 (用户指定音频模式)
  → 提交到 MeTube...
  ✓ 下载任务已提交
✅ 处理完成：好了
```

**识别逻辑**：
- 用户强制指定 `audio` 参数
- 忽略标题内容，强制下载 **MP3 音频**

---

### 示例 4：B 站视频

```bash
python3 smart-link-handler-final.py "https://www.bilibili.com/video/BV1MgXYBgErX"
```

**输出**：
```
📺 识别为 B 站链接
  → 下载模式：视频 (默认视频模式)
  → 提交到 MeTube...
  ✓ 下载任务已提交
✅ 处理完成：好了
```

---

## 下载格式

| 模式 | 格式 | 说明 |
|------|------|------|
| **视频** | `any` | 最高质量视频（含音频） |
| **音频** | `mp3` | 仅音频（MP3 格式） |

---

## 技术实现

### 1. YouTube oEmbed API
```python
def get_video_title(url: str) -> Optional[str]:
    """获取 YouTube 视频标题"""
    oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
    resp = requests.get(oembed_url, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        return data.get("title", "")
    return None
```

### 2. 智能判断逻辑
```python
def should_download_audio(self, url: str, title: Optional[str] = None) -> bool:
    """判断是否应该下载音频"""
    # 检查标题
    if title:
        title_lower = title.lower()
        
        # 检查是否包含艺术家 - 歌曲名格式
        if " - " in title and len(title) < 100:
            return True
        
        # 检查音乐关键词
        audio_keywords = ["music", "音乐", "mv", "歌曲", "专辑", ...]
        for keyword in audio_keywords:
            if keyword.lower() in title_lower:
                return True
    
    return False
```

---

## 配置

在 `TOOLS.md` 中配置 MeTube 服务地址：

```markdown
### Smart Link Handler

- **METUBE_ENDPOINT**: `http://YOUR_SERVER_IP:8081` - MeTube 视频下载服务
```

---

## 测试用例

| 链接类型 | 标题示例 | 预期结果 |
|----------|----------|----------|
| 音乐 MV | "周杰伦 - 告白气球 (Official MV)" | ✅ 音频 (MP3) |
| 音乐现场 | "Taylor Swift - Live at Wembley" | ✅ 音频 (MP3) |
| 音乐合集 | "Best Music 2024 Mix" | ✅ 音频 (MP3) |
| 教程视频 | "Python 入门教程" | ✅ 视频 |
| 产品介绍 | "iPhone 16 评测" | ✅ 视频 |
| 强制音频 | "任何标题" + `audio` 参数 | ✅ 音频 (MP3) |

---

**状态**: ✅ 完成  
**最后更新**: 2026-03-30
