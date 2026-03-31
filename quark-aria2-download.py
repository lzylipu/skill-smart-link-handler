#!/usr/bin/env python3
"""
从夸克网盘下载文件到本地（通过 aria2）
前提：文件已经在夸克网盘中
"""

import os
import sys
import requests
import time

# aria2 配置
ARIA2_ENDPOINT = os.environ.get("ARIA2_ENDPOINT", "http://YOUR_SERVER_IP:6802/jsonrpc")
ARIA2_SECRET = os.environ.get("ARIA2_SECRET", "dai123123")
ARIA2_DIR = os.environ.get("ARIA2_DIR", "/downloads")

def aria2_add_uri(uri, dir=None):
    """通过 aria2 添加下载任务"""
    payload = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "aria2.addUri",
        "params": [
            f"token:{ARIA2_SECRET}",
            [uri],
            {
                "dir": dir or ARIA2_DIR
            }
        ]
    }
    
    try:
        resp = requests.post(ARIA2_ENDPOINT, json=payload, timeout=30)
        if resp.status_code == 200:
            result = resp.json()
            if "result" in result:
                return result["result"]
        return None
    except Exception as e:
        print(f"❌ aria2 添加失败：{e}")
        return None

def aria2_tell_active():
    """获取正在下载的任务"""
    payload = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "aria2.tellActive",
        "params": [f"token:{ARIA2_SECRET}"]
    }
    
    try:
        resp = requests.post(ARIA2_ENDPOINT, json=payload, timeout=30)
        if resp.status_code == 200:
            result = resp.json()
            return result.get("result", [])
        return []
    except Exception as e:
        print(f"❌ 获取下载状态失败：{e}")
        return []

def main():
    print("=" * 60)
    print("夸克网盘 → 本地下载（aria2）")
    print("=" * 60)
    
    # 示例：从夸克分享链接下载
    # 注意：这需要夸克的下载链接，通常需要 cookie 认证
    
    print("\n说明：")
    print("1. 此脚本用于从夸克网盘下载已转存的文件到本地")
    print("2. 需要夸克 cookie 认证")
    print("3. 或者使用 QAS Web UI 的自动下载功能")
    print("\n建议在 QAS Web UI 中配置：")
    print("  http://YOUR_SERVER_IP:5015")
    print("  设置 → 转存后自动下载 → 启用")
    print("=" * 60)

if __name__ == "__main__":
    main()
