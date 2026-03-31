#!/usr/bin/env python3
"""
智能链接处理 Skill - 修正版（匹配真实 API）

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


# ==================== QAS 客户端（修正版）====================
class QuarkAutoSaveClient:
    """夸克自动转存客户端 - 匹配真实 QAS API"""
    
    def __init__(self, endpoint: str, token: str, save_root: str = "自动"):
        self.endpoint = endpoint.rstrip("/")
        self.token = token
        self.save_root = save_root
        self.session = requests.Session()
        self.session.params = {"token": token}
    
    def get_data(self) -> Optional[Dict[str, Any]]:
        """获取 QAS 完整数据（包含 tasklist）"""
        try:
            resp = self.session.get(f"{self.endpoint}/", timeout=30)
            if resp.status_code == 200:
                return resp.json()
            else:
                print(f"❌ QAS 获取数据失败：{resp.status_code}")
                return None
        except Exception as e:
            print(f"❌ QAS 请求异常：{e}")
            return None
    
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
    
    def add_task_to_data(self, data: Dict[str, Any], task_item: Dict[str, Any]) -> bool:
        """添加任务到数据并更新"""
        try:
            data["tasklist"].append(task_item)
            resp = self.session.post(
                f"{self.endpoint}/update",
                json=data,
                timeout=30
            )
            return resp.status_code == 200
        except Exception as e:
            print(f"❌ QAS 添加任务失败：{e}")
            return False
    
    def run_script_for_task(self, task_index: int) -> bool:
        """执行特定任务的转存脚本"""
        try:
            # 获取最新数据以确保索引正确
            data = self.get_data()
            if not data or task_index >= len(data["tasklist"]):
                print(f"❌ 任务索引无效：{task_index}")
                return False
            
            # 构建 payload，只包含要执行的任务
            task_payload = data["tasklist"][task_index]
            # 移除不需要的字段
            if "runweek" in task_payload:
                del task_payload["runweek"]
            
            payload = {"tasklist": [task_payload]}
            
            resp = self.session.post(
                f"{self.endpoint}/run_script_now",
                json=payload,
                timeout=300  # 转存可能需要较长时间
            )
            return resp.status_code == 200
        except Exception as e:
            print(f"❌ QAS 执行脚本失败：{e}")
            return False
    
    def delete_task_from_data(self, data: Dict[str, Any], task_index: int) -> bool:
        """从数据中删除任务并更新"""
        try:
            if 0 <= task_index < len(data["tasklist"]):
                data["tasklist"].pop(task_index)
                resp = self.session.post(
                    f"{self.endpoint}/update",
                    json=data,
                    timeout=30
                )
                return resp.status_code == 200
            else:
                print(f"❌ 任务索引超出范围：{task_index}")
                return False
        except Exception as e:
            print(f"❌ QAS 删除任务失败：{e}")
            return False
    
    def process_share(self, share_url: str) -> bool:
        """完整处理流程：获取数据 → 添加任务 → 执行 → 删除任务"""
        print(f"📥 开始处理夸克分享：{share_url}")
        
        # 1. 获取当前 QAS 数据
        print("  → 获取 QAS 数据...")
        data = self.get_data()
        if not data:
            return False
        
        # 2. 创建任务项（这里简化，实际应该解析分享获取标题）
        # 注意：真实情况下需要先解析分享链接获取标题
        # 但 QAS 的 / 接口不提供解析功能，所以这里用默认标题
        folder_name = "夸克分享"
        task_item = self.create_task_item(folder_name, share_url)
        print(f"  ✓ 任务标题：{folder_name}")
        
        # 3. 添加任务到 QAS
        print("  → 添加转存任务...")
        if not self.add_task_to_data(data, task_item):
            return False
        task_index = len(data["tasklist"]) - 1
        print(f"  ✓ 任务索引：{task_index}")
        
        # 4. 执行转存脚本
        print("  → 执行转存...")
        if not self.run_script_for_task(task_index):
            return False
        print("  ✓ 转存执行成功")
        
        # 5. 重新获取数据（因为执行后可能有变化）
        data = self.get_data()
        if not data:
            print("⚠️ 无法获取执行后的数据，跳过清理")
            return True
        
        # 6. 清理任务记录
        print("  → 清理任务记录...")
        self.delete_task_from_data(data, task_index)
        
        return True


# ==================== MeTube 客户端（保持不变）====================
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
        print("用法：python3 smart-link-handler-corrected.py <链接> [模式]")
        print("模式：video(默认) | audio")
        print("\n例子:")
        print("  python3 smart-link-handler-corrected.py https://pan.quark.cn/s/xxx")
        print("  python3 smart-link-handler-corrected.py https://youtube.com/watch?v=xxx")
        print("  python3 smart-link-handler-corrected.py https://youtube.com/watch?v=xxx audio")
        sys.exit(1)
    
    link_text = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "video"
    
    print("=" * 60)
    print("智能链接处理器（修正版）")
    print("=" * 60)
    
    success = process_link(link_text, mode)
    
    print("=" * 60)
    if success:
        print("✅ 处理完成：好了")
    else:
        print("❌ 处理失败：错")
    
    sys.exit(0 if success else 1)
