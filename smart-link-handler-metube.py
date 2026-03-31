#!/usr/bin/env python3
"""
MeTube 视频下载技能 - 支持 YouTube、Bilibili 等数千个网站
基于 yt-dlp 引擎，通过 MeTube API 提供服务
"""

import os
import re
import sys
import requests
from typing import Optional, Dict, Any

# ==================== 配置区域 ====================
METUBE_ENDPOINT = os.environ.get("METUBE_ENDPOINT", "http://YOUR_SERVER_IP:8081")
METUBE_DOWNLOAD_DIR = os.environ.get("METUBE_DOWNLOAD_DIR", "/downloads")

# ==================== 链接识别 ====================
def is_video_link(text: str) -> bool:
    """判断是否是支持的视频链接"""
    video_patterns = [
        r'youtube\.com/watch\?v=',
        r'youtu\.be/',
        r'bilibili\.com/video/',
        r'instagram\.com/',
        r'twitter\.com/.*/status/',
        r'x\.com/.*/status/',
        r'tiktok\.com/',
        r'facebook\.com/',
        r'reddit\.com/',
        r'vimeo\.com/',
        r'dailymotion\.com/'
    ]
    
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in video_patterns)

def extract_video_link(text: str) -> Optional[str]:
    """从文本中提取视频链接"""
    # 匹配各种视频网站链接
    url_pattern = r'https?://[^\s<>"]+'
    urls = re.findall(url_pattern, text)
    
    for url in urls:
        if is_video_link(url):
            return url
    
    return None

# ==================== MeTube API 客户端 ====================
class MeTubeClient:
    """
    MeTube 视频下载客户端
    支持 YouTube、Bilibili 等数千个网站
    """
    
    def __init__(self, endpoint: str, download_dir: str = "/downloads"):
        self.endpoint = endpoint.rstrip("/")
        self.download_dir = download_dir
        self.session = requests.Session()
    
    def get_supported_sites(self) -> list:
        """获取支持的网站列表"""
        try:
            resp = self.session.get(f"{self.endpoint}/api/sites", timeout=10)
            if resp.status_code == 200:
                return resp.json().get("sites", [])
        except Exception as e:
            print(f"❌ 获取支持网站失败: {e}")
        return []
    
    def add_download_task(self, url: str, quality: str = "best") -> bool:
        """
        添加下载任务
        支持的 quality 参数: best, worst, audio, 720p, 1080p 等
        """
        try:
            payload = {
                "url": url,
                "quality": quality,
                "format": "mp4",  # 默认 MP4 格式
                "folder": self.download_dir
            }
            
            resp = self.session.post(
                f"{self.endpoint}/api/download",
                json=payload,
                timeout=30
            )
            
            if resp.status_code == 200:
                result = resp.json()
                if result.get("success", False):
                    print(f"  ✓ 下载任务添加成功")
                    return True
            
            print(f"❌ MeTube 添加任务失败: {resp.status_code} - {resp.text}")
            return False
        except Exception as e:
            print(f"❌ MeTube 请求异常: {e}")
            return False
    
    def get_download_status(self) -> list:
        """获取当前下载状态"""
        try:
            resp = self.session.get(f"{self.endpoint}/api/status", timeout=10)
            if resp.status_code == 200:
                return resp.json().get("tasks", [])
        except Exception as e:
            print(f"❌ 获取下载状态失败: {e}")
        return []
    
    def process_video_link(self, url: str) -> bool:
        """处理视频链接下载"""
        print(f"📥 开始处理视频链接: {url}")
        
        # 检查链接是否支持
        supported_sites = self.get_supported_sites()
        if not supported_sites:
            print("  ⚠️ 无法获取支持的网站列表，但将继续尝试")
        
        # 添加下载任务
        print("  → 添加下载任务...")
        if self.add_download_task(url):
            print("  ✓ 视频下载已启动")
            return True
        else:
            print("  ❌ 视频下载失败")
            return False

# ==================== 主处理函数 ====================
def process_video_link(text: str) -> bool:
    """处理视频链接"""
    link = extract_video_link(text)
    if not link:
        print("❌ 未找到有效的视频链接")
        return False
    
    print(f"🔗 检测到视频链接: {link}")
    
    client = MeTubeClient(METUBE_ENDPOINT, METUBE_DOWNLOAD_DIR)
    return client.process_video_link(link)

# ==================== 命令行入口 ====================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python3 smart-link-handler-metube.py <视频链接>")
        print("\n支持的网站:")
        print("  - YouTube, Bilibili, Instagram, Twitter/X, TikTok")
        print("  - Facebook, Reddit, Vimeo, Dailymotion 等")
        print("\n例子:")
        print("  python3 smart-link-handler-metube.py https://www.youtube.com/watch?v=xxx")
        print("  python3 smart-link-handler-metube.py https://www.bilibili.com/video/BVxxx")
        sys.exit(1)
    
    link_text = sys.argv[1]
    
    print("=" * 60)
    print("MeTube 视频下载技能")
    print("=" * 60)
    
    success = process_video_link(link_text)
    
    print("=" * 60)
    if success:
        print("✅ 处理完成：视频下载已启动")
    else:
        print("❌ 处理失败：无法下载视频")
    
    sys.exit(0 if success else 1)