import re

with open('post1 copy.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 找到参考文献部分
ref_start = content.find('<div class="ref-title">参考文献 / REFERENCES</div>')
ref_end = content.find('</section>', ref_start)

if ref_start == -1 or ref_end == -1:
    print("找不到参考文献部分")
    exit(1)

# 提取参考文献内容
before_ref = content[:ref_start + len('<div class="ref-title">参考文献 / REFERENCES</div>')]
ref_content = content[ref_start + len('<div class="ref-title">参考文献 / REFERENCES</div>'):ref_end]
after_ref = content[ref_end:]

# 处理参考文献文本
lines = ref_content.split('\n')
new_lines = []
ref_num = 1
in_chinese = False
in_english = False

for line in lines:
    line = line.strip()
    
    if not line:
        new_lines.append('')
        continue
    
    if '中文文献' in line:
        new_lines.append(line)
        in_chinese = True
        in_english = False
        continue
    
    if '外文文献' in line:
        new_lines.append('<br>')
        new_lines.append(line)
        in_english = True
        in_chinese = False
        continue
    
    # 检查是否是参考文献条目
    # 中文文献通常以作者名开头，外文文献也是
    if line and not line.startswith('['):
        # 这是一条参考文献
        new_lines.append(f'[{ref_num}] {line}<br>')
        new_lines.append('<br>')
        ref_num += 1
    else:
        new_lines.append(line)

# 重新组合
new_ref_content = '\n'.join(new_lines)
new_content = before_ref + new_ref_content + after_ref

with open('post1 copy.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"✓ 已添加参考文献编号（共 {ref_num - 1} 条）和换行！")
