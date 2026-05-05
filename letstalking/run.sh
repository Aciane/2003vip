#!/bin/bash

# 启动本地服务器脚本
echo "正在启动本地服务器..."
echo "请在浏览器中访问: http://localhost:8080"
echo ""
echo "如果浏览器没有自动打开，请手动打开上述地址"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""

cd /Users/tangzezhen/letstalking
python3 -m http.server 8080