#!/usr/bin/env python3
"""
╔══════════════════════════════════════╗
║  ★ BLOG FORGE ★                     ║
║  MD → HTML  /  Stardew Pixel Art     ║
╚══════════════════════════════════════╝
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import re
import os
import html as htmllib
import tempfile
import webbrowser
import subprocess
import threading
from datetime import datetime

REPO_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

# ── Stardew Valley palette ───────────────────────────────────────────────────
BG      = "#1c1208"
PANEL   = "#2a1b0e"
RAISED  = "#3d2814"
BORDER  = "#7a5530"
GOLD    = "#e8c56a"
RED     = "#c44030"
GREEN   = "#4aa840"
TEAL    = "#48b898"
TEXT    = "#f0ddb0"
DIM     = "#8a6a40"
INPUT   = "#160e06"
DROP_BG = "#211508"
DROP_HL = "#3d2e08"

F_XL = ("Courier", 15, "bold")
F_LG = ("Courier", 11, "bold")
F_MD = ("Courier", 10, "bold")
F_SM = ("Courier",  9, "bold")
F_XS = ("Courier",  8)
F_BD = ("Courier",  9)


# ── Obsidian inline syntax ───────────────────────────────────────────────────

def _embed_html(ref):
    if re.search(r'\.(png|jpg|jpeg|gif|svg|webp|bmp)$', ref, re.I):
        return f'<img src="{htmllib.escape(ref)}" alt="{htmllib.escape(ref)}" class="obs-img">'
    return f'<span class="obs-embed">![[{htmllib.escape(ref)}]]</span>'


def inline_md(text):
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
    text = re.sub(r'\*\*(.+?)\*\*',     r'<strong>\1</strong>', text)
    text = re.sub(r'__(.+?)__',         r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*',         r'<em>\1</em>', text)
    text = re.sub(r'_([^_]+)_',         r'<em>\1</em>', text)
    text = re.sub(r'==(.+?)==',         r'<mark>\1</mark>', text)
    text = re.sub(r'~~(.+?)~~',         r'<del>\1</del>', text)
    text = re.sub(r'`([^`]+)`',         r'<code class="ic">\1</code>', text)
    text = re.sub(r'!\[\[([^\]]+)\]\]', lambda m: _embed_html(m.group(1)), text)
    text = re.sub(r'\[\[([^|\]]+)\|([^\]]+)\]\]',
                  r'<span class="wl">\2</span>', text)
    text = re.sub(r'\[\[([^\]]+)\]\]',
                  r'<span class="wl">\1</span>', text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    text = re.sub(r'(?<![&\w])#([\w/-]+)', r'<span class="tag">#\1</span>', text)
    return text


# ── Block parsers ─────────────────────────────────────────────────────────────

def _parse_table(lines):
    headers, rows = [], []
    for i, line in enumerate(lines):
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if i == 0:
            headers = [inline_md(c) for c in cells]
        elif i == 1:
            continue  # separator row ---
        else:
            rows.append([inline_md(c) for c in cells])
    return {'type': 'table', 'headers': headers, 'rows': rows}


def _parse_list_block(lines):
    ordered = bool(re.match(r'^\s*\d+\.', lines[0]))
    items = []
    for line in lines:
        line = line.strip()
        m = re.match(r'^(?:[-*+]|\d+\.)\s+\[([ xX])\]\s+(.*)', line)
        if m:
            items.append({'task': True, 'done': m.group(1).lower() == 'x',
                          'text': inline_md(m.group(2))})
        else:
            text = re.sub(r'^(?:[-*+]|\d+\.)\s+', '', line)
            items.append({'task': False, 'text': inline_md(text)})
    return {'type': 'list', 'ordered': ordered, 'items': items}


# ── Obsidian callout color map ────────────────────────────────────────────────

_CALLOUT = {
    'NOTE':      ('#2196f3', '#e3f2fd'),
    'INFO':      ('#2196f3', '#e3f2fd'),
    'TIP':       ('#4caf50', '#e8f5e9'),
    'HINT':      ('#4caf50', '#e8f5e9'),
    'SUCCESS':   ('#4caf50', '#e8f5e9'),
    'CHECK':     ('#4caf50', '#e8f5e9'),
    'DONE':      ('#4caf50', '#e8f5e9'),
    'WARNING':   ('#ff9800', '#fff3e0'),
    'CAUTION':   ('#ff9800', '#fff3e0'),
    'ATTENTION': ('#ff9800', '#fff3e0'),
    'DANGER':    ('#f44336', '#ffebee'),
    'ERROR':     ('#f44336', '#ffebee'),
    'FAILURE':   ('#f44336', '#ffebee'),
    'BUG':       ('#f44336', '#ffebee'),
    'QUESTION':  ('#9c27b0', '#f3e5f5'),
    'FAQ':       ('#9c27b0', '#f3e5f5'),
    'HELP':      ('#9c27b0', '#f3e5f5'),
    'QUOTE':     ('#607d8b', '#eceff1'),
    'CITE':      ('#607d8b', '#eceff1'),
    'EXAMPLE':   ('#009688', '#e0f2f1'),
    'TODO':      ('#ff6f00', '#fff8e1'),
    'ABSTRACT':  ('#00bcd4', '#e0f7fa'),
    'SUMMARY':   ('#00bcd4', '#e0f7fa'),
}


# ── Main Markdown parser ──────────────────────────────────────────────────────

def parse_md(text):
    meta = {
        'title': '', 'subtitle': '',
        'author': 'TANG ZE ZHEN',
        'date': datetime.now().strftime('%Y.%m.%d'),
        'abstract': '', 'keywords': '',
        'prev_text': '', 'prev_url': '#',
        'next_text': '', 'next_url': '#',
        'footer_tag': 'END OF DOCUMENT / NODE_01_SUCCESS',
    }

    # YAML frontmatter
    fm = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
    if fm:
        for line in fm.group(1).splitlines():
            m = re.match(r'(\w+):\s*(.*)', line)
            if m:
                k, v = m.group(1).lower(), m.group(2).strip().strip("\"'")
                if k in meta:
                    meta[k] = v
        text = text[fm.end():]

    blocks = []
    lines  = text.splitlines()
    i      = 0

    def is_list_line(ln):
        return bool(re.match(r'^\s*(?:[-*+]|\d+\.)\s', ln))

    def is_block_start(ln):
        s = ln.strip()
        return (s == '' or s.startswith('>') or s.startswith('|') or
                re.match(r'^#{1,6}\s', ln) or re.match(r'^```', ln) or
                re.match(r'^[-*_]{3,}\s*$', s) or is_list_line(ln))

    while i < len(lines):
        line  = lines[i]
        line_s = line.strip()

        # ── Fenced code block
        if re.match(r'^```', line):
            lang = line.lstrip('`').strip()
            code = []
            i += 1
            while i < len(lines) and not re.match(r'^```', lines[i]):
                code.append(lines[i])
                i += 1
            blocks.append({'type': 'code', 'lang': lang,
                           'content': '\n'.join(code)})
            i += 1
            continue

        # ── Headings
        m = re.match(r'^(#{1,6})\s+(.*)', line)
        if m:
            level   = len(m.group(1))
            content = m.group(2).strip()
            if level == 1:
                if not meta['title']:
                    meta['title'] = content
            elif level == 2:
                blocks.append({'type': 'h2', 'content': content})
            else:
                blocks.append({'type': 'h3', 'content': content})
            i += 1
            continue

        # ── Pipe table
        if line_s.startswith('|'):
            tbl = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                tbl.append(lines[i])
                i += 1
            if len(tbl) >= 2:
                blocks.append(_parse_table(tbl))
            continue

        # ── Blockquote / Callout
        if line_s.startswith('>'):
            bq = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                bq.append(re.sub(r'^>\s?', '', lines[i]))
                i += 1
            cm = re.match(r'^\[!([\w -]+)\][-+]?\s*(.*)', bq[0]) if bq else None
            if cm:
                ctype  = cm.group(1).strip().upper()
                ctitle = cm.group(2).strip() or ctype.capitalize()
                blocks.append({'type': 'callout', 'ctype': ctype,
                               'title': ctitle,
                               'content': '\n'.join(bq[1:]).strip()})
            else:
                blocks.append({'type': 'blockquote',
                               'content': inline_md(' '.join(
                                   ln for ln in bq if ln.strip()))})
            continue

        # ── Horizontal rule
        if re.match(r'^[-*_]{3,}\s*$', line_s):
            blocks.append({'type': 'hr'})
            i += 1
            continue

        # ── List
        if is_list_line(line):
            lst = []
            while i < len(lines) and (is_list_line(lines[i]) or
                  (lines[i].startswith(('  ', '\t')) and lst)):
                lst.append(lines[i])
                i += 1
            blocks.append(_parse_list_block(lst))
            continue

        # ── Blank line
        if line_s == '':
            i += 1
            continue

        # ── Paragraph
        para = []
        while i < len(lines) and not is_block_start(lines[i]):
            para.append(lines[i].strip())
            i += 1
        if para:
            blocks.append({'type': 'p',
                           'content': inline_md(' '.join(para))})

    return meta, blocks


# ── HTML builder ─────────────────────────────────────────────────────────────

def _render_blocks(blocks):
    e = htmllib.escape
    out = ""
    for b in blocks:
        t = b['type']

        if t == 'h2':
            out += f'\n<h2>{b["content"]}</h2>'

        elif t == 'h3':
            out += f'\n<h3>{b["content"]}</h3>'

        elif t == 'p':
            out += f'\n<p>{b["content"]}</p>'

        elif t == 'hr':
            out += '\n<hr>'

        elif t == 'blockquote':
            out += f'\n<blockquote>{b["content"]}</blockquote>'

        elif t == 'code':
            lang     = e(b.get('lang', ''))
            content  = e(b.get('content', ''))
            lang_tag = f'<span class="code-lang">{lang}</span>\n' if lang else ''
            out += f'\n<pre>{lang_tag}{content}</pre>'

        elif t == 'table':
            out += '\n<div class="table-wrap"><table><thead><tr>'
            for h in b['headers']:
                out += f'<th>{h}</th>'
            out += '</tr></thead><tbody>'
            for row in b['rows']:
                out += '<tr>'
                for cell in row:
                    out += f'<td>{cell}</td>'
                out += '</tr>'
            out += '</tbody></table></div>'

        elif t == 'list':
            tag = 'ol' if b['ordered'] else 'ul'
            out += f'\n<{tag}>'
            for item in b['items']:
                if item.get('task'):
                    chk = ' checked' if item['done'] else ''
                    sty = ' class="done"' if item['done'] else ''
                    out += (f'<li class="task-item">'
                            f'<input type="checkbox" disabled{chk}>'
                            f'<span{sty}>{item["text"]}</span></li>')
                else:
                    out += f'<li>{item["text"]}</li>'
            out += f'</{tag}>'

        elif t == 'callout':
            bc, bg = _CALLOUT.get(b['ctype'], ('#607d8b', '#f5f5f5'))
            title   = inline_md(b['title'])
            content = inline_md(b['content']).replace('\n', '<br>')
            out += (f'\n<div class="callout" style="border-color:{bc};background:{bg}">'
                    f'<div class="ct" style="color:{bc}">{title}</div>'
                    f'<div class="cb">{content}</div></div>')

    return out


def build_html(meta, blocks):
    e = htmllib.escape

    body = _render_blocks(blocks)

    sub_html = (f'<div class="article-subtitle">{e(meta["subtitle"])}</div>'
                if meta["subtitle"] else "")

    abs_html = ""
    if meta["abstract"]:
        kw = (f'<br><strong>关键词：</strong>{meta["keywords"]}'
              if meta["keywords"] else "")
        abs_html = (
            '<section class="abstract-box">'
            '<span class="abstract-label">摘要 / ABSTRACT</span>'
            f'{meta["abstract"].replace(chr(10), "<br>")}{kw}'
            '</section>'
        )

    inner_js = (
        "var poster=document.getElementById('poster');"
        "var tx=0,ty=0,cx=0,cy=0;"
        "if(window.innerWidth>1024){window.addEventListener('mousemove',function(e){"
        "tx=(e.clientX/window.innerWidth-0.5)*15;"
        "ty=(e.clientY/window.innerHeight-0.5)*15;});}"
        "function raf(){cx+=(tx-cx)*0.1;cy+=(ty-cy)*0.1;"
        "poster.style.transform='rotateY('+cx+'deg) rotateX('+(-cy)+'deg)';"
        "requestAnimationFrame(raf);}raf();"
        "setInterval(function(){var n=new Date();"
        "document.getElementById('time-code').textContent="
        "n.toLocaleTimeString('en-GB')+':'+('0'+Math.floor(n.getMilliseconds()/10)).slice(-2);},40);"
        "var pc=document.getElementById('particles');"
        "for(var i=0;i<40;i++){var d=document.createElement('div');d.className='dot';"
        "var s=Math.random()*2;"
        "d.style.cssText='width:'+s+'px;height:'+s+'px;left:'+(Math.random()*100)+'%;"
        "top:'+(Math.random()*100)+'%;--z:'+(Math.random()*1000-500)+'px;"
        "--duration:'+(2+Math.random()*3)+'s;';pc.appendChild(d);}"
    )

    title  = meta['title'] or '未命名文章'
    author = meta['author']
    date   = meta['date']
    pu     = e(meta['prev_url'] or '#')
    nu     = e(meta['next_url'] or '#')

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
    <title>{e(title)}</title>
    <style>
:root{{--red:#ff3b30;--paper:#f5f5f7;--dark:#1d1d1f;--dim:#86868b;--bg:#0a0b10;}}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:var(--bg);color:var(--dark);font-family:"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;line-height:1.8;overflow-x:hidden;}}
.particles{{position:fixed;width:100%;height:100%;pointer-events:none;z-index:0;}}
.dot{{position:absolute;background:#fff;border-radius:50%;opacity:.2;animation:tw var(--duration) infinite ease-in-out;}}
@keyframes tw{{0%,100%{{opacity:.1;transform:scale(.8);}}50%{{opacity:.6;transform:scale(1.2);}}}}
.top-nav{{position:fixed;top:0;width:100%;z-index:100;background:rgba(245,245,247,.88);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);border-bottom:1px solid rgba(0,0,0,.07);padding:10px 20px;display:flex;justify-content:space-between;align-items:center;}}
.back-link{{font-size:12px;font-weight:800;color:var(--red);text-decoration:none;letter-spacing:1px;}}
.nav-info{{font-size:10px;color:var(--dim);font-family:monospace;}}
.wrap{{position:relative;z-index:10;margin:80px auto 40px;width:92%;max-width:800px;background:var(--paper);box-shadow:0 40px 100px rgba(0,0,0,.5);padding:40px 30px;min-height:100vh;transition:transform .4s cubic-bezier(.2,0,.2,1);}}
@media(max-width:600px){{.wrap{{width:100%;margin:60px 0 0;padding:30px 20px;box-shadow:none;}}h1.at{{font-size:24px!important;}}}}
/* Header */
.ah{{border-bottom:2px solid var(--red);padding-bottom:20px;margin-bottom:30px;}}
h1.at{{font-size:28px;font-weight:900;line-height:1.3;margin-bottom:10px;color:#000;}}
.article-subtitle{{font-size:18px;color:#444;margin-bottom:15px;font-weight:600;}}
.abstract-box{{background:#eee;padding:15px;margin-bottom:30px;font-size:14px;color:#555;border-left:3px solid var(--red);}}
.abstract-label{{font-weight:800;color:var(--dark);display:block;margin-bottom:5px;font-size:12px;}}
/* Body */
.ab{{font-size:16px;text-align:justify;}}
.ab p{{margin-bottom:22px;}}
.ab h2{{font-size:20px;font-weight:800;margin:40px 0 18px;display:flex;align-items:center;}}
.ab h2::before{{content:"";width:12px;height:12px;background:var(--red);margin-right:10px;display:inline-block;flex-shrink:0;}}
.ab h3{{font-size:17px;font-weight:700;margin:28px 0 14px;color:#333;}}
.ab hr{{border:none;border-top:1px dashed #ccc;margin:28px 0;}}
/* Tables */
.table-wrap{{overflow-x:auto;margin:20px 0;}}
.ab table{{width:100%;border-collapse:collapse;font-size:15px;}}
.ab th{{background:#f0f0f0;font-weight:800;padding:10px 14px;text-align:left;border-bottom:2px solid var(--red);white-space:nowrap;}}
.ab td{{padding:8px 14px;border-bottom:1px solid #ddd;}}
.ab tr:last-child td{{border-bottom:none;}}
.ab tr:nth-child(even) td{{background:#f9f9f9;}}
/* Code */
.ab pre{{background:#1e1e2e;color:#cdd6f4;padding:16px 18px;overflow-x:auto;margin:20px 0;font-family:"Courier New",monospace;font-size:13px;line-height:1.65;border-left:3px solid var(--red);}}
.code-lang{{font-size:10px;color:var(--red);letter-spacing:1px;display:block;margin-bottom:8px;font-family:monospace;}}
.ab code.ic{{background:#f0f0f2;color:#c44030;padding:2px 5px;font-size:.88em;font-family:"Courier New",monospace;}}
/* Blockquote */
.ab blockquote{{border-left:3px solid var(--red);padding:8px 16px;margin:20px 0;color:#555;font-style:italic;background:#f5f5f5;}}
/* Callout */
.callout{{margin:20px 0;padding:14px 18px;border-left:4px solid;}}
.callout .ct{{font-weight:800;font-size:13px;letter-spacing:.5px;margin-bottom:6px;}}
.callout .cb{{font-size:15px;line-height:1.7;}}
/* Lists */
.ab ul,.ab ol{{margin:12px 0 16px 26px;}}
.ab li{{margin-bottom:5px;line-height:1.7;}}
.task-item{{list-style:none;margin-left:-18px;}}
.task-item input{{margin-right:7px;cursor:default;}}
.task-item .done{{text-decoration:line-through;color:#999;}}
/* Obsidian inline */
mark{{background:#ffe066;padding:1px 3px;}}
del{{color:#999;}}
.wl{{color:var(--red);font-style:italic;border-bottom:1px dashed var(--red);cursor:default;}}
.tag{{background:#eee;color:#666;font-size:12px;padding:1px 6px;border-radius:3px;font-family:monospace;}}
.obs-img{{max-width:100%;height:auto;margin:16px 0;display:block;}}
.obs-embed{{color:#aaa;font-style:italic;}}
/* Footer */
.footer-tag{{margin-top:40px;text-align:center;font-family:monospace;font-size:10px;color:var(--red);opacity:.6;}}
.bottom-actions{{display:flex;justify-content:space-between;margin-top:40px;padding:20px 0;border-top:1px dashed #ccc;flex-wrap:wrap;gap:8px;}}
.action-btn{{font-size:12px;color:var(--dark);text-decoration:none;font-weight:bold;}}
.action-btn:hover{{color:var(--red);}}
    </style>
</head>
<body>
<div class="particles" id="particles"></div>
<nav class="top-nav">
    <a href="javascript:history.back()" class="back-link">&#8592; INDEX</a>
    <div class="nav-info" id="time-code">00:00:00</div>
</nav>
<div class="wrap" id="poster">
    <header class="ah">
        <h1 class="at">{e(title)}</h1>
        {sub_html}
        <div style="font-size:12px;color:var(--dim);font-weight:bold;letter-spacing:2px;">{e(author)} / {e(date)}</div>
    </header>
    {abs_html}
    <article class="ab">
{body}
    </article>
    <div class="bottom-actions">
        <a href="{pu}" class="action-btn">PREV: {e(meta['prev_text'])}</a>
        <a href="javascript:window.scrollTo({{top:0,behavior:'smooth'}})" class="action-btn">BACK TO TOP &#8593;</a>
        <a href="{nu}" class="action-btn">NEXT: {e(meta['next_text'])}</a>
    </div>
    <div class="footer-tag">{e(meta['footer_tag'])}</div>
</div>
<script>{inner_js}</script>
</body>
</html>"""


# ── GUI ──────────────────────────────────────────────────────────────────────

class BlogForge:

    PIXEL_STARS = [
        "  ·  ★  ·  ·  ·  ★  ·  ",
        "·  ·  ·  ◆  ·  ·  ·  ·  ",
        "  ·  ·  ·  ·  ★  ·  ◆  ·",
    ]

    def __init__(self):
        if HAS_DND:
            self.root = TkinterDnD.Tk()
        else:
            self.root = tk.Tk()

        self.root.title("★ BLOG FORGE ★  MD → HTML")
        self.root.configure(bg=BG)
        self.root.geometry("1160x720")
        self.root.minsize(860, 560)

        self.md_path      = ""
        self.meta         = {}
        self.blocks       = []
        self.generated    = ""
        self._blink_state = True
        self._star_idx    = 0

        self._build()
        self._tick()
        self.root.mainloop()

    # ── Layout ───────────────────────────────────────────────────────────────

    def _build(self):
        self._titlebar()
        tk.Frame(self.root, bg=BORDER, height=2).pack(fill=tk.X)

        panes = tk.Frame(self.root, bg=BG)
        panes.pack(fill=tk.BOTH, expand=True)

        self._left(panes)
        tk.Frame(panes, bg=BORDER, width=2).pack(side=tk.LEFT, fill=tk.Y)
        self._right(panes)

        self._statusbar()

    def _titlebar(self):
        bar = tk.Frame(self.root, bg=RAISED, height=50)
        bar.pack(fill=tk.X)
        bar.pack_propagate(False)

        tk.Label(bar, text="▓▒░", bg=RAISED, fg=GOLD, font=F_XL
                 ).pack(side=tk.LEFT, padx=12)
        tk.Label(bar, text="★  BLOG FORGE  ★", bg=RAISED, fg=TEXT, font=F_XL
                 ).pack(side=tk.LEFT)
        tk.Label(bar, text="  MD → HTML 转换器", bg=RAISED, fg=GOLD, font=F_LG
                 ).pack(side=tk.LEFT)
        tk.Label(bar, text="░▒▓", bg=RAISED, fg=GOLD, font=F_XL
                 ).pack(side=tk.LEFT, padx=6)

        dnd_txt = "◆ 拖放已启用" if HAS_DND else "△ pip install tkinterdnd2 开启拖放"
        tk.Label(bar, text=dnd_txt, bg=RAISED,
                 fg=GREEN if HAS_DND else DIM, font=F_XS
                 ).pack(side=tk.RIGHT, padx=12)

    def _left(self, parent):
        left = tk.Frame(parent, bg=PANEL, width=430)
        left.pack(side=tk.LEFT, fill=tk.Y)
        left.pack_propagate(False)

        # ── Drop zone ──
        self._sec(left, "01", "INPUT / 输入 MD 文件")

        drop_outer = tk.Frame(left, bg=BORDER, padx=2, pady=2)
        drop_outer.pack(fill=tk.X, padx=14, pady=(0, 6))

        self.drop_frame = tk.Frame(drop_outer, bg=DROP_BG, height=150)
        self.drop_frame.pack(fill=tk.BOTH)
        self.drop_frame.pack_propagate(False)

        self.drop_top = tk.Label(self.drop_frame,
            text="◆  ◆  ◆",
            bg=DROP_BG, fg=GOLD, font=F_LG)
        self.drop_top.pack(pady=(18, 4))

        self.drop_main = tk.Label(self.drop_frame,
            text="拖入 .md 文件  /  DROP FILE HERE",
            bg=DROP_BG, fg=TEXT, font=F_MD)
        self.drop_main.pack()

        self.drop_sub = tk.Label(self.drop_frame,
            text="或点击此区域浏览  /  or click to browse",
            bg=DROP_BG, fg=DIM, font=F_XS)
        self.drop_sub.pack(pady=(4, 0))

        self.drop_star = tk.Label(self.drop_frame,
            text=self.PIXEL_STARS[0],
            bg=DROP_BG, fg=DIM, font=F_XS)
        self.drop_star.pack(pady=(6, 10))

        for w in (self.drop_frame, self.drop_top, self.drop_main,
                  self.drop_sub, self.drop_star):
            w.bind("<Button-1>", lambda e: self._browse())
            w.configure(cursor="hand2")

        if HAS_DND:
            self.drop_frame.drop_target_register(DND_FILES)
            self.drop_frame.dnd_bind("<<Drop>>", self._on_drop)
            self.drop_frame.bind("<Enter>", self._drop_enter)
            self.drop_frame.bind("<Leave>", self._drop_leave)

        # File label
        self.file_lbl = tk.Label(left, text="[ 未选择文件 ]",
                                  bg=PANEL, fg=DIM, font=F_XS)
        self.file_lbl.pack(pady=(0, 4))

        # Browse button
        bf = tk.Frame(left, bg=PANEL)
        bf.pack(fill=tk.X, padx=14, pady=2)
        self._btn(bf, "▶  浏览文件 / BROWSE FILE", GREEN, self._browse
                  ).pack(fill=tk.X)

        # ── Metadata ──
        self._sec(left, "02", "METADATA / 文章元信息")

        ff = tk.Frame(left, bg=PANEL)
        ff.pack(fill=tk.X, padx=14, pady=2)

        self.v_title    = tk.StringVar()
        self.v_subtitle = tk.StringVar()
        self.v_author   = tk.StringVar(value="TANG ZE ZHEN")
        self.v_date     = tk.StringVar(value=datetime.now().strftime("%Y.%m.%d"))
        self.v_footer   = tk.StringVar(value="END OF DOCUMENT / NODE_01_SUCCESS")

        self._field(ff, "TITLE / 标题",      self.v_title,    focus=True)
        self._field(ff, "SUBTITLE / 副标题", self.v_subtitle)
        self._field(ff, "AUTHOR / 作者",     self.v_author)
        self._field(ff, "DATE / 日期",       self.v_date)
        self._field(ff, "FOOTER TAG",        self.v_footer)

        # ── Actions ──
        self._sec(left, "03", "ACTION / 操作")

        af = tk.Frame(left, bg=PANEL)
        af.pack(fill=tk.X, padx=14, pady=6)
        self._btn(af, "◆  GENERATE HTML  /  生成", RED, self._generate,
                  pady=8).pack(fill=tk.X)

    def _right(self, parent):
        right = tk.Frame(parent, bg=BG)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Header bar
        hdr = tk.Frame(right, bg=RAISED, height=38)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        self.dot = tk.Label(hdr, text="●", bg=RAISED, fg=DIM, font=F_MD)
        self.dot.pack(side=tk.LEFT, padx=10)
        tk.Label(hdr, text="OUTPUT / HTML 输出预览",
                 bg=RAISED, fg=TEXT, font=F_MD).pack(side=tk.LEFT)

        self.info_lbl = tk.Label(hdr, text="", bg=RAISED, fg=DIM, font=F_XS)
        self.info_lbl.pack(side=tk.RIGHT, padx=10)

        # Button row
        br = tk.Frame(right, bg=PANEL)
        br.pack(fill=tk.X, padx=10, pady=6)
        self._btn(br, "▼ SAVE / 保存",    TEAL,  self._save   ).pack(side=tk.LEFT, padx=(0, 6))
        self._btn(br, "◻ COPY / 复制",    GOLD,  self._copy   ).pack(side=tk.LEFT, padx=(0, 6))
        self._btn(br, "⊕ BROWSER / 预览", GREEN, self._open   ).pack(side=tk.LEFT, padx=(0, 6))
        self._btn(br, "▲ PUBLISH / 发布", RED,   self._publish).pack(side=tk.LEFT)

        tk.Frame(right, bg=BORDER, height=1).pack(fill=tk.X)

        # Text + scrollbars
        tf = tk.Frame(right, bg=BG)
        tf.pack(fill=tk.BOTH, expand=True)

        vsb = tk.Scrollbar(tf, bg=RAISED, troughcolor=PANEL,
                           activebackground=GOLD)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self.out = tk.Text(tf,
            bg=INPUT, fg=TEXT,
            font=("Courier", 9),
            insertbackground=GOLD,
            selectbackground=BORDER,
            selectforeground=TEXT,
            relief=tk.FLAT,
            padx=12, pady=12,
            wrap=tk.NONE,
            yscrollcommand=vsb.set,
            state=tk.DISABLED)
        self.out.pack(fill=tk.BOTH, expand=True)
        vsb.config(command=self.out.yview)

        hsb = tk.Scrollbar(right, orient=tk.HORIZONTAL,
                           bg=RAISED, troughcolor=PANEL)
        hsb.pack(fill=tk.X)
        self.out.config(xscrollcommand=hsb.set)
        hsb.config(command=self.out.xview)

        self._write_out(
            "╔══════════════════════════════════════════════════════╗\n"
            "║                                                      ║\n"
            "║   ★  BLOG FORGE  ★   等待中...                     ║\n"
            "║                                                      ║\n"
            "║   1. 拖入 .md 文件  ─────────────  drop zone       ║\n"
            "║   2. 确认元信息    ──────────────  左侧面板         ║\n"
            "║   3. 点击  GENERATE  ───────────  生成 HTML        ║\n"
            "║   4. SAVE / COPY / BROWSER  ────  导出或预览       ║\n"
            "║                                                      ║\n"
            "╚══════════════════════════════════════════════════════╝"
        )

    def _statusbar(self):
        sb = tk.Frame(self.root, bg=RAISED, height=24)
        sb.pack(fill=tk.X, side=tk.BOTTOM)
        sb.pack_propagate(False)
        tk.Frame(sb, bg=BORDER, width=1).pack(side=tk.LEFT, fill=tk.Y)
        self.status_var = tk.StringVar(value="READY  ◆  拖入 MD 文件或点击浏览")
        tk.Label(sb, textvariable=self.status_var,
                 bg=RAISED, fg=DIM, font=F_XS,
                 anchor=tk.W).pack(side=tk.LEFT, padx=8)
        self.cursor_lbl = tk.Label(sb, text="█", bg=RAISED, fg=GOLD, font=F_XS)
        self.cursor_lbl.pack(side=tk.LEFT)
        tk.Label(sb, text="★ BLOG FORGE v1.0  ★ 2003vip",
                 bg=RAISED, fg=DIM, font=F_XS).pack(side=tk.RIGHT, padx=10)

    # ── Widget helpers ────────────────────────────────────────────────────────

    def _sec(self, parent, num, label):
        f = tk.Frame(parent, bg=PANEL)
        f.pack(fill=tk.X, padx=14, pady=(10, 4))
        tk.Label(f, text=f" {num} ", bg=RED, fg=TEXT,
                 font=F_SM).pack(side=tk.LEFT, padx=(0, 7))
        tk.Label(f, text=label, bg=PANEL, fg=GOLD,
                 font=F_SM).pack(side=tk.LEFT)
        tk.Frame(parent, bg=BORDER, height=1).pack(fill=tk.X, padx=14, pady=(0, 6))

    def _btn(self, parent, text, color, cmd, pady=5):
        text_color = BG if color in (GOLD, TEAL, GREEN) else TEXT
        b = tk.Button(parent, text=text, bg=color, fg=text_color,
                      font=F_SM, relief=tk.FLAT, bd=0,
                      padx=10, pady=pady, cursor="hand2", command=cmd,
                      activebackground=BORDER, activeforeground=TEXT)
        c = color  # capture
        tc = text_color
        b.bind("<Enter>", lambda e, _b=b: _b.configure(bg=BORDER, fg=TEXT))
        b.bind("<Leave>", lambda e, _b=b, _c=c, _tc=tc: _b.configure(bg=_c, fg=_tc))
        return b

    def _field(self, parent, label, var, focus=False):
        tk.Label(parent, text=label, bg=PANEL, fg=DIM,
                 font=F_XS, anchor=tk.W).pack(fill=tk.X, pady=(4, 0))
        e = tk.Entry(parent, textvariable=var, bg=INPUT, fg=TEXT,
                     insertbackground=GOLD, relief=tk.FLAT, font=F_MD,
                     highlightthickness=1,
                     highlightcolor=GOLD, highlightbackground=BORDER)
        e.pack(fill=tk.X, pady=(1, 4))
        if focus:
            e.focus_set()

    def _write_out(self, text):
        self.out.configure(state=tk.NORMAL)
        self.out.delete("1.0", tk.END)
        self.out.insert(tk.END, text)
        self.out.configure(state=tk.DISABLED)

    def _set_status(self, msg):
        self.status_var.set(msg)

    # ── Animation ─────────────────────────────────────────────────────────────

    def _tick(self):
        self._blink_state = not self._blink_state
        self.cursor_lbl.configure(fg=GOLD if self._blink_state else PANEL)
        if self._blink_state:
            self.dot.configure(fg=GREEN)
        else:
            self.dot.configure(fg=DIM)

        self._star_idx = (self._star_idx + 1) % len(self.PIXEL_STARS)
        self.drop_star.configure(text=self.PIXEL_STARS[self._star_idx])

        self.root.after(700, self._tick)

    # ── Drop zone hover ───────────────────────────────────────────────────────

    def _drop_enter(self, _e=None):
        self.drop_frame.configure(bg=DROP_HL)
        for w in (self.drop_top, self.drop_main, self.drop_sub, self.drop_star):
            w.configure(bg=DROP_HL)
        self.drop_main.configure(text="◆  释放以加载  /  RELEASE TO LOAD  ◆",
                                  fg=GOLD)

    def _drop_leave(self, _e=None):
        self.drop_frame.configure(bg=DROP_BG)
        for w in (self.drop_top, self.drop_main, self.drop_sub, self.drop_star):
            w.configure(bg=DROP_BG)
        self.drop_main.configure(text="拖入 .md 文件  /  DROP FILE HERE",
                                  fg=TEXT)

    # ── File handling ─────────────────────────────────────────────────────────

    def _on_drop(self, event):
        raw = event.data.strip()
        # tkinterdnd2 wraps space-containing paths in {}
        if raw.startswith("{") and raw.endswith("}"):
            raw = raw[1:-1]
        self._load(raw)

    def _browse(self):
        path = filedialog.askopenfilename(
            title="选择 Markdown 文件",
            filetypes=[("Markdown", "*.md *.markdown"), ("All files", "*.*")])
        if path:
            self._load(path)

    def _load(self, path):
        path = path.strip()
        if not os.path.isfile(path):
            self._set_status(f"ERROR ◆ 文件不存在: {path}")
            return
        try:
            with open(path, encoding="utf-8") as f:
                raw = f.read()
        except Exception as ex:
            self._set_status(f"ERROR ◆ 读取失败: {ex}")
            return

        self.md_path = path
        fname = os.path.basename(path)

        self.meta, self.blocks = parse_md(raw)

        # Update fields
        self.v_title.set(self.meta.get("title", ""))
        self.v_subtitle.set(self.meta.get("subtitle", ""))
        self.v_author.set(self.meta.get("author", "TANG ZE ZHEN"))
        self.v_date.set(self.meta.get("date", ""))
        self.v_footer.set(self.meta.get("footer_tag",
                          "END OF DOCUMENT / NODE_01_SUCCESS"))

        # Update drop zone appearance
        self.drop_main.configure(text=f"◆  {fname}  ◆", fg=GREEN)
        self.drop_sub.configure(text="已加载  ✓  点击 GENERATE 生成", fg=TEAL)
        self.file_lbl.configure(text=f"◆ {fname}", fg=TEAL)

        n = len(self.blocks)
        self._set_status(f"LOADED  ◆  {fname}  |  {n} 块  |  标题: {self.meta.get('title', '无')}")

        preview_lines = [
            "╔══ 文件加载成功 ════════════════════════════════════╗",
            f"║  文件: {fname[:48]}",
            f"║  标题: {self.meta.get('title', '(无)')[:48]}",
            f"║  作者: {self.meta.get('author', '')[:48]}",
            f"║  日期: {self.meta.get('date', '')[:48]}",
            f"║  块数: {n} 个内容块",
            "║",
            "║  内容预览:",
        ]
        for b in self.blocks[:8]:
            tag = {"h2": "## ", "h3": "### ", "p": "   "}.get(b["type"], "   ")
            txt = re.sub(r"<[^>]+>", "", b.get("content", ""))
            preview_lines.append(f"║  {tag}{txt[:50]}")
        if len(self.blocks) > 8:
            preview_lines.append(f"║  ... 还有 {len(self.blocks) - 8} 块")
        preview_lines.append("╚══════════════════════════════════════════════════╝")
        preview_lines.append("")
        preview_lines.append("  ▶  点击  GENERATE HTML  生成完整 HTML")

        self._write_out("\n".join(preview_lines))

    # ── Generate ──────────────────────────────────────────────────────────────

    def _generate(self):
        if not self.blocks and not self.v_title.get().strip():
            messagebox.showwarning("Blog Forge", "请先加载 .md 文件，或填写标题！")
            return

        self.meta["title"]     = self.v_title.get()
        self.meta["subtitle"]  = self.v_subtitle.get()
        self.meta["author"]    = self.v_author.get()
        self.meta["date"]      = self.v_date.get()
        self.meta["footer_tag"] = self.v_footer.get()

        self.generated = build_html(self.meta, self.blocks)
        self._write_out(self.generated)

        lines = self.generated.count("\n")
        chars = len(self.generated)
        self._set_status(
            f"GENERATED  ◆  {lines} 行  |  {chars:,} 字符  |  可保存 / 复制 / 预览")
        self.info_lbl.configure(text=f"✓ {chars:,} chars", fg=GREEN)
        self.dot.configure(fg=GOLD)

    # ── Export ────────────────────────────────────────────────────────────────

    def _save(self):
        if not self.generated:
            messagebox.showwarning("Blog Forge", "请先点击 GENERATE 生成 HTML！")
            return
        default = re.sub(r"[^\w一-龥]", "_",
                         self.meta.get("title", "article"))[:40] + ".html"
        init_dir = os.path.dirname(self.md_path) if self.md_path else \
                   os.path.expanduser("~")
        path = filedialog.asksaveasfilename(
            title="保存 HTML 文件",
            initialdir=init_dir,
            initialfile=default,
            defaultextension=".html",
            filetypes=[("HTML", "*.html"), ("All", "*.*")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.generated)
        fname = os.path.basename(path)
        self._set_status(f"SAVED  ◆  {fname}  ✓")
        self.info_lbl.configure(text=f"✓ {fname}", fg=GREEN)

    def _copy(self):
        if not self.generated:
            messagebox.showwarning("Blog Forge", "请先点击 GENERATE 生成 HTML！")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(self.generated)
        self._set_status("COPIED  ◆  HTML 已复制到剪贴板  ✓")

    def _open(self):
        if not self.generated:
            messagebox.showwarning("Blog Forge", "请先点击 GENERATE 生成 HTML！")
            return
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False,
                                         encoding="utf-8") as f:
            f.write(self.generated)
            tmp = f.name
        webbrowser.open(f"file://{tmp}")
        self._set_status(f"BROWSER  ◆  已在浏览器打开预览  ✓")

    def _publish(self):
        if not self.generated:
            messagebox.showwarning("Blog Forge", "请先点击 GENERATE 生成 HTML！")
            return

        title   = self.meta.get('title', 'article')
        default = re.sub(r'[^\w一-龥]', '_', title)[:40] + '.html'

        path = filedialog.asksaveasfilename(
            title="保存到仓库并发布",
            initialdir=REPO_DIR,
            initialfile=default,
            defaultextension=".html",
            filetypes=[("HTML", "*.html")])
        if not path:
            return

        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.generated)

        fname = os.path.basename(path)
        self._set_status(f"PUBLISHING  ◆  {fname}  →  pushing to GitHub...")
        self.info_lbl.configure(text="pushing...", fg=GOLD)

        def _git_push():
            try:
                subprocess.run(['git', 'add', fname],
                               cwd=REPO_DIR, check=True,
                               capture_output=True)
                subprocess.run(['git', 'commit', '-m', f'publish: {title}'],
                               cwd=REPO_DIR, check=True,
                               capture_output=True)
                result = subprocess.run(['git', 'push', 'origin', 'main'],
                                        cwd=REPO_DIR,
                                        capture_output=True, text=True)
                if result.returncode == 0:
                    self.root.after(0, lambda: self._set_status(
                        f"PUBLISHED  ◆  {fname}  →  GitHub  →  Cloudflare Pages  ✓"))
                    self.root.after(0, lambda: self.info_lbl.configure(
                        text="✓ published", fg=GREEN))
                else:
                    err = (result.stderr or result.stdout).strip()[:100]
                    self.root.after(0, lambda: self._set_status(
                        f"PUSH FAILED  ◆  {err}"))
                    self.root.after(0, lambda: self.info_lbl.configure(
                        text="push failed", fg=RED))
            except subprocess.CalledProcessError as ex:
                msg = str(ex)[:100]
                self.root.after(0, lambda: self._set_status(
                    f"GIT ERROR  ◆  {msg}"))
                self.root.after(0, lambda: self.info_lbl.configure(
                    text="git error", fg=RED))

        threading.Thread(target=_git_push, daemon=True).start()


# ── Entry ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    BlogForge()
