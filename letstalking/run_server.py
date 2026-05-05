#!/usr/bin/env python3
"""
本地HTTP服务器 - 用于解决FBX文件加载的CORS问题
运行方式: python run_server.py
然后在浏览器打开: http://localhost:8080
"""

import http.server
import socketserver
import os
import webbrowser
import sys

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        # 添加CORS头，允许本地文件访问
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def main():
    os.chdir(DIRECTORY)
    
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"\n🌐 本地服务器已启动")
        print(f"   地址: http://localhost:{PORT}")
        print(f"   目录: {DIRECTORY}")
        print(f"\n   按 Ctrl+C 停止服务器\n")
        
        # 自动打开浏览器
        webbrowser.open(f"http://localhost:{PORT}/index.html")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务器已停止")
            sys.exit(0)

if __name__ == "__main__":
    main()