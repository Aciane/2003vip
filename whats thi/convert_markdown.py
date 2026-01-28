import re

# 读取文件
with open('post1 copy.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 寻找 <article> 标签内的内容
article_start = content.find('<article class="article-body">')
article_end = content.find('</article>', article_start)

if article_start == -1 or article_end == -1:
    print("未找到 article 标签")
    exit(1)

article_content = content[article_start:article_end]

# Markdown 到 HTML 的转换规则（顺序很重要）
# 先处理最长的匹配

# #### 四级标题 -> <h4>
article_content = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', article_content, flags=re.MULTILINE)

# ### 三级标题 -> <h3>
article_content = re.sub(r'^### (.+)$', r'<h3>\1</h3>', article_content, flags=re.MULTILINE)

# ## 二级标题 -> <h2>  
article_content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', article_content, flags=re.MULTILINE)

# # 一级标题 -> <h1>
article_content = re.sub(r'^# (.+)$', r'<h1>\1</h1>', article_content, flags=re.MULTILINE)

# **粗体** -> <strong>
article_content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', article_content)

# *斜体* 或 _斜体_ -> <em>
article_content = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<em>\1</em>', article_content)
article_content = re.sub(r'_([^_]+?)_', r'<em>\1</em>', article_content)

# `代码` -> <code>
article_content = re.sub(r'`([^`]+?)`', r'<code>\1</code>', article_content)

# 组合回去
new_content = content[:article_start] + article_content + content[article_end:]

# 写回文件
with open('post1 copy.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✓ Markdown 转换完成！")
