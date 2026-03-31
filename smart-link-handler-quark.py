#!/usr/bin/env python3
"""
夸克链接自动转存 - 根据 lzylipu/quark-autosave-bot 项目实现
API 端点根据实际项目代码：/data, /update, /run_script_now, /api/add_task, /get_share_detail
"""

import os
import re
import sys
import requests
from typing import Optional, Dict, Any

# ==================== 配置区域 ====================
# 根据 lzylipu/quark-autosave-bot 项目配置
QAS_ENDPOINT = os.environ.get("QAS_ENDPOINT", "http://YOUR_SERVER_IP:5015")
QAS_TOKEN = os.environ.get("QAS_TOKEN", "YOUR_QAS_TOKEN")
QAS_SAVE_ROOT = os.environ.get("QAS_SAVE_ROOT", "自动")

# ==================== 链接识别 ====================
def is_quark_link(text: str) -> bool:
    """判断是否是夸克分享链接"""
    return bool(re.search(r"pan\.quark\.cn/s/[a-zA-Z0-9]+", text))

def extract_quark_link(text: str) -> Optional[str]:
    """从文本中提取夸克链接"""
    match = re.search(r"https?://pan\.quark\.cn/s/[a-zA-Z0-9]+", text)
    return match.group(0) if match else None

# ==================== QAS API 客户端 ====================
class QuarkAutoSaveClient:
    """
    夸克自动转存客户端
    根据 lzylipu/quark-autosave-bot 项目实现
    API: /data, /update, /run_script_now, /api/add_task, /get_share_detail
    """
    
    def __init__(self, endpoint: str, token: str, save_root: str = "自动"):
        self.endpoint = endpoint.rstrip("/")
        self.token = token
        self.save_root = save_root
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
            print(f"❌ QAS 获取数据失败：{resp.status_code}")
            return None
        except Exception as e:
            print(f"❌ QAS 请求异常：{e}")
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
                    "taskname": "",
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
                    return data.get("data", {})
            
            print(f"❌ QAS 解析分享失败：{resp.status_code}")
            return None
        except Exception as e:
            print(f"❌ QAS 请求异常：{e}")
            return None
    
    def add_task(self, share_url: str, task_name: str) -> bool:
        """
        添加转存任务 - 确保 aria2 自动下载正确配置
        API: POST /api/add_task
        """
        try:
            save_path = f"/{self.save_root}/{task_name}"
            
            # 关键修复：显式设置 aria2 配置，覆盖默认值
            task = {
                "shareurl": share_url,
                "taskname": task_name,
                "savepath": save_path,
                "enddate": "",
                "week": [],
                "pattern": "",
                "replace": "",
                # 顶层 aria2 配置
                "aria2": {
                    "auto_download": True,
                    "pause": False,
                    "save_path": ""
                },
                # addition 字段中的 aria2 配置（双重保险）
                "addition": {
                    "aria2": {
                        "auto_download": True,
                        "pause": False,
                        "save_path": ""
                    }
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
                    print(f"  ✓ 任务添加成功，aria2 自动下载已启用")
                    return True
            
            print(f"❌ QAS 添加任务失败：{resp.status_code} - {resp.text}")
            return False
        except Exception as e:
            print(f"❌ QAS 请求异常：{e}")
            return False
    
    def run_script(self) -> bool:
        """
        执行转存脚本 - 给 aria2 足够的启动时间
        API: POST /run_script_now
        """
        try:
            # 先等待 2 秒，确保任务完全注册
            import time
            time.sleep(2)
            
            resp = self.session.post(
                f"{self.endpoint}/run_script_now",
                json={},
                timeout=600  # 延长超时时间
            )
            
            if resp.status_code == 200:
                # 检查响应中是否包含 aria2 下载信息
                if 'Aria2下载' in resp.text:
                    print("  ✓ aria2 自动下载已触发")
                return True
            return False
        except Exception as e:
            print(f"❌ QAS 执行异常：{e}")
            return False
    
    def delete_task(self, task_name: str) -> bool:
        """
        删除任务（通过任务名查找并删除）
        API: GET /data → POST /update (移除任务)
        """
        try:
            # 获取任务列表
            data_resp = self.session.get(f"{self.endpoint}/data", timeout=30)
            if data_resp.status_code != 200:
                return False
            
            data_json = data_resp.json()
            if not data_json.get("success"):
                return False
            
            tasklist = data_json.get("data", {}).get("tasklist", [])
            
            # 找到要删除的任务索引
            for i, task in enumerate(tasklist):
                if task.get("taskname") == task_name:
                    # 从列表中移除
                    tasklist.pop(i)
                    
                    # 更新任务列表
                    update_data = data_json.get("data", {})
                    update_data["tasklist"] = tasklist
                    
                    resp = self.session.post(
                        f"{self.endpoint}/update",
                        json=update_data,
                        timeout=30
                    )
                    return resp.status_code == 200 and resp.json().get("success", False)
            
            return False  # 没找到任务
        except Exception as e:
            print(f"❌ QAS 删除异常：{e}")
            return False
    
    def process_share(self, share_url: str) -> bool:
        """
        完整处理流程：解析 → 添加 → 执行 → 删除
        """
        print(f"📥 开始处理夸克分享：{share_url}")
        
        # 1. 获取分享详情（根目录名）
        print("  → 解析分享链接...")
        share_detail = self.get_share_detail(share_url)
        if not share_detail:
            return False
        
        folder_name = share_detail.get("folder_name", "夸克分享")
        print(f"  ✓ 分享目录：{folder_name}")
        
        # 2. 添加任务
        print("  → 添加转存任务...")
        if not self.add_task(share_url, folder_name):
            return False
        print("  ✓ 任务添加成功")
        
        # 3. 执行转存（关键：给 aria2 足够时间启动）
        print("  → 执行转存（等待 aria2 启动）...")
        if not self.run_script():
            return False
        print("  ✓ 转存执行完成")
        
        # 4. 等待 aria2 开始下载后再删除任务
        print("  → 等待 aria2 下载启动...")
        import time
        time.sleep(5)  # 给 aria2 足够时间开始下载
        
        # 5. 删除任务（清理临时记录）
        print("  → 删除任务记录...")
        if self.delete_task(folder_name):
            print("  ✓ 任务已删除")
        else:
            print("  ⚠️ 任务删除失败（不影响转存结果）")
        
        return True

# ==================== 主处理函数 ====================
def process_quark_link(text: str) -> bool:
    """处理夸克链接"""
    link = extract_quark_link(text)
    if not link:
        print("❌ 未找到有效夸克链接")
        return False
    
    print(f"🔗 检测到夸克链接")
    
    client = QuarkAutoSaveClient(QAS_ENDPOINT, QAS_TOKEN, QAS_SAVE_ROOT)
    return client.process_share(link)

# ==================== 命令行入口 ====================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python3 smart-link-handler-quark.py <夸克链接>")
        print("\n例子:")
        print("  python3 smart-link-handler-quark.py https://pan.quark.cn/s/xxx")
        sys.exit(1)
    
    link_text = sys.argv[1]
    
    print("=" * 60)
    print("夸克自动转存（根据 lzylipu/quark-autosave-bot 实现）")
    print("=" * 60)
    
    success = process_quark_link(link_text)
    
    print("=" * 60)
    if success:
        print("✅ 处理完成：好了")
    else:
        print("❌ 处理失败：错")
    
    sys.exit(0 if success else 1)