#!/usr/bin/env python3
"""
智能链接处理 Skill - 最终版（匹配真实 API）

功能：
- 夸克分享链接 → 调用 QAS /update + /run_script_now 转存  
- YouTube/B 站链接 → 调用 MeTube /add 下载
- 智能识别链接类型
- 支持视频/音频模式选择
"""

import os
import re
import sys
import json
import requests
from typing import Optional, Dict, Any, List

# ==================== 配置区域 ====================
QAS_ENDPOINT = os.environ.get("QAS_ENDPOINT", "http://YOUR_SERVER_IP:5015")
QAS_TOKEN = os.environ.get("QAS_TOKEN", "YOUR_QAS_TOKEN")
QAS_SAVE_ROOT = os.environ.get("QAS_SAVE_ROOT", "自动")

METUBE_ENDPOINT = os.environ.get("METUBE_ENDPOINT", "http://YOUR_SERVER_IP:8081")

LINK_PATTERNS = {
    "quark": [r"pan\.quark\.cn/s/[a-zA-Z0-9]+"],
    "youtube": [r"(youtube\.com/watch\?v=|youtu\.be/)[a-zA-Z0-9_-]+"],
    "bilibili": [r"bilibili\.com/video/(BV[a-zA-Z0-9]+|av\d+)"],
}


def detect_link_type(text: str) -> Optional[str]:
    """检测链接类型"""
    for link_type, patterns in LINK_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return link_type
    return None


def extract_link(text: str) -> Optional[str]:
    """从文本中提取链接"""
    url_pattern = r"https?://[^\s<>\[\]\"']+"
    match = re.search(url_pattern, text)
    return match.group(0) if match else None


# ==================== QAS 客户端（最终版）====================
class QuarkAutoSaveClient:
    """夸克自动转存客户端 - 直接操作 tasklist"""
    
    def __init__(self, endpoint: str, token: str, save_root: str = "自动"):
        self.endpoint = endpoint.rstrip("/")
        self.token = token
        self.save_root = save_root
        self.session = requests.Session()
        self.session.params = {"token": token}
    
    def create_task_item(self, title: str, share_url: str) -> Dict[str, Any]:
        """创建任务项"""
        return {
            "taskname": title,
            "shareurl": share_url,
            "savepath": f"/{self.save_root}/{title}",
            "enddate": "",
            "week": [],
            "pattern": "",
            "replace": "",
            "aria2": {
                "auto_download": True,
                "pause": False,
                "save_path": ""
            }
        }
    
    def update_tasks(self, tasklist: List[Dict[str, Any]]) -> bool:
        """更新任务列表"""
        try:
            resp = self.session.post(
                f"{self.endpoint}/update",
                json={"tasklist": tasklist},
                timeout=30
            )
            return resp.status_code == 200
        except Exception as e:
            print(f"❌ QAS 更新失败：{e}")
            return False
    
    def run_script_for_task(self, task_item: Dict[str, Any]) -> bool:
        """执行单个任务的转存脚本"""
        try:
            # 移除不需要的字段
            task_payload = task_item.copy()
            if "runweek" in task_payload:
                del task_payload["runweek"]
            
            payload = {"tasklist": [task_payload]}
            
            resp = self.session.post(
                f"{self.endpoint}/run_script_now",
                json=payload,
                timeout=300
            )
            return resp.status_code == 200
        except Exception as e:
            print(f"❌ QAS 执行失败：{e}")
            return False
    
    def process_share(self, share_url: str) -> bool:
        """处理夸克分享链接"""
        print(f"📥 开始处理夸克分享：{share_url}")
        
        # 创建任务项（简化标题）
        folder_name = "夸克分享"
        task_item = self.create_task_item(folder_name, share_url)
        print(f"  ✓ 任务标题：{folder_name}")
        
        # 添加任务
        print("  → 添加转存任务...")
        if not self.update_tasks([task_item]):
            return False
        print("  ✓ 任务添加成功")
        
        # 执行转存
        print("  → 执行转存...")
        if not self.run_script_for_task(task_item):
            return False
        print("  ✓ 转存执行成功")
        
        # 清理任务（发送空任务列表）
        print("  → 清理任务记录...")
        self.update_tasks([])
        
        return True


# ==================== MeTube 客户端 ====================
class MeTubeClient:
    """MeTube 下载客户端 - 支持 YouTube 标题识别"""
    
    def __init__(self, endpoint: str):
        self.endpoint = endpoint.rstrip("/")
        self.session = requests.Session()
    
    def get_video_title(self, url: str) -> Optional[str]:
        """获取 YouTube 视频标题（通过 oEmbed API）"""
        try:
            # 使用 YouTube oEmbed API 获取标题
            oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
            resp = requests.get(oembed_url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("title", "")
            return None
        except Exception as e:
            return None
    
    def should_download_audio(self, url: str, title: Optional[str] = None) -> bool:
        """
        判断是否应该下载音频
        规则：
        1. URL 中包含 /shorts/ → 视频
        2. 标题包含 music/音乐/MV 等 → 音频
        3. 其他 → 视频
        """
        # 关键词列表（音频）
        audio_keywords = [
            # 英文
            "music", "mv", "official music", "audio", "song",
            "album", "single", "ost", "soundtrack", "remix", "cover",
            "lyrics", "lyric video", "music video",
            # 中文
            "音乐", "歌曲", "专辑", "单曲", "演唱会",
            "live", "纯音乐", "伴奏", "主题曲", "插曲",
            # 特殊格式（艺术家 - 歌曲名）
            " - ",  # 艺术家和歌曲名分隔符
        ]
        
        # 检查标题
        if title:
            title_lower = title.lower()
            
            # 检查是否包含艺术家 - 歌曲名格式（如 "Artist - Song"）
            if " - " in title and len(title) < 100:
                # 短标题且有分隔符，很可能是音乐
                return True
            
            for keyword in audio_keywords:
                if keyword.lower() in title_lower:
                    return True
        
        return False
    
    def add_download(self, url: str, is_audio: bool = False) -> bool:
        """添加下载任务"""
        try:
            params = {
                "url": url,
                "quality": "best",
                "format": "mp3" if is_audio else "any",
                "auto_start": True
            }
            
            resp = self.session.post(
                f"{self.endpoint}/add",
                json=params,
                timeout=30
            )
            
            if resp.status_code == 200:
                return True
            else:
                print(f"❌ MeTube 添加失败：{resp.status_code}")
                return False
        except Exception as e:
            print(f"❌ MeTube 请求异常：{e}")
            return False
    
    def process_video(self, url: str, force_audio: bool = False) -> bool:
        """
        处理视频下载
        force_audio: 用户强制指定音频模式
        """
        link_type = detect_link_type(url)
        
        if link_type == "youtube":
            print(f"📺 识别为 YouTube 链接")
            
            # 获取视频标题
            print("  → 获取视频标题...")
            title = self.get_video_title(url)
            if title:
                print(f"  ✓ 标题：{title[:60]}...")
            else:
                print("  ⚠️ 无法获取标题")
            
            # 判断下载模式
            if force_audio:
                is_audio = True
                mode_desc = "用户指定音频模式"
            elif title and self.should_download_audio(url, title):
                is_audio = True
                mode_desc = "标题包含音乐关键词，自动选择音频"
            else:
                is_audio = False
                mode_desc = "默认视频模式"
            
        elif link_type == "bilibili":
            print(f"📺 识别为 B 站链接")
            is_audio = force_audio
            mode_desc = "用户指定音频模式" if force_audio else "默认视频模式"
        else:
            print(f"📺 识别为通用视频链接")
            is_audio = force_audio
            mode_desc = "用户指定音频模式" if force_audio else "默认视频模式"
        
        mode = "音频" if is_audio else "视频"
        print(f"  → 下载模式：{mode} ({mode_desc})")
        print(f"  → 提交到 MeTube...")
        
        if self.add_download(url, is_audio=is_audio):
            print("  ✓ 下载任务已提交")
            return True
        else:
            print("  ❌ 下载任务提交失败")
            return False


# ==================== 主处理函数 ====================
def process_link(text: str, mode: str = "video") -> bool:
    """智能处理链接"""
    link = extract_link(text)
    if not link:
        print("❌ 未找到有效链接")
        return False
    
    link_type = detect_link_type(text)
    if not link_type:
        print(f"❌ 不支持的链接类型：{link}")
        return False
    
    print(f"🔗 检测到 {link_type} 链接")
    
    if link_type == "quark":
        client = QuarkAutoSaveClient(QAS_ENDPOINT, QAS_TOKEN, QAS_SAVE_ROOT)
        return client.process_share(link)
    
    elif link_type in ["youtube", "bilibili"]:
        force_audio = (mode.lower() == "audio")
        client = MeTubeClient(METUBE_ENDPOINT)
        return client.process_video(link, force_audio=force_audio)
    
    else:
        print(f"❌ 未知链接类型：{link_type}")
        return False


# ==================== 命令行入口 ====================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python3 smart-link-handler-final.py <链接> [模式]")
        print("模式：video(默认) | audio")
        sys.exit(1)
    
    link_text = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "video"
    
    print("=" * 60)
    print("智能链接处理器（最终版）")
    print("=" * 60)
    
    success = process_link(link_text, mode)
    
    print("=" * 60)
    if success:
        print("✅ 处理完成：好了")
    else:
        print("❌ 处理失败：错")
    
    sys.exit(0 if success else 1)
