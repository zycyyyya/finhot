#!/usr/bin/env bash
# finhot 一行安装脚本
# 用法: curl -fsSL https://raw.githubusercontent.com/zycyyyya/finhot/main/install.sh | bash

set -e

# 检测 Skill 目录
SKILL_DIR=""

# 优先检测 WorkBuddy
if [ -d "$HOME/.workbuddy/skills" ]; then
    SKILL_DIR="$HOME/.workbuddy/skills/finhot"
# Claude Code
elif [ -d "$HOME/.claude/skills" ]; then
    SKILL_DIR="$HOME/.claude/skills/finhot"
# Codex CLI
elif [ -d "$HOME/.codex/skills" ]; then
    SKILL_DIR="$HOME/.codex/skills/finhot"
# 通用回退
else
    SKILL_DIR="$HOME/.skills/finhot"
fi

echo "=== finhot 安装 ==="
echo "目标目录: $SKILL_DIR"

# 克隆仓库
if [ -d "$SKILL_DIR" ]; then
    echo "检测到已有安装，更新中..."
    cd "$SKILL_DIR" && git pull --ff-only || { echo "更新失败，尝试重新克隆"; rm -rf "$SKILL_DIR"; }
fi

if [ ! -d "$SKILL_DIR" ]; then
    echo "克隆仓库..."
    git clone https://github.com/zycyyyya/finhot.git "$SKILL_DIR"
fi

# 检查 Python 依赖
echo ""
echo "检查依赖..."

if command -v python3 &>/dev/null; then
    if python3 -c "import feedparser" 2>/dev/null; then
        echo "✅ feedparser 已安装"
    else
        echo "⚠️  feedparser 未安装（脚本模式需要）"
        echo "   安装命令: pip install feedparser"
    fi
else
    echo "⚠️  Python3 未安装（脚本模式需要）"
fi

echo ""
echo "✅ finhot 安装完成！"
echo ""
echo "使用方法："
echo "  在对话中说「今天金融圈有什么」「金融日报」「银保监会最近发了什么」"
echo "  Skill 会自动触发并聚合多个数据源输出中文简报"
echo ""
echo "脚本模式（可选）："
echo "  cd $SKILL_DIR"
echo "  pip install feedparser"
echo "  python scripts/rss_fetcher.py --output ./data --days 1"
echo "  python scripts/daily_generator.py --input ./data --output ./daily --markdown"
