#!/usr/bin/env python3
"""
QAS 任务管理器 - 读取任务、应用规则、自动下载
功能：
1. 读取所有任务内容
2. 根据规则过滤（关键词、大小、类型等）
3. 自动添加 aria2 下载配置
4. 批量执行/删除任务
"""

import os
import sys
import requests
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

# ==================== 配置区域 ====================
QAS_ENDPOINT = os.environ.get("QAS_ENDPOINT", "http://YOUR_SERVER_IP:5015")
QAS_TOKEN = os.environ.get("QAS_TOKEN", "YOUR_QAS_TOKEN")
QAS_SAVE_ROOT = os.environ.get("QAS_SAVE_ROOT", "自动")

# ==================== 规则配置 ====================
class TaskRules:
    """任务规则配置"""
    
    # 关键词过滤
    INCLUDE_KEYWORDS = []  # 包含这些关键词（空=全部）
    EXCLUDE_KEYWORDS = ["广告", "推广", "赞助"]  # 排除这些关键词
    
    # 文件大小过滤（字节）
    MIN_FILE_SIZE = 0  # 最小文件大小
    MAX_FILE_SIZE = float('inf')  # 最大文件大小
    
    # 自动下载配置
    AUTO_DOWNLOAD = True  # 自动启用 aria2 下载
    PAUSE = False  # 不暂停
    
    # 保存路径规则
    SAVE_PATH_TEMPLATE = "/{root}/{taskname}"  # 保存路径模板
    
    @classmethod
    def should_process(cls, task: Dict[str, Any]) -> bool:
        """判断任务是否应该处理"""
        taskname = task.get("taskname", "")
        
        # 检查排除关键词
        for keyword in cls.EXCLUDE_KEYWORDS:
            if keyword in taskname:
                print(f"  ⚠️ 排除关键词：{keyword}")
                return False
        
        # 检查包含关键词
        if cls.INCLUDE_KEYWORDS:
            match = False
            for keyword in cls.INCLUDE_KEYWORDS:
                if keyword in taskname:
                    match = True
                    break
            if not match:
                print(f"  ⚠️ 不包含任何关键词")
                return False
        
        return True

# ==================== QAS 客户端 ====================
class QASManager:
    """QAS 任务管理器"""
    
    def __init__(self, endpoint: str, token: str):
        self.endpoint = endpoint.rstrip("/")
        self.token = token
        self.session = requests.Session()
        self.session.params = {"token": token}
    
    def get_data(self) -> Optional[Dict[str, Any]]:
        """获取完整数据"""
        try:
            resp = self.session.get(f"{self.endpoint}/data", timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    return data.get("data", {})
            return None
        except Exception as e:
            print(f"❌ 获取数据失败：{e}")
            return None
    
    def list_tasks(self) -> List[Dict[str, Any]]:
        """获取任务列表"""
        data = self.get_data()
        if data:
            return data.get("tasklist", [])
        return []
    
    def print_tasks(self, tasks: List[Dict[str, Any]]):
        """打印任务列表"""
        print(f"\n{'='*60}")
        print(f"当前任务数：{len(tasks)}")
        print(f"{'='*60}\n")
        
        for i, task in enumerate(tasks, 1):
            print(f"[{i}] {task.get('taskname', '未知')}")
            print(f"    链接：{task.get('shareurl', 'N/A')[:60]}...")
            print(f"    保存路径：{task.get('savepath', 'N/A')}")
            
            # 显示 aria2 配置
            aria2_config = task.get("aria2", {})
            if aria2_config:
                auto_dl = aria2_config.get("auto_download", False)
                print(f"    自动下载：{'✅' if auto_dl else '❌'}")
            
            print()
    
    def apply_rules(self, tasks: List[Dict[str, Any]]) -> List[int]:
        """应用规则，返回符合条件的任务索引"""
        matched_indices = []
        
        for i, task in enumerate(tasks, 1):
            print(f"[{i}/{len(tasks)}] 检查：{task.get('taskname', '未知')[:50]}")
            
            if TaskRules.should_process(task):
                matched_indices.append(i)
                print(f"  ✓ 符合规则")
            else:
                print(f"  ❌ 不符合规则")
        
        return matched_indices
    
    def update_task_aria2(self, task_idx: int, auto_download: bool = True, pause: bool = False) -> bool:
        """更新任务的 aria2 配置"""
        try:
            data = self.get_data()
            if not data:
                return False
            
            tasklist = data.get("tasklist", [])
            if task_idx <= 0 or task_idx > len(tasklist):
                return False
            
            # 更新 aria2 配置
            task = tasklist[task_idx - 1]
            if "aria2" not in task:
                task["aria2"] = {}
            
            task["aria2"]["auto_download"] = auto_download
            task["aria2"]["pause"] = pause
            task["aria2"]["save_path"] = ""
            
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
            print(f"❌ 更新任务失败：{e}")
            return False
    
    def run_script(self, task_idx: int) -> bool:
        """执行单个任务"""
        try:
            data = self.get_data()
            if not data:
                return False
            
            tasklist = data.get("tasklist", [])
            if task_idx <= 0 or task_idx > len(tasklist):
                return False
            
            task_item = tasklist[task_idx - 1].copy()
            if "runweek" in task_item:
                del task_item["runweek"]
            
            payload = {"tasklist": [task_item]}
            
            resp = self.session.post(
                f"{self.endpoint}/run_script_now",
                json=payload,
                timeout=300
            )
            
            return resp.status_code == 200
        except Exception as e:
            print(f"❌ 执行失败：{e}")
            return False
    
    def delete_task(self, task_idx: int) -> bool:
        """删除任务"""
        try:
            data = self.get_data()
            if not data:
                return False
            
            tasklist = data.get("tasklist", [])
            if task_idx <= 0 or task_idx > len(tasklist):
                return False
            
            tasklist.pop(task_idx - 1)
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
            print(f"❌ 删除失败：{e}")
            return False
    
    def process_all_tasks(self, auto_execute: bool = True, auto_delete: bool = False):
        """
        处理所有任务：
        1. 读取任务
        2. 应用规则
        3. 更新 aria2 配置
        4. 执行下载
        5. 删除任务（可选）
        """
        print("=" * 60)
        print("QAS 任务管理器")
        print("=" * 60)
        print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"API: {self.endpoint}")
        print("")
        
        # 1. 读取任务
        print("📖 读取任务列表...")
        tasks = self.list_tasks()
        self.print_tasks(tasks)
        
        if not tasks:
            print("✅ 没有任务需要处理")
            return
        
        # 2. 应用规则
        print("\n🔍 应用规则过滤...")
        matched_indices = self.apply_rules(tasks)
        
        if not matched_indices:
            print("\n⚠️ 没有符合规则的任务")
            return
        
        print(f"\n✅ 符合规则的任务：{len(matched_indices)}/{len(tasks)}")
        
        # 3. 批量处理
        success_count = 0
        failed_count = 0
        
        for task_idx in matched_indices:
            task_name = tasks[task_idx - 1].get("taskname", "未知")
            print(f"\n[{success_count + 1}/{len(matched_indices)}] 处理：{task_name[:50]}")
            
            # 更新 aria2 配置
            print("  → 更新 aria2 配置...")
            if self.update_task_aria2(task_idx, TaskRules.AUTO_DOWNLOAD, TaskRules.PAUSE):
                print("  ✓ 配置更新成功")
            else:
                print("  ❌ 配置更新失败")
            
            # 执行下载
            if auto_execute:
                print("  → 执行下载...")
                if self.run_script(task_idx):
                    print("  ✓ 下载执行成功")
                    success_count += 1
                else:
                    print("  ❌ 下载执行失败")
                    failed_count += 1
            
            # 删除任务
            if auto_delete:
                print("  → 删除任务...")
                if self.delete_task(task_idx):
                    print("  ✓ 任务已删除")
                else:
                    print("  ⚠️ 任务删除失败")
            
            # 等待一下
            time.sleep(2)
        
        # 4. 输出统计
        print("\n" + "=" * 60)
        print("处理完成！")
        print(f"成功：{success_count}")
        print(f"失败：{failed_count}")
        print("=" * 60)

# ==================== 命令行入口 ====================
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="QAS 任务管理器")
    parser.add_argument("--no-execute", action="store_true", help="只查看，不执行下载")
    parser.add_argument("--delete", action="store_true", help="执行后删除任务")
    parser.add_argument("--list", action="store_true", help="只列出任务")
    
    args = parser.parse_args()
    
    manager = QASManager(QAS_ENDPOINT, QAS_TOKEN)
    
    if args.list:
        tasks = manager.list_tasks()
        manager.print_tasks(tasks)
    else:
        manager.process_all_tasks(
            auto_execute=not args.no_execute,
            auto_delete=args.delete
        )
