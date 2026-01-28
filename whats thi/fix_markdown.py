import re

# 读取原始文件
with open('post1 copy.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 首先还原到原始状态（移除出错的标签）
content = content.replace('</h3>\n</h3>', '\n')
content = re.sub(r'</h[1-4]>\n</h[1-4]>', '\n', content)
content = re.sub(r'</h[1-4]>(?=\n        )', '\n', content)

# 寻找 <article class="article-body"> 和 </article>
article_match = re.search(r'<article class="article-body">(.*?)</article>', content, re.DOTALL)

if not article_match:
    print("找不到 article 标签")
    exit(1)

# 只处理 article 内的内容
article_text = article_match.group(1)
start_pos = article_match.start(1)
end_pos = article_match.end(1)

# 转换规则（必须按照长度从长到短处理）
def convert_markdown(text):
    # #### -> <h4>
    text = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
    # ### -> <h3>
    text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    # ## -> <h2>
    text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    # # -> <h1>
    text = re.sub(r'^# (.+)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    # **文本** -> <strong>文本</strong>
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # *文本* -> <em>文本</em> (避免匹配**)
    text = re.sub(r'(?<!\*)\*([^\*]+?)\*(?!\*)', r'<em>\1</em>', text)
    # `代码` -> <code>代码</code>
    text = re.sub(r'`([^`]+?)`', r'<code>\1</code>', text)
    return text

# 转换 article 内容
converted_article = convert_markdown(article_text)

# 重新组合
new_content = content[:start_pos] + converted_article + content[end_pos:]

# 写回
with open('post1 copy.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✓ Markdown 转换完成（已修复）！")
