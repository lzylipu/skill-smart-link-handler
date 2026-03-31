#!/usr/bin/env python3
"""
统一智能链接处理器 - 自动识别并处理夸克网盘和视频网站链接
"""

import os
import sys
import subprocess

def is_quark_link(text: str) -> bool:
    """判断是否是夸克分享链接"""
    import re
    return bool(re.search(r"pan\.quark\.cn/s/[a-zA-Z0-9]+", text))

def is_video_link(text: str) -> bool:
    """判断是否是视频网站链接"""
    import re
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

def main():
    if len(sys.argv) < 2:
        print("用法：python3 smart-link-handler-unified.py <链接>")
        print("\n支持的链接类型:")
        print("  - 夸克网盘: https://pan.quark.cn/s/xxx")
        print("  - 视频网站: YouTube, Bilibili, Instagram, Twitter 等")
        sys.exit(1)
    
    link_text = sys.argv[1]
    
    print("=" * 60)
    print("统一智能链接处理器")
    print("=" * 60)
    
    if is_quark_link(link_text):
        print("🔗 检测到夸克网盘链接")
        # 调用夸克转存技能
        result = subprocess.run([
            "python3", 
            "/vol1/@apphome/trim.openclaw/data/workspace/skills/smart-link-handler/smart-link-handler-quark.py",
            link_text
        ])
        sys.exit(result.returncode)
    
    elif is_video_link(link_text):
        print("🔗 检测到视频网站链接")
        # 调用 MeTube 下载技能
        result = subprocess.run([
            "python3",
            "/vol1/@apphome/trim.openclaw/data/workspace/skills/smart-link-handler/smart-link-handler-metube.py", 
            link_text
        ])
        sys.exit(result.returncode)
    
    else:
        print("❌ 不支持的链接类型")
        print("支持: 夸克网盘、YouTube、Bilibili、Instagram、Twitter/X、TikTok 等")
        sys.exit(1)

if __name__ == "__main__":
    main()