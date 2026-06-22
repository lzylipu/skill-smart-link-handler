#!/usr/bin/env python3
"""
夸克转存下载器 v12.0

流程：
1. 收到夸克分享链接
2. QAS 全量转存
3. Alist 刷新文件列表
4. 按剧集编号匹配下载（E01, E02...），Alist 提取直链，aria2 下载
5. QAS 清空任务

使用:
    python3 quark-download.py <链接>           # 全量下载
    python3 quark-download.py <链接> E01 E05   # 下载第1、5集
    python3 quark-download.py <链接> E01-E10   # 下载第1到10集
    python3 quark-download.py --list           # 查看任务列表
    python3 quark-download.py --del 0          # 删除任务
    python3 quark-download.py --clear          # 清空任务
"""

import os
import sys
import re
import requests
import time
import json

# ==================== API 配置（环境变量）====================
# 所有 API 凭据通过环境变量传入，不要硬编码

QAS_ENDPOINT = os.environ.get("QAS_ENDPOINT")
QAS_TOKEN = os.environ.get("QAS_TOKEN")
QAS_SAVE_ROOT = os.environ.get("QAS_SAVE_ROOT", "自动")

ALIST_ENDPOINT = os.environ.get("ALIST_ENDPOINT")
ALIST_TOKEN = os.environ.get("ALIST_TOKEN")
ALIST_MOUNT_PATH = os.environ.get("ALIST_MOUNT_PATH", "/夸克网盘")

ARIA2_ENDPOINT = os.environ.get("ARIA2_ENDPOINT")
ARIA2_TOKEN = os.environ.get("ARIA2_TOKEN")


class QuarkDownloader:
    """夸克转存下载器"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        })
        self._config = None

    # ==================== QAS API ====================

    def qas_get_config(self) -> dict:
        """GET /data - 获取配置"""
        try:
            r = self.session.get(
                f"{QAS_ENDPOINT}/data",
                params={"token": QAS_TOKEN},
                timeout=10
            )
            data = r.json()
            if data.get("success"):
                self._config = data.get("data", {})
                return self._config
        except Exception as e:
            print(f"   ✗ 获取配置失败: {e}")
        return {}

    def qas_update_config(self, config: dict) -> bool:
        """POST /update - 更新配置"""
        try:
            r = self.session.post(
                f"{QAS_ENDPOINT}/update",
                params={"token": QAS_TOKEN},
                json=config,
                timeout=10
            )
            return r.json().get("success", False)
        except:
            return False

    def qas_list_tasks(self) -> list:
        """获取任务列表"""
        config = self.qas_get_config()
        return config.get("tasklist", [])

    def qas_del_task(self, index: int) -> bool:
        """删除指定任务"""
        config = self.qas_get_config()
        tasklist = config.get("tasklist", [])

        if 0 <= index < len(tasklist):
            task_name = tasklist[index].get("taskname", "未知")
            del tasklist[index]
            config["tasklist"] = tasklist
            if self.qas_update_config(config):
                print(f"   ✓ 已删除: {task_name}")
                return True
        else:
            print(f"   ✗ 索引越界: {index}")
        return False

    def qas_clear_tasks(self) -> bool:
        """清空所有任务"""
        config = self.qas_get_config()
        count = len(config.get("tasklist", []))
        config["tasklist"] = []
        if self.qas_update_config(config):
            print(f"   ✓ 已清空 {count} 个任务")
            return True
        return False

    def qas_parse(self, share_url: str) -> dict:
        """POST /get_share_detail - 解析分享"""
        try:
            r = self.session.post(
                f"{QAS_ENDPOINT}/get_share_detail",
                params={"token": QAS_TOKEN},
                json={"shareurl": share_url},
                timeout=30
            )
            data = r.json()
            if data.get("success"):
                share = data.get("data", {}).get("share", {})
                return {
                    "success": True,
                    "title": share.get("title", "未知"),
                    "file_num": share.get("file_num", 0),
                    "size": share.get("size", 0) / 1024 / 1024 / 1024
                }
            return {"success": False, "error": data.get("message", "未知错误")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def qas_add_task(self, share_url: str, task_name: str) -> bool:
        """POST /api/add_task - 添加转存任务"""
        try:
            r = self.session.post(
                f"{QAS_ENDPOINT}/api/add_task",
                params={"token": QAS_TOKEN},
                json={
                    "taskname": task_name,
                    "shareurl": share_url,
                    "savepath": f"/{QAS_SAVE_ROOT}/{task_name}"
                },
                timeout=30
            )
            return r.json().get("success", False)
        except:
            return False

    def qas_run_task(self, index: int = None) -> bool:
        """POST /run_script_now - 运行任务"""
        try:
            if index is None:
                r = self.session.post(
                    f"{QAS_ENDPOINT}/run_script_now",
                    params={"token": QAS_TOKEN},
                    headers={"Content-Type": "application/json"},
                    json={},
                    timeout=60
                )
            else:
                tasklist = self.qas_list_tasks()
                if 0 <= index < len(tasklist):
                    r = self.session.post(
                        f"{QAS_ENDPOINT}/run_script_now",
                        params={"token": QAS_TOKEN},
                        json={"tasklist": [tasklist[index]]},
                        timeout=60
                    )
                else:
                    return False
            return True
        except:
            return False

    # ==================== Alist API ====================

    def alist_wait_files(self, path: str, max_wait: int = 180) -> list:
        """等待文件出现在 Alist"""
        headers = {"Authorization": ALIST_TOKEN}

        for i in range(max_wait // 3):
            try:
                r = self.session.post(
                    f"{ALIST_ENDPOINT}/api/fs/list",
                    headers=headers,
                    json={"path": path, "page": 1, "per_page": 100},
                    timeout=10
                )
                data = r.json()
                if data.get("code") == 200:
                    items = data.get("data", {}).get("content", [])
                    if items:
                        return items
            except:
                pass
            time.sleep(3)
        return []

    def alist_list_recursive(self, path: str) -> list:
        """递归获取所有文件"""
        headers = {"Authorization": ALIST_TOKEN}
        all_files = []

        try:
            r = self.session.post(
                f"{ALIST_ENDPOINT}/api/fs/list",
                headers=headers,
                json={"path": path, "page": 1, "per_page": 100},
                timeout=30
            )
            data = r.json()
            if data.get("code") == 200:
                items = data.get("data", {}).get("content", [])
                for item in items:
                    if item.get("is_dir"):
                        sub = self.alist_list_recursive(f"{path}/{item['name']}")
                        all_files.extend(sub)
                    else:
                        all_files.append({
                            "name": item["name"],
                            "path": f"{path}/{item['name']}",
                            "size": item.get("size", 0)
                        })
        except:
            pass
        return all_files

    def alist_get_url(self, file_path: str) -> str:
        """获取下载直链"""
        headers = {"Authorization": ALIST_TOKEN}
        try:
            r = self.session.post(
                f"{ALIST_ENDPOINT}/api/fs/get",
                headers=headers,
                json={"path": file_path},
                timeout=30
            )
            data = r.json()
            if data.get("code") == 200:
                return data.get("data", {}).get("raw_url", "")
        except:
            pass
        return ""

    # ==================== aria2 RPC ====================

    def aria2_add(self, url: str, filename: str, folder: str) -> str:
        """添加下载任务"""
        try:
            r = self.session.post(
                ARIA2_ENDPOINT,
                json={
                    "jsonrpc": "2.0",
                    "method": "aria2.addUri",
                    "id": "1",
                    "params": [
                        f"token:{ARIA2_TOKEN}",
                        [url],
                        {"dir": f"/downloads/{folder}", "out": filename}
                    ]
                },
                timeout=30
            )
            return r.json().get("result", "")
        except:
            return ""

    def aria2_remove(self, gid: str) -> bool:
        """删除下载任务"""
        try:
            r = self.session.post(
                ARIA2_ENDPOINT,
                json={
                    "jsonrpc": "2.0",
                    "method": "aria2.remove",
                    "id": "1",
                    "params": [f"token:{ARIA2_TOKEN}", gid]
                },
                timeout=10
            )
            return True
        except:
            return False

    def aria2_status(self) -> dict:
        """获取状态"""
        try:
            r = self.session.post(
                ARIA2_ENDPOINT,
                json={
                    "jsonrpc": "2.0",
                    "method": "aria2.getGlobalStat",
                    "id": "1",
                    "params": [f"token:{ARIA2_TOKEN}"]
                },
                timeout=10
            )
            return r.json().get("result", {})
        except:
            return {}

    # ==================== 剧集匹配 ====================

    def parse_episodes(self, args: list) -> list:
        """解析剧集编号参数

        支持格式:
        - E01 E05 E10  -> ['E01', 'E05', 'E10']
        - E01-E10      -> ['E01', 'E02', ..., 'E10']
        - 1 5 10       -> ['E01', 'E05', 'E10']
        """
        episodes = []

        for arg in args:
            arg = arg.upper()

            if '-' in arg and arg.startswith('E'):
                match = re.match(r'E(\d+)-E(\d+)', arg)
                if match:
                    start, end = int(match.group(1)), int(match.group(2))
                    for i in range(start, end + 1):
                        episodes.append(f"E{i:02d}")
                continue

            if arg.startswith('E'):
                match = re.match(r'E(\d+)', arg)
                if match:
                    episodes.append(f"E{int(match.group(1)):02d}")
                continue

            if arg.isdigit():
                episodes.append(f"E{int(arg):02d}")

        return episodes

    def match_files_by_episodes(self, files: list, episodes: list) -> list:
        """按剧集编号匹配文件"""
        matched = []
        for ep in episodes:
            for f in files:
                name = f.get("name", "")
                if re.search(rf'\b{ep}\b', name, re.IGNORECASE):
                    matched.append((ep, f))
                    break
        return matched

    # ==================== 主流程 ====================

    def process(self, share_url: str, episodes: list = None) -> bool:
        """完整下载流程"""
        print("=" * 50)
        print("夸克转存下载 v12.0")
        print("=" * 50)

        print("\n[1/5] 解析分享链接")
        result = self.qas_parse(share_url)
        if not result.get("success"):
            print(f"   ✗ 解析失败: {result.get('error')}")
            return False

        task_name = result["title"]
        print(f"   ✓ {task_name} | {result['file_num']}个文件")

        print("\n[2/5] QAS 全量转存")
        if not self.qas_add_task(share_url, task_name):
            print("   ✗ 转存失败")
            return False
        print("   ✓ 已添加转存任务")

        print("\n[3/5] Alist 刷新文件列表")
        folder_path = f"{ALIST_MOUNT_PATH}/{QAS_SAVE_ROOT}/{task_name}"
        items = self.alist_wait_files(folder_path)
        if not items:
            print("   ✗ 等待超时")
            self.qas_run_task()
            print("   已触发 QAS 运行，等待文件...")
            items = self.alist_wait_files(folder_path, max_wait=120)
            if not items:
                print("   ✗ 文件仍未出现")
                return False

        if len(items) == 1 and items[0].get("is_dir"):
            folder_path = f"{folder_path}/{items[0]['name']}"
            files = self.alist_list_recursive(folder_path)
        else:
            files = items
        print(f"   ✓ 发现 {len(files)} 个文件")

        print("\n[4/5] 下载")
        if episodes:
            print(f"   指定剧集: {episodes}")
            matched = self.match_files_by_episodes(files, episodes)
            if not matched:
                print("   ✗ 未匹配到指定剧集")
                print("\n   可用文件:")
                for i, f in enumerate(files[:15], 1):
                    print(f"     {i}. {f.get('name', '')[:45]}")
                return False

            added = 0
            for ep, f in matched:
                name = f.get("name", "")
                path = f.get("path", "")
                size = f.get("size", 0) / 1024 / 1024 / 1024
                print(f"   -> {ep}: {name[:40]} | {size:.2f}GB")
                url = self.alist_get_url(path)
                if url:
                    gid = self.aria2_add(url, name, task_name)
                    if gid:
                        print("     ✓ 已添加")
                        added += 1
                    else:
                        print("     ✗ aria2 失败")
                else:
                    print("     ✗ 无直链")
            print(f"\n   ✓ 已添加 {added}/{len(matched)} 个")
        else:
            print("   模式: 全量下载（QAS自动）")
            self.qas_run_task()
            print("   ✓ 已触发 QAS 自动下载")

        print("\n[5/5] 清空 QAS 任务")
        tasklist = self.qas_list_tasks()
        for i, task in enumerate(tasklist):
            if task.get("taskname") == task_name:
                self.qas_del_task(i)
                break

        stat = self.aria2_status()
        if stat:
            speed = int(stat.get("downloadSpeed", 0)) / 1024 / 1024
            print(f"\n📊 aria2: 活跃 {stat.get('numActive')} | 等待 {stat.get('numWaiting')} | {speed:.1f}MB/s")

        print("\n" + "=" * 50)
        print("✅ 完成")
        print("=" * 50)
        return True


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    dl = QuarkDownloader()

    if sys.argv[1] == "--list":
        print("📋 QAS 任务列表:")
        tasks = dl.qas_list_tasks()
        if not tasks:
            print("   无任务")
        for i, task in enumerate(tasks):
            print(f"   [{i}] {task.get('taskname', '未知')}")
        sys.exit(0)

    if sys.argv[1] == "--del" and len(sys.argv) > 2:
        dl.qas_del_task(int(sys.argv[2]))
        sys.exit(0)

    if sys.argv[1] == "--clear":
        dl.qas_clear_tasks()
        sys.exit(0)

    share_url = sys.argv[1]
    episodes = None
    if len(sys.argv) > 2:
        episodes = dl.parse_episodes(sys.argv[2:])

    dl.process(share_url, episodes)


if __name__ == "__main__":
    main()