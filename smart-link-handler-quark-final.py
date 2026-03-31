#!/usr/bin/env python3
"""
夸克自动转存 - 完全根据 lzylipu/quark-autosave-bot 项目实现
完整流程：
1. 获取分享详情（根目录名）
2. 创建任务（带 aria2 自动下载配置）
3. 获取任务列表（获取任务索引）
4. 执行转存（通过索引）
5. 删除任务（通过索引）
"""

import os
import re
import sys
import requests
import time
from typing import Optional, Dict, Any

# ==================== 配置区域 ====================
QAS_ENDPOINT = os.environ.get("QAS_ENDPOINT", "http://YOUR_SERVER_IP:5015")
QAS_TOKEN = os.environ.get("QAS_TOKEN", "YOUR_QAS_TOKEN")
QAS_SAVE_ROOT = os.environ.get("QAS_SAVE_ROOT", "自动")

# ==================== 链接识别 ====================
def extract_quark_link(text: str) -> Optional[str]:
    """从文本中提取夸克链接"""
    match = re.search(r"https?://pan\.quark\.cn/s/[a-zA-Z0-9]+", text)
    return match.group(0) if match else None

# ==================== QAS API 客户端 ====================
class QuarkAutoSaveClient:
    """完全根据 lzylipu/quark-autosave-bot 项目实现"""
    
    def __init__(self, endpoint: str, token: str):
        self.endpoint = endpoint.rstrip("/")
        self.token = token
        self.session = requests.Session()
        self.session.params = {"token": token}
    
    def get_data(self) -> Optional[Dict[str, Any]]:
        """获取 QAS 数据（任务列表等）"""
        try:
            resp = self.session.get(f"{self.endpoint}/data", timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    return data.get("data", {})
            return None
        except Exception as e:
            print(f"❌ QAS 获取数据失败：{e}")
            return None
    
    def get_share_detail(self, share_url: str) -> Optional[Dict[str, Any]]:
        """
        获取分享链接详情（根目录名等）
        API: POST /get_share_detail
        """
        try:
            payload = {
                "shareurl": share_url,
                "task": {
                    "shareurl": share_url,
                    "taskname": "临时任务",
                    "savepath": "",
                    "enddate": "",
                    "week": [],
                    "pattern": "",
                    "replace": "",
                    "aria2": {}
                }
            }
            
            resp = self.session.post(
                f"{self.endpoint}/get_share_detail",
                json=payload,
                timeout=30
            )
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    share_data = data.get("data", {})
                    # 获取分享标题（根目录名）
                    title = share_data.get("share", {}).get("title", "夸克分享")
                    return {"title": title}
            return None
        except Exception as e:
            print(f"❌ QAS 解析分享失败：{e}")
            return None
    
    def add_task(self, share_url: str, task_name: str) -> bool:
        """
        添加转存任务（带 aria2 自动下载配置）
        API: POST /api/add_task
        注意：aria2 会在任务创建后自动开始下载，不需要额外触发
        """
        try:
            save_path = f"/{QAS_SAVE_ROOT}/{task_name}"
            task = {
                "shareurl": share_url,
                "taskname": task_name,
                "savepath": save_path,
                "enddate": "",
                "week": [],
                "pattern": "",
                "replace": "",
                "aria2": {
                    "auto_download": True,  # 启用 aria2 自动下载
                    "pause": False,         # 不暂停，立即开始
                    "save_path": ""         # 使用默认保存路径
                }
            }
            
            resp = self.session.post(
                f"{self.endpoint}/api/add_task",
                json=task,
                timeout=30
            )
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    print(f"  ✓ aria2 配置：auto_download=True, pause=False")
                    return True
            return False
        except Exception as e:
            print(f"❌ QAS 添加任务失败：{e}")
            return False
    
    def run_script(self, task_idx: int) -> bool:
        """
        执行转存脚本（通过任务索引）
        API: POST /run_script_now
        """
        try:
            # 获取任务列表
            data = self.get_data()
            if not data:
                return False
            
            tasklist = data.get("tasklist", [])
            if task_idx <= 0 or task_idx > len(tasklist):
                print(f"❌ 任务索引无效：{task_idx}")
                return False
            
            # 获取要执行的任务
            task_item = tasklist[task_idx - 1].copy()
            # 删除 runweek 字段（和原脚本一致）
            if "runweek" in task_item:
                del task_item["runweek"]
            
            payload = {"tasklist": [task_item]}
            
            resp = self.session.post(
                f"{self.endpoint}/run_script_now",
                json=payload,
                timeout=300
            )
            
            # 等待 aria2 开始下载
            if resp.status_code == 200:
                print("  → 等待 aria2 开始下载...")
                import time
                time.sleep(5)
            
            return resp.status_code == 200
        except Exception as e:
            print(f"❌ QAS 执行失败：{e}")
            return False
    
    def trigger_aria2(self, task_idx: int) -> bool:
        """
        触发 aria2 下载
        API: POST /api/aria2_add
        """
        try:
            data = self.get_data()
            if not data:
                return False
            
            tasklist = data.get("tasklist", [])
            if task_idx <= 0 or task_idx > len(tasklist):
                return False
            
            task_item = tasklist[task_idx - 1]
            
            # 调用 aria2 添加接口
            payload = {
                "task_idx": task_idx - 1,  # 0-based 索引
                "task": task_item
            }
            
            resp = self.session.post(
                f"{self.endpoint}/api/aria2_add",
                json=payload,
                timeout=30
            )
            
            if resp.status_code == 200:
                resp_data = resp.json()
                return resp_data.get("success", False)
            return False
        except Exception as e:
            print(f"❌ aria2 触发失败：{e}")
            return False
    
    def delete_task(self, task_idx: int) -> bool:
        """
        删除任务（通过任务索引）
        API: GET /data → POST /update
        """
        try:
            # 获取任务列表
            data = self.get_data()
            if not data:
                return False
            
            tasklist = data.get("tasklist", [])
            if task_idx <= 0 or task_idx > len(tasklist):
                print(f"❌ 任务索引无效：{task_idx}")
                return False
            
            # 从列表中移除任务
            tasklist.pop(task_idx - 1)
            
            # 更新任务列表
            data["tasklist"] = tasklist
            
            resp = self.session.post(
                f"{self.endpoint}/update",
                json=data,
                timeout=30
            )
            
            if resp.status_code == 200:
                resp_data = resp.json()
                return resp_data.get("success", False)
            return False
        except Exception as e:
            print(f"❌ QAS 删除失败：{e}")
            return False
    
    def process_share(self, share_url: str) -> bool:
        """
        完整处理流程（完全匹配原脚本）：
        1. 获取分享详情（根目录名）
        2. 添加任务（带 aria2 配置）
        3. 获取任务索引
        4. 执行转存
        5. 删除任务
        """
        print(f"📥 开始处理夸克分享：{share_url}")
        
        # 1. 获取分享详情（根目录名）
        print("  → 解析分享链接...")
        share_detail = self.get_share_detail(share_url)
        if not share_detail:
            return False
        
        folder_name = share_detail.get("title", "夸克分享")
        print(f"  ✓ 分享目录：{folder_name}")
        
        # 2. 添加任务（带 aria2 自动下载配置）
        print("  → 添加转存任务...")
        if not self.add_task(share_url, folder_name):
            return False
        print("  ✓ 任务添加成功")
        
        # 3. 获取任务索引（最后一个）
        data = self.get_data()
        if not data:
            return False
        task_idx = len(data.get("tasklist", []))
        print(f"  ✓ 任务索引：{task_idx}")
        
        # 4. 执行转存（aria2 会自动开始下载）
        print("  → 执行转存（aria2 自动下载已启用）...")
        if not self.run_script(task_idx):
            return False
        print("  ✓ 转存成功，aria2 开始下载")
        
        # 5. 立即删除任务（不影响 aria2 继续下载）
        print("  → 删除任务记录...")
        if not self.delete_task(task_idx):
            print("  ⚠️ 任务删除失败（不影响下载）")
        else:
            print("  ✓ 任务已删除（aria2 继续下载）")
        
        return True

# ==================== 主处理函数 ====================
def process_quark_link(text: str) -> bool:
    """处理夸克链接"""
    link = extract_quark_link(text)
    if not link:
        print("❌ 未找到有效夸克链接")
        return False
    
    print(f"🔗 检测到夸克链接")
    
    client = QuarkAutoSaveClient(QAS_ENDPOINT, QAS_TOKEN)
    return client.process_share(link)

# ==================== 命令行入口 ====================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python3 smart-link-handler-quark-final.py <夸克链接>")
        sys.exit(1)
    
    link_text = sys.argv[1]
    
    print("=" * 60)
    print("夸克自动转存（完全匹配 lzylipu/quark-autosave-bot）")
    print("=" * 60)
    
    success = process_quark_link(link_text)
    
    print("=" * 60)
    if success:
        print("✅ 处理完成：好了")
    else:
        print("❌ 处理失败：错")
    
    sys.exit(0 if success else 1)
