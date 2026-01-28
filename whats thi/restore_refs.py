import re

# 读取两个文件
with open('post1.html', 'r', encoding='utf-8') as f:
    original = f.read()

with open('post1 copy.html', 'r', encoding='utf-8') as f:
    copy = f.read()

# 从原始文件中提取参考文献部分
ref_match_original = re.search(
    r'<div class="ref-title">参考文献 / REFERENCES</div>(.*?)</section>',
    original,
    re.DOTALL
)

# 在 copy 中找到参考文献部分
ref_match_copy = re.search(
    r'(<div class="ref-title">参考文献 / REFERENCES</div>)(.*?)(</section>)',
    copy,
    re.DOTALL
)

if ref_match_original and ref_match_copy:
    # 替换 copy 中的参考文献部分
    original_ref_content = ref_match_original.group(1)
    new_copy = copy[:ref_match_copy.start(1) + len('<div class="ref-title">参考文献 / REFERENCES</div>')] + \
              original_ref_content + \
              copy[ref_match_copy.start(3):]
    
    with open('post1 copy.html', 'w', encoding='utf-8') as f:
        f.write(new_copy)
    
    print("✓ 已从原始文件恢复参考文献！")
else:
    print("找不到参考文献部分")
