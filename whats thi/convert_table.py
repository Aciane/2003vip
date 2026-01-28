import re

with open('post1 copy.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找并转换 Markdown 表格
# 模式：| 内容 | 内容 | ... |
table_pattern = r'\| (.+?) \| (.+?) \| (.+?) \|(?=\s*(?:\||-|$|\n|<))'

def find_tables(text):
    """找出所有连续的表格行"""
    lines = text.split('\n')
    tables = []
    current_table = []
    
    for i, line in enumerate(lines):
        # 检查是否是表格行
        if re.match(r'^\s*\|', line):
            current_table.append((i, line))
        else:
            if current_table:
                tables.append(current_table)
                current_table = []
    
    if current_table:
        tables.append(current_table)
    
    return tables

# 查找所有表格
tables = find_tables(content)

# 从后向前替换（避免位置变动）
for table in reversed(tables):
    # 解析表头和分隔符
    if len(table) >= 2:
        header_line = table[0][1]
        
        # 检查第二行是否是分隔符
        if '---' in table[1][1]:
            # 这是标准 Markdown 表格
            header_cells = [cell.strip() for cell in header_line.split('|')[1:-1]]
            
            # 收集所有数据行
            data_rows = []
            for j in range(2, len(table)):
                if '---' not in table[j][1]:  # 跳过分隔符
                    row_cells = [cell.strip() for cell in table[j][1].split('|')[1:-1]]
                    data_rows.append(row_cells)
            
            # 构建 HTML 表格
            html_table = '<table border="1" cellpadding="10" cellspacing="0">\n<tr>'
            for header_cell in header_cells:
                html_table += f'<th>{header_cell}</th>'
            html_table += '</tr>\n'
            
            for row in data_rows:
                html_table += '<tr>'
                for cell in row:
                    html_table += f'<td>{cell}</td>'
                html_table += '</tr>\n'
            
            html_table += '</table>'
            
            # 替换原表格
            start_line_idx = table[0][0]
            end_line_idx = table[-1][0]
            
            lines = content.split('\n')
            lines[start_line_idx:end_line_idx+1] = [html_table]
            content = '\n'.join(lines)

with open('post1 copy.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ 表格转换完成！")
