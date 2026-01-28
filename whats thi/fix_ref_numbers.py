import re

with open('post1 copy.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 使用正则表达式找到参考文献部分
pattern = r'(<div class="ref-title">参考文献 / REFERENCES</div>)(.*?)(</section>)'
match = re.search(pattern, content, re.DOTALL)

if not match:
    print("找不到参考文献部分")
    exit(1)

# 提取参考文献内容
ref_title = match.group(1)
ref_content = match.group(2)
ref_end = match.group(3)

# 将参考文献内容按行处理
lines = ref_content.split('\n')
new_lines = []
ref_num = 1
skip_blank = False

for i, line in enumerate(lines):
    stripped = line.strip()
    
    # 跳过完全空白的行
    if not stripped:
        if not skip_blank:
            new_lines.append('<br>')
            skip_blank = True
        continue
    
    skip_blank = False
    
    # 处理文献标题
    if '中文文献' in stripped or '外文文献' in stripped:
        new_lines.append(stripped)
        continue
    
    # 这是一条参考文献
    new_lines.append(f'[{ref_num}] {stripped}')
    ref_num += 1

# 重新组合
new_ref_content = '\n'.join(new_lines)
new_match = ref_title + '\n' + new_ref_content + '\n' + ref_end

new_content = content[:match.start()] + new_match + content[match.end():]

with open('post1 copy.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"✓ 已修复参考文献编号！")
