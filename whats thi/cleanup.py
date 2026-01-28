import re

with open('post1 copy.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 移除不配对的闭合标签（HTML 标签之外的地方）
# 特别是在 CSS 和 HTML 标签之间的孤立 </h3> 等

# 1. 移除在 </head> 或其他非 article 区域的多余标签
content = content.replace('</head></h3>', '</head>')
content = content.replace('</h3>\n    </nav>', '\n    </nav>')
content = content.replace('</h3>\n        </header>', '\n        </header>')
content = content.replace('</h3>\n</h3>\n        <article', '\n        <article')
content = re.sub(r'</h[1-4]>\n\s*</h[1-4]>', '', content)

# 2. 检查不匹配的标签对（可选）
# 确保 <h4> 后面跟 </h4>，不是其他闭合标签
content = re.sub(r'<h4>([^<]+)</h3>', r'<h4>\1</h4>', content)
content = re.sub(r'<h3>([^<]+)</h3>([^<]*)</h3>', r'<h3>\1</h3>\2', content)

with open('post1 copy.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ 清理完成！")
