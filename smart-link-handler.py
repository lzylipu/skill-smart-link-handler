#!/usr/bin/env python3
"""
智能链接处理 Skill - 自动识别并处理夸克/YouTube/B 站链接

功能：
- 夸克分享链接 → 调用 QAS API 自动转存
- YouTube/B 站链接 → 调用 MeTube API 自动下载
- 智能识别链接类型
- 支持视频/音频模式选择

用法：
    python3 smart-link-handler.py <链接> [模式]
    模式：video(默认) | audio
"""

import os
import re
import sys
import json
import requests
from typing import Optional, Dict, Any

# ==================== 配置区域 ====================
# 从环境变量读取，如果没有则使用默认值
QAS_ENDPOINT = os.environ.get("QAS_ENDPOINT", "http://YOUR_SERVER_IP:5015")
QAS_TOKEN = os.environ.get("QAS_TOKEN", "YOUR_QAS_TOKEN")
QAS_SAVE_ROOT = os.environ.get("QAS_SAVE_ROOT", "自动")

METUBE_ENDPOINT = os.environ.get("METUBE_ENDPOINT", "http://YOUR_SERVER_IP:8081")
METUBE_DEFAULT_QUALITY = "best"
METUBE_DEFAULT_FORMAT = "any"  # any=视频，mp3=音频

# ==================== 链接识别规则 ====================
LINK_PATTERNS = {
    "quark": [
        r"pan\.quark\.cn/s/[a-zA-Z0-9]+",
        r"pan\.quark\.cn/s/[a-zA-Z0-9]+/.*",
    ],
    "youtube": [
        r"(youtube\.com/watch\?v=|youtu\.be/)[a-zA-Z0-9_-]+",
        r"youtube\.com/shorts/[a-zA-Z0-9_-]+",
    ],
    "bilibili": [
        r"bilibili\.com/video/(BV[a-zA-Z0-9]+|av\d+)",
        r"b23\.tv/[a-zA-Z0-9]+",
    ],
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


# ==================== QAS 客户端 ====================
class QuarkAutoSaveClient:
    """夸克自动转存客户端"""
    
    def __init__(self, endpoint: str, token: str, save_root: str = "自动"):
        self.endpoint = endpoint.rstrip("/")
        self.token = token
        self.save_root = save_root
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        })
    
    def get_share_info(self, share_url: str) -> Optional[Dict[str, Any]]:
        """获取分享链接信息（目录名等）"""
        try:
            # QAS API: 解析分享链接
            resp = self.session.post(
                f"{self.endpoint}/api/parse",
                json={"url": share_url},
                timeout=30
            )
            if resp.status_code == 200:
                return resp.json()
            else:
                print(f"❌ QAS 解析失败：{resp.status_code} - {resp.text[:200]}")
                return None
        except Exception as e:
            print(f"❌ QAS 请求异常：{e}")
            return None
    
    def create_task(self, share_url: str, folder_name: str) -> Optional[int]:
        """创建转存任务"""
        try:
            task_name = folder_name  # 使用分享目录名作为任务名
            save_path = f"/{self.save_root}/{folder_name}"
            
            resp = self.session.post(
                f"{self.endpoint}/api/tasks",
                json={
                    "url": share_url,
                    "task_name": task_name,
                    "save_path": save_path
                },
                timeout=30
            )
            
            if resp.status_code == 200:
                result = resp.json()
                return result.get("task_id")
            else:
                print(f"❌ QAS 创建任务失败：{resp.status_code} - {resp.text[:200]}")
                return None
        except Exception as e:
            print(f"❌ QAS 请求异常：{e}")
            return None
    
    def execute_task(self, task_id: int) -> bool:
        """执行转存任务"""
        try:
            resp = self.session.post(
                f"{self.endpoint}/api/tasks/{task_id}/execute",
                timeout=30
            )
            return resp.status_code == 200
        except Exception as e:
            print(f"❌ QAS 执行异常：{e}")
            return False
    
    def delete_task(self, task_id: int) -> bool:
        """删除任务（清理临时记录）"""
        try:
            resp = self.session.delete(
                f"{self.endpoint}/api/tasks/{task_id}",
                timeout=30
            )
            return resp.status_code in [200, 204]
        except Exception as e:
            print(f"⚠️ QAS 删除异常：{e}")
            return False
    
    def process_share(self, share_url: str) -> bool:
        """完整处理流程：解析 → 创建 → 执行 → 删除"""
        print(f"📥 开始处理夸克分享：{share_url}")
        
        # 1. 解析分享链接，获取目录名
        print("  → 解析分享链接...")
        share_info = self.get_share_info(share_url)
        if not share_info:
            return False
        
        folder_name = share_info.get("folder_name", "未命名分享")
        print(f"  ✓ 分享目录：{folder_name}")
        
        # 2. 创建任务
        print("  → 创建转存任务...")
        task_id = self.create_task(share_url, folder_name)
        if not task_id:
            return False
        print(f"  ✓ 任务 ID: {task_id}")
        
        # 3. 执行任务
        print("  → 执行转存...")
        if not self.execute_task(task_id):
            return False
        print("  ✓ 转存成功")
        
        # 4. 清理任务记录
        print("  → 清理任务记录...")
        self.delete_task(task_id)
        
        return True


# ==================== MeTube 客户端 ====================
class MeTubeClient:
    """MeTube 下载客户端"""
    
    def __init__(self, endpoint: str):
        self.endpoint = endpoint.rstrip("/")
        self.session = requests.Session()
    
    def add_download(self, url: str, quality: str = "best", 
                     format: str = "any", is_audio: bool = False) -> bool:
        """添加下载任务"""
        try:
            # 根据是否为音频模式设置格式
            if is_audio:
                format = "mp3"
            
            params = {
                "url": url,
                "quality": quality,
                "format": format,
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
                print(f"❌ MeTube 添加失败：{resp.status_code} - {resp.text[:200]}")
                return False
        except Exception as e:
            print(f"❌ MeTube 请求异常：{e}")
            return False
    
    def process_video(self, url: str, is_audio: bool = False) -> bool:
        """处理视频下载"""
        link_type = detect_link_type(url)
        
        if link_type == "youtube":
            print(f"📺 识别为 YouTube 链接")
        elif link_type == "bilibili":
            print(f"📺 识别为 B 站链接")
        else:
            print(f"📺 识别为通用视频链接")
        
        mode = "音频" if is_audio else "视频"
        print(f"  → 下载模式：{mode}")
        print(f"  → 提交到 MeTube...")
        
        if self.add_download(url, is_audio=is_audio):
            print("  ✓ 下载任务已提交")
            return True
        else:
            print("  ❌ 下载任务提交失败")
            return False


# ==================== 主处理函数 ====================
def process_link(text: str, mode: str = "video") -> bool:
    """
    智能处理链接
    
    Args:
        text: 用户输入的文本（包含链接）
        mode: 模式 "video" 或 "audio"
    
    Returns:
        bool: 是否成功处理
    """
    # 提取链接
    link = extract_link(text)
    if not link:
        print("❌ 未找到有效链接")
        return False
    
    # 检测链接类型
    link_type = detect_link_type(text)
    if not link_type:
        print(f"❌ 不支持的链接类型：{link}")
        return False
    
    print(f"🔗 检测到 {link_type} 链接")
    
    # 根据链接类型调用不同处理器
    if link_type == "quark":
        client = QuarkAutoSaveClient(QAS_ENDPOINT, QAS_TOKEN, QAS_SAVE_ROOT)
        return client.process_share(link)
    
    elif link_type in ["youtube", "bilibili"]:
        is_audio = (mode.lower() == "audio")
        client = MeTubeClient(METUBE_ENDPOINT)
        return client.process_video(link, is_audio=is_audio)
    
    else:
        print(f"❌ 未知链接类型：{link_type}")
        return False


# ==================== 命令行入口 ====================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python3 smart-link-handler.py <链接> [模式]")
        print("模式：video(默认) | audio")
        print("\n例子:")
        print("  python3 smart-link-handler.py https://pan.quark.cn/s/xxx")
        print("  python3 smart-link-handler.py https://youtube.com/watch?v=xxx")
        print("  python3 smart-link-handler.py https://youtube.com/watch?v=xxx audio")
        sys.exit(1)
    
    link_text = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "video"
    
    print("=" * 60)
    print("智能链接处理器")
    print("=" * 60)
    
    success = process_link(link_text, mode)
    
    print("=" * 60)
    if success:
        print("✅ 处理完成：好了")
    else:
        print("❌ 处理失败：错")
    
    sys.exit(0 if success else 1)
