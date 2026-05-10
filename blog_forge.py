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


def inline_poem(text):
    """Like inline_md, plus auto-dim full-width / ASCII parentheticals for poetry."""
    text = inline_md(text)
    # 全角括号  （...）→ dim-text
    text = re.sub(r'（([^）]+)）', r'<span class="dim-text">（\1）</span>', text)
    # 半角括号  (...)  → dim-text
    text = re.sub(r'\(([^)]+)\)',  r'<span class="dim-text">(\1)</span>',   text)
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


# ── Callout body renderer (supports embedded tables) ─────────────────────────

def _render_callout_body(content_text):
    """Render callout / blockquote body with support for embedded pipe tables,
    code spans, and basic Obsidian inline syntax."""
    if not content_text:
        return ''
    lines = content_text.split('\n')
    out   = ''
    i     = 0
    while i < len(lines):
        line = lines[i]
        # ── Embedded pipe table: need ≥2 consecutive | lines
        if (line.strip().startswith('|') and
                i + 1 < len(lines) and lines[i + 1].strip().startswith('|')):
            tbl_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                tbl_lines.append(lines[i])
                i += 1
            if len(tbl_lines) >= 2:
                tbl = _parse_table(tbl_lines)
                out += '<div class="table-wrap"><table><thead><tr>'
                for h in tbl['headers']:
                    out += f'<th>{h}</th>'
                out += '</tr></thead><tbody>'
                for row in tbl['rows']:
                    out += '<tr>'
                    for cell in row:
                        out += f'<td>{cell}</td>'
                    out += '</tr>'
                out += '</tbody></table></div>'
        else:
            rendered = inline_md(line)
            if rendered.strip():
                out += rendered + '<br>'
            else:
                out += '<br>'   # blank line as spacing
            i += 1
    # 用 re.sub 按字符串去掉末尾多余 <br>（不能用 rstrip，它按字符集裁剪会删掉 > 等字符）
    return re.sub(r'(<br>)+$', '', out)


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


# ── Poem Markdown parser ──────────────────────────────────────────────────────

def parse_poem_md(text):
    """Parse a Markdown file structured as a poem collection.

    Convention:
      # 诗题        →  new poem section
      body text     →  poem lines (newlines preserved verbatim)
      （dim text）  →  auto-converted to dim span by inline_poem()
    """
    meta = {
        'title': '', 'author': 'TANG ZE ZHEN',
        'date':  datetime.now().strftime('%Y.%m.%d'),
        'footer_tag': 'THE VOID / 2026',
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

    sections       = []
    current_title  = None
    current_lines  = []

    for line in text.splitlines():
        h1 = re.match(r'^#\s+(.*)', line)
        if h1:
            if current_title is not None:
                sections.append({
                    'title': current_title,
                    'body':  '\n'.join(current_lines).strip(),
                })
            current_title = h1.group(1).strip()
            current_lines = []
        elif current_title is not None:
            current_lines.append(line)

    if current_title is not None:
        sections.append({
            'title': current_title,
            'body':  '\n'.join(current_lines).strip(),
        })

    if not meta['title'] and sections:
        meta['title'] = sections[0]['title']

    return meta, sections


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
            content = _render_callout_body(b['content'])
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
.wrap{{position:relative;z-index:10;margin:80px auto 40px;width:92%;max-width:800px;background:var(--paper);box-shadow:0 40px 100px rgba(0,0,0,.5);padding:40px 30px;min-height:100vh;}}
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


# ── Poem HTML builder ────────────────────────────────────────────────────────

def build_poem_html(meta, sections):
    """Render a poem collection — matches ta-zuoshi.html aesthetic:
    black BG, Noto Serif SC, full-page sections, alternating L/R layout,
    fade-in animations, parenthetical dim spans.
    """
    e = htmllib.escape
    title      = e(meta.get('title', '组诗'))
    author     = e(meta.get('author', 'TANG ZE ZHEN'))
    date       = e(meta.get('date', ''))
    footer_tag = e(meta.get('footer_tag', 'THE VOID / 2026'))

    secs_html = ''
    for i, sec in enumerate(sections):
        cls    = ' alt-layout' if i % 2 == 1 else ''
        stitle = e(sec['title'])
        # Apply inline_poem line-by-line to keep pre-wrap newlines
        lines_out = [inline_poem(ln) for ln in sec['body'].split('\n')]
        body_html = '\n'.join(lines_out)
        secs_html += (
            f'\n        <section class="fade-in{cls}">'
            f'\n            <h1 class="poem-title">{stitle}</h1>'
            f'\n            <div class="poem-body">{body_html}</div>'
            f'\n        </section>'
        )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>{title}</title>
    <style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@200;300;400&display=swap');
*{{margin:0;padding:0;box-sizing:border-box;}}
:root{{--bg:#000000;--text:#c0c0c0;--dim:#444;--highlight:#ffffff;}}
body{{background-color:var(--bg);color:var(--text);font-family:'Noto Serif SC',serif;font-weight:200;line-height:2;overflow-x:hidden;-webkit-font-smoothing:antialiased;}}
.scroll-container{{width:100%;max-width:1200px;margin:0 auto;position:relative;}}
section{{min-height:100vh;display:flex;flex-direction:column;justify-content:center;padding:10vh 5vw;border-left:1px solid #111;margin-left:10vw;}}
.alt-layout{{align-items:flex-end;text-align:right;border-left:none;border-right:1px solid #111;margin-left:0;margin-right:10vw;}}
.poem-title{{font-size:2.5rem;color:var(--highlight);letter-spacing:0.8rem;margin-bottom:4rem;font-weight:300;}}
.poem-body{{font-size:1.15rem;white-space:pre-wrap;letter-spacing:0.15rem;max-width:600px;line-height:2.2;}}
.dim-text{{color:var(--dim);font-size:0.95rem;}}
.fade-in{{opacity:0;transform:translateY(30px);transition:all 1.8s cubic-bezier(0.16,1,0.3,1);}}
.fade-in.active{{opacity:1;transform:translateY(0);}}
footer{{height:30vh;display:flex;align-items:center;justify-content:center;font-size:0.7rem;color:#222;letter-spacing:0.5rem;}}
::-webkit-scrollbar{{display:none;}}
    </style>
</head>
<body>
<div class="scroll-container">
{secs_html}
</div>
<footer>{footer_tag} · {author} · {date}</footer>
<script>
const obs=new IntersectionObserver(
  (entries)=>{{entries.forEach(e=>{{if(e.isIntersecting)e.target.classList.add('active');}});}},
  {{threshold:0.1}}
);
document.querySelectorAll('.fade-in').forEach(el=>obs.observe(el));
</script>
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
        self.raw_md       = ""
        self.meta         = {}
        self.blocks       = []
        self.poem_sections = []
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

        # Scrollable canvas wrapper
        _canvas = tk.Canvas(left, bg=PANEL, bd=0, highlightthickness=0)
        _vsb = tk.Scrollbar(left, orient=tk.VERTICAL, command=_canvas.yview,
                            bg=RAISED, troughcolor=PANEL, activebackground=GOLD)
        _vsb.pack(side=tk.RIGHT, fill=tk.Y)
        _canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        inner = tk.Frame(_canvas, bg=PANEL)
        _win = _canvas.create_window((0, 0), window=inner, anchor=tk.NW)

        def _on_frame_configure(_e):
            _canvas.configure(scrollregion=_canvas.bbox("all"))
        inner.bind("<Configure>", _on_frame_configure)

        def _on_canvas_configure(e):
            _canvas.itemconfig(_win, width=e.width)
        _canvas.configure(yscrollcommand=_vsb.set)
        _canvas.bind("<Configure>", _on_canvas_configure)

        def _on_mousewheel(e):
            _canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        inner.bind_all("<MouseWheel>", _on_mousewheel)

        # All content goes into `inner` (was `left`)
        left = inner

        # ── Drop zone ──
        self._sec(left, "01", "INPUT / 输入 MD 文件")

        drop_outer = tk.Frame(left, bg=BORDER, padx=2, pady=2)
        drop_outer.pack(fill=tk.X, padx=14, pady=(0, 6))

        self.drop_frame = tk.Frame(drop_outer, bg=DROP_BG, height=110)
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

        # ── Template ──
        self._sec(left, "03", "TEMPLATE / 输出样式")

        tf2 = tk.Frame(left, bg=PANEL)
        tf2.pack(fill=tk.X, padx=14, pady=4)

        self.v_template = tk.StringVar(value="article")
        for val, label in [
            ("article", "ARTICLE  ·  博客文章（默认）"),
            ("poem",    "POEM     ·  她组诗 / 诗集样式"),
        ]:
            tk.Radiobutton(
                tf2, text=label, variable=self.v_template, value=val,
                bg=PANEL, fg=TEXT, selectcolor=INPUT,
                activebackground=PANEL, activeforeground=GOLD,
                font=F_SM
            ).pack(anchor=tk.W, pady=3)

        # ── Category ──
        self._sec(left, "04", "CATEGORY / 发布归类")

        cf = tk.Frame(left, bg=PANEL)
        cf.pack(fill=tk.X, padx=14, pady=4)

        self.v_category = tk.StringVar(value="2")
        for val, label in [
            ("2", "2.html  ·  理论 / 影评"),
            ("3", "3.html  ·  创作 / 其他"),
            ("0", "不归类  /  Skip index"),
        ]:
            tk.Radiobutton(
                cf, text=label, variable=self.v_category, value=val,
                bg=PANEL, fg=TEXT, selectcolor=INPUT,
                activebackground=PANEL, activeforeground=GOLD,
                font=F_SM
            ).pack(anchor=tk.W, pady=3)

        # ── Actions ──
        self._sec(left, "05", "ACTION / 操作")

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
        self._btn(br, "▲ PUBLISH / 发布", RED,   self._publish).pack(side=tk.LEFT, padx=(0, 6))
        self._btn(br, "◈ DIR EDIT",       BORDER, self._open_dir_editor).pack(side=tk.LEFT)

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
        self.raw_md  = raw          # keep original for poem re-parse
        fname = os.path.basename(path)

        self.meta, self.blocks = parse_md(raw)
        _, self.poem_sections  = parse_poem_md(raw)  # pre-parse poem view too

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
        p = len(self.poem_sections)
        self._set_status(f"LOADED  ◆  {fname}  |  {n} 块 / {p} 诗节  |  标题: {self.meta.get('title', '无')}")

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
        template = self.v_template.get()   # 'article' or 'poem'

        if template == 'poem':
            if not self.poem_sections and not self.v_title.get().strip():
                messagebox.showwarning("Blog Forge",
                    "请先加载包含 # 诗题 的 .md 文件！")
                return

            # Re-parse with latest raw_md in case it changed
            pmeta, psecs = parse_poem_md(self.raw_md) if self.raw_md else ({}, [])

            # Apply GUI field overrides
            if self.v_title.get():  pmeta['title']      = self.v_title.get()
            if self.v_author.get(): pmeta['author']     = self.v_author.get()
            if self.v_date.get():   pmeta['date']       = self.v_date.get()
            if self.v_footer.get(): pmeta['footer_tag'] = self.v_footer.get()

            self.meta  = pmeta
            self.generated = build_poem_html(pmeta, psecs)

            n_sec = len(psecs)
            self._write_out(self.generated)
            chars = len(self.generated)
            self._set_status(
                f"GENERATED [POEM]  ◆  {n_sec} 诗节  |  {chars:,} 字符  |  可保存/预览")
            self.info_lbl.configure(
                text=f"✓ {n_sec} poems · {chars:,} chars", fg=TEAL)
            self.dot.configure(fg=TEAL)

        else:  # article (default)
            if not self.blocks and not self.v_title.get().strip():
                messagebox.showwarning("Blog Forge", "请先加载 .md 文件，或填写标题！")
                return

            self.meta["title"]      = self.v_title.get()
            self.meta["subtitle"]   = self.v_subtitle.get()
            self.meta["author"]     = self.v_author.get()
            self.meta["date"]       = self.v_date.get()
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

    # ── Index injection ───────────────────────────────────────────────────────

    @staticmethod
    def _inject_index(index_path, href, title, date_str):
        """Insert a new list-item into 2.html or 3.html before the footer."""
        with open(index_path, 'r', encoding='utf-8') as f:
            html = f.read()

        # Next INDEX number
        nums = re.findall(r'INDEX_(\d+)', html)
        next_n = max(int(n) for n in nums) + 1 if nums else 1
        idx   = f'INDEX_{next_n:02d}'

        # Date format: 2026.05.07 → 2026/05/07
        date_fmt = date_str.replace('.', '/')

        entry = (
            f'\n            <a href="{href}" class="list-item">\n'
            f'                <div class="item-meta">'
            f'<span>{idx}</span><span>{date_fmt}</span></div>\n'
            f'                <div class="item-title">{title}</div>\n'
            f'            </a>'
        )

        # Inject just before the closing of list-container
        html = html.replace(
            '\n        </div>\n\n        <div class="footer">',
            entry + '\n        </div>\n\n        <div class="footer">'
        )

        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(html)

        return idx

    # ── Publish ───────────────────────────────────────────────────────────────

    def _publish(self):
        if not self.generated:
            messagebox.showwarning("Blog Forge", "请先点击 GENERATE 生成 HTML！")
            return

        title    = self.meta.get('title', 'article')
        date_str = self.meta.get('date', datetime.now().strftime('%Y.%m.%d'))
        default  = re.sub(r'[^\w一-龥]', '_', title)[:40] + '.html'
        category = self.v_category.get()  # "2", "3", or "0"

        path = filedialog.asksaveasfilename(
            title="保存到仓库并发布",
            initialdir=REPO_DIR,
            initialfile=default,
            defaultextension=".html",
            filetypes=[("HTML", "*.html")])
        if not path:
            return

        # Save article HTML
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.generated)

        fname      = os.path.basename(path)
        to_add     = [fname]
        index_note = ""

        # Inject into 2.html or 3.html
        if category in ('2', '3'):
            index_path = os.path.join(REPO_DIR, f'{category}.html')
            try:
                idx = self._inject_index(index_path, fname, title, date_str)
                to_add.append(f'{category}.html')
                index_note = f" + {category}.html ({idx})"
            except Exception as ex:
                messagebox.showerror("Index Error",
                    f"无法写入 {category}.html：\n{ex}")
                return

        self._set_status(f"PUBLISHING  ◆  {fname}{index_note}  →  pushing...")
        self.info_lbl.configure(text="pushing...", fg=GOLD)

        # Capture for thread closure
        _to_add    = list(to_add)
        _note      = index_note
        _fname     = fname

        def _git_push():
            try:
                subprocess.run(['git', 'add'] + _to_add,
                               cwd=REPO_DIR, check=True, capture_output=True)
                subprocess.run(
                    ['git', 'commit', '-m', f'publish: {title}'],
                    cwd=REPO_DIR, check=True, capture_output=True)
                r = subprocess.run(
                    ['git', 'push', 'origin', 'main'],
                    cwd=REPO_DIR, capture_output=True, text=True)

                if r.returncode == 0:
                    self.root.after(0, lambda: self._set_status(
                        f"PUBLISHED  ◆  {_fname}{_note}  →  GitHub  →  CF Pages  ✓"))
                    self.root.after(0, lambda: self.info_lbl.configure(
                        text="✓ published", fg=GREEN))
                else:
                    err = (r.stderr or r.stdout).strip()[:120]
                    self.root.after(0, lambda: self._set_status(
                        f"PUSH FAILED  ◆  {err}"))
                    self.root.after(0, lambda: self.info_lbl.configure(
                        text="push failed", fg=RED))

            except subprocess.CalledProcessError as ex:
                msg = str(ex)[:120]
                self.root.after(0, lambda: self._set_status(
                    f"GIT ERROR  ◆  {msg}"))
                self.root.after(0, lambda: self.info_lbl.configure(
                    text="git error", fg=RED))

        threading.Thread(target=_git_push, daemon=True).start()

    # ── Directory Editor ──────────────────────────────────────────────────────

    def _open_dir_editor(self):
        """Visual editor for 2.html and 3.html directory indexes."""
        win = tk.Toplevel(self.root)
        win.title("★ DIRECTORY EDITOR ★  目录编辑器")
        win.configure(bg=BG)
        win.geometry("960x660")
        win.minsize(720, 480)

        _entries = []          # list of dicts: href, date, title
        _which   = tk.StringVar(value="2")

        # ── helpers ──────────────────────────────────────────────

        def _parse_entries(html_text):
            pat = (r'<a href="([^"]+)" class="list-item">\s*'
                   r'<div class="item-meta"><span>[^<]+</span>'
                   r'<span>([^<]+)</span></div>\s*'
                   r'<div class="item-title">([^<]+)</div>\s*</a>')
            return [{'href': m.group(1), 'date': m.group(2), 'title': m.group(3)}
                    for m in re.finditer(pat, html_text, re.DOTALL)]

        def _sync_vars():
            for e in _entries:
                if '_v_title' in e: e['title'] = e['_v_title'].get()
                if '_v_href'  in e: e['href']  = e['_v_href'].get()
                if '_v_date'  in e: e['date']  = e['_v_date'].get()

        def _set_status(msg, color=DIM):
            status_lbl.configure(text=msg, fg=color)

        def _refresh_rows():
            for w in inner.winfo_children():
                w.destroy()
            for i, entry in enumerate(_entries):
                _build_row(i, entry)
            inner.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _build_row(i, entry):
            row_bg = RAISED if i % 2 == 0 else PANEL
            row = tk.Frame(inner, bg=row_bg)
            row.pack(fill=tk.X, pady=1, padx=2)

            # Index badge
            tk.Label(row, text=f"{i+1:02d}", bg=row_bg, fg=DIM,
                     font=F_XS, width=3).pack(side=tk.LEFT, padx=(6, 2))

            # ▲▼ buttons
            tk.Button(row, text="▲", bg=row_bg, fg=DIM, font=F_XS,
                      relief=tk.FLAT, bd=0, padx=3, pady=2, cursor="hand2",
                      command=lambda idx=i: _move(idx, -1)).pack(side=tk.LEFT)
            tk.Button(row, text="▼", bg=row_bg, fg=DIM, font=F_XS,
                      relief=tk.FLAT, bd=0, padx=3, pady=2, cursor="hand2",
                      command=lambda idx=i: _move(idx, +1)).pack(side=tk.LEFT, padx=(0, 6))

            # Title entry (widest)
            v_title = tk.StringVar(value=entry['title'])
            entry['_v_title'] = v_title
            tk.Entry(row, textvariable=v_title, bg=INPUT, fg=TEXT, font=F_SM,
                     relief=tk.FLAT, insertbackground=GOLD,
                     highlightthickness=1, highlightbackground=BORDER,
                     highlightcolor=GOLD).pack(side=tk.LEFT, fill=tk.X,
                                               expand=True, padx=(0, 4), ipady=3)

            # Href entry (medium)
            v_href = tk.StringVar(value=entry['href'])
            entry['_v_href'] = v_href
            tk.Entry(row, textvariable=v_href, bg=INPUT, fg=TEAL, font=F_XS,
                     relief=tk.FLAT, insertbackground=GOLD,
                     highlightthickness=1, highlightbackground=BORDER,
                     highlightcolor=GOLD, width=26).pack(side=tk.LEFT,
                                                         padx=(0, 4), ipady=3)

            # Date entry (small)
            v_date = tk.StringVar(value=entry['date'])
            entry['_v_date'] = v_date
            tk.Entry(row, textvariable=v_date, bg=INPUT, fg=GOLD, font=F_XS,
                     relief=tk.FLAT, insertbackground=GOLD,
                     highlightthickness=1, highlightbackground=BORDER,
                     highlightcolor=GOLD, width=12).pack(side=tk.LEFT,
                                                          padx=(0, 4), ipady=3)

            # Delete
            tk.Button(row, text="✕", bg=row_bg, fg=RED, font=F_SM,
                      relief=tk.FLAT, bd=0, padx=6, pady=2, cursor="hand2",
                      command=lambda idx=i: _delete(idx)).pack(side=tk.LEFT, padx=(0, 4))

        def _move(idx, delta):
            _sync_vars()
            new_i = idx + delta
            if 0 <= new_i < len(_entries):
                _entries[idx], _entries[new_i] = _entries[new_i], _entries[idx]
                _refresh_rows()

        def _delete(idx):
            _sync_vars()
            removed = _entries.pop(idx)
            _refresh_rows()
            _set_status(f"已删除: {removed['title'][:40]}", RED)

        def _add_entry():
            _sync_vars()
            _entries.append({'href': 'new-article.html',
                             'date': datetime.now().strftime('%Y/%m/%d'),
                             'title': '新条目'})
            _refresh_rows()
            canvas.after(60, lambda: canvas.yview_moveto(1.0))
            _set_status("已添加新条目 · 请填写标题和链接", TEAL)

        def _load_file(which):
            _entries.clear()
            path = os.path.join(REPO_DIR, f"{which}.html")
            if not os.path.isfile(path):
                _set_status(f"⚠ 找不到 {which}.html", RED)
                _refresh_rows()
                return
            with open(path, encoding='utf-8') as f:
                html_text = f.read()
            _entries.extend(_parse_entries(html_text))
            _refresh_rows()
            _update_tabs(which)
            _set_status(f"已加载 {which}.html  ·  {len(_entries)} 条目")

        def _switch_file(which):
            _sync_vars()
            _which.set(which)
            _load_file(which)

        def _update_tabs(which):
            for v, btn in tab_btns.items():
                btn.configure(bg=RAISED if v == which else PANEL,
                              fg=GOLD  if v == which else TEXT)

        def _save():
            _sync_vars()
            which = _which.get()
            path  = os.path.join(REPO_DIR, f"{which}.html")
            with open(path, encoding='utf-8') as f:
                html_text = f.read()

            new_items = ''
            for i, e in enumerate(_entries, 1):
                idx  = f'INDEX_{i:02d}'
                href = e['href'].strip()
                date = e['date'].strip()
                title = e['title'].strip()
                new_items += (
                    f'\n            <a href="{href}" class="list-item">'
                    f'\n                <div class="item-meta">'
                    f'<span>{idx}</span><span>{date}</span></div>'
                    f'\n                <div class="item-title">{title}</div>'
                    f'\n            </a>'
                )

            new_html = re.sub(
                r'(<div class="list-container">)(.*?)'
                r'(</div>\s*\n\s*<div class="footer">)',
                r'\1' + new_items + '\n        </div>\n\n        <div class="footer">',
                html_text, flags=re.DOTALL
            )

            if new_html == html_text:
                _set_status("⚠ 未找到 list-container 区域", RED)
                return

            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_html)
            _set_status(f"✓ 已保存 {which}.html  ·  {len(_entries)} 条目", GREEN)

        # ── Title bar ─────────────────────────────────────────────

        bar = tk.Frame(win, bg=RAISED, height=44)
        bar.pack(fill=tk.X)
        bar.pack_propagate(False)
        tk.Label(bar, text="▓▒░  ★ DIRECTORY EDITOR ★  ░▒▓",
                 bg=RAISED, fg=GOLD, font=F_LG).pack(side=tk.LEFT, padx=12)
        tk.Label(bar, text="可视化目录编辑器",
                 bg=RAISED, fg=TEXT, font=F_SM).pack(side=tk.LEFT)

        # ── File tabs ─────────────────────────────────────────────

        tab_f = tk.Frame(win, bg=PANEL)
        tab_f.pack(fill=tk.X)
        tk.Frame(win, bg=BORDER, height=1).pack(fill=tk.X)

        tab_btns = {}
        for val, label in [("2", "  2.html  ·  理论 / 影评  "),
                            ("3", "  3.html  ·  创作 / 其他  ")]:
            btn = tk.Button(tab_f, text=label, bg=PANEL, fg=TEXT, font=F_SM,
                            relief=tk.FLAT, bd=0, padx=8, pady=7,
                            cursor="hand2", command=lambda v=val: _switch_file(v))
            btn.pack(side=tk.LEFT)
            tab_btns[val] = btn

        # ── Column header ─────────────────────────────────────────

        hdr = tk.Frame(win, bg=RAISED, pady=4)
        hdr.pack(fill=tk.X, padx=10)
        tk.Label(hdr, text="#  ▲▼", bg=RAISED, fg=DIM, font=F_XS,
                 width=8).pack(side=tk.LEFT)
        tk.Label(hdr, text="TITLE / 标题", bg=RAISED, fg=GOLD,
                 font=F_XS).pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(hdr, text="HREF / 链接", bg=RAISED, fg=TEAL,
                 font=F_XS, width=26).pack(side=tk.LEFT)
        tk.Label(hdr, text="DATE", bg=RAISED, fg=GOLD,
                 font=F_XS, width=12).pack(side=tk.LEFT)
        tk.Label(hdr, text="DEL", bg=RAISED, fg=DIM,
                 font=F_XS, width=5).pack(side=tk.LEFT)
        tk.Frame(win, bg=BORDER, height=1).pack(fill=tk.X)

        # ── Scrollable list area ───────────────────────────────────

        list_outer = tk.Frame(win, bg=PANEL)
        list_outer.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        vsb_e = tk.Scrollbar(list_outer, orient=tk.VERTICAL,
                             bg=RAISED, troughcolor=PANEL, activebackground=GOLD)
        vsb_e.pack(side=tk.RIGHT, fill=tk.Y)
        canvas = tk.Canvas(list_outer, bg=PANEL, bd=0, highlightthickness=0,
                           yscrollcommand=vsb_e.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb_e.config(command=canvas.yview)

        inner = tk.Frame(canvas, bg=PANEL)
        win_id = canvas.create_window((0, 0), window=inner, anchor=tk.NW)

        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win_id, width=e.width))
        canvas.bind("<MouseWheel>",
                    lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        # ── Bottom bar ────────────────────────────────────────────

        tk.Frame(win, bg=BORDER, height=1).pack(fill=tk.X)
        bot = tk.Frame(win, bg=RAISED, height=44)
        bot.pack(fill=tk.X, side=tk.BOTTOM)
        bot.pack_propagate(False)

        tk.Button(bot, text="＋ ADD ENTRY", bg=GREEN, fg=BG, font=F_SM,
                  relief=tk.FLAT, bd=0, padx=12, pady=5, cursor="hand2",
                  command=_add_entry).pack(side=tk.LEFT, padx=(8, 4), pady=6)
        tk.Button(bot, text="▲ SAVE FILE", bg=RED, fg=TEXT, font=F_SM,
                  relief=tk.FLAT, bd=0, padx=12, pady=5, cursor="hand2",
                  command=_save).pack(side=tk.RIGHT, padx=(4, 8), pady=6)

        status_lbl = tk.Label(bot, text="", bg=RAISED, fg=DIM, font=F_XS)
        status_lbl.pack(side=tk.LEFT, padx=8)

        # ── Initial load ──────────────────────────────────────────
        _load_file("2")


# ── Entry ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    BlogForge()
