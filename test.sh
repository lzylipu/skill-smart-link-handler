#!/bin/bash
# Smart Link Handler 测试脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HANDLER="$SCRIPT_DIR/smart-link-handler.py"

echo "========================================"
echo "Smart Link Handler 测试"
echo "========================================"
echo ""

# 测试 1: 帮助信息
echo "测试 1: 帮助信息"
python3 "$HANDLER" 2>&1 | head -5
echo ""

# 测试 2: YouTube 链接（视频）
echo "测试 2: YouTube 链接（视频模式）"
python3 "$HANDLER" "https://youtube.com/watch?v=dQw4w9WgXcQ"
echo ""

# 测试 3: YouTube 链接（音频）
echo "测试 3: YouTube 链接（音频模式）"
python3 "$HANDLER" "https://youtube.com/watch?v=dQw4w9WgXcQ audio"
echo ""

# 测试 4: B 站链接
echo "测试 4: B 站链接"
python3 "$HANDLER" "https://b23.tv/abc123"
echo ""

# 测试 5: 夸克链接（需要有效链接）
echo "测试 5: 夸克链接（示例）"
python3 "$HANDLER" "https://pan.quark.cn/s/test123"
echo ""

# 测试 6: 无效链接
echo "测试 6: 无效链接"
python3 "$HANDLER" "not-a-valid-url"
echo ""

echo "========================================"
echo "测试完成"
echo "========================================"
