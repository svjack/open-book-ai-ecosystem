"""
Pipeline v3: 整章拆分 + 并行 API 翻译
"""
import zipfile, os, re, time, sys, math, json
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI

API_KEY = "sk-e85d7c7c33cd482b92c1531da27a5d3d"
MODEL = "deepseek-v4-flash"
MAX_TOKENS = 32768
PARALLEL = 4          # 并行API调用数
CHUNK_TARGET = 2500   # 每块目标字节数
TEMPERATURE = 0

BOOKS_DIR = "/Users/svjack/temp/open-book-ai-ecosystem/books"
OUT_DIR = "/Users/svjack/temp/open-book-ai-ecosystem/books/taejong_output"
EPUB_PATH = "/Users/svjack/temp/open-book-ai-ecosystem/books/太宗实录_白话文版.epub"

def find_source_epub():
    for f in os.listdir(BOOKS_DIR):
        if "50b42aa847d2cdcc7ffdf712e92269d0" in f:
            return os.path.join(BOOKS_DIR, f)
    raise FileNotFoundError("Source EPUB not found")
EPUB_SRC = find_source_epub()

SECTIONS = {
    28: "太宗 4年", 29: "太宗 5年", 30: "太宗 6年",
    31: "太宗 7年", 32: "太宗 8年", 33: "太宗 9年",
    34: "太宗 10年", 35: "太宗 11年", 36: "太宗 12年",
    37: "太宗 13年", 38: "太宗 14年", 39: "太宗 15年",
    40: "太宗 16年",
}

SYSTEM_PROMPT = """你是一个文言文→白话文翻译助手。翻译朝鲜王朝实录的文言文段落。

规则：
1. 保留所有 XHTML 标签（<h2>, <p> 等）不变
2. 日期头「太宗 X年 X月 X日(干支)」→ 去掉干支
3. 每个 <p>○...内容...</p> 翻译成白话，去掉○，保留<p>标签
4. 人名官名地名保留
5. 天文现象自然表达
6. 只返回翻译后的 XHTML 片段，不要额外说明"""


def get_body(section_num):
    z = zipfile.ZipFile(EPUB_SRC, 'r')
    fname = f"Section{section_num:04d}.xhtml"
    content = z.read(f'OEBPS/Text/{fname}').decode('utf-8')
    z.close()
    body = re.search(r'<body>(.*?)</body>', content, re.DOTALL)
    return body.group(1) if body else ''


def chunk_body(body):
    """按目标字节大小拆分，保证在 <p> 边界处断开"""
    lines = body.split('\n')
    chunks = []
    current = []
    size = 0
    for line in lines:
        current.append(line)
        size += len(line)
        if size >= CHUNK_TARGET and line.strip().startswith('<p>太宗'):
            chunks.append('\n'.join(current))
            current = []
            size = 0
    if current:
        chunks.append('\n'.join(current))
    return chunks


def translate_one_chunk(chunk, idx, total):
    """调用 API 翻译一个 chunk"""
    chunk_clean = chunk.replace('<body>', '').replace('</body>', '')

    for attempt in range(3):
        try:
            client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com/v1")
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"翻译：\n{chunk_clean}"}
                ],
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
            )
            result = resp.choices[0].message.content or ""
            if result.strip():
                return result
        except Exception as e:
            print(f"    ⚠️ 重试 {attempt+1}/3: {e}")
            time.sleep(3)
    return None


def translate_section(section_num):
    label = SECTIONS[section_num]
    fname = f"Section{section_num:04d}.xhtml"
    print(f"\n{'='*50}\n{label} ({fname})", flush=True)

    body = get_body(section_num)
    chunks = chunk_body(body)
    print(f"  拆分为 {len(chunks)} 块 (每块 ~{CHUNK_TARGET}B)", flush=True)

    results = {}
    with ThreadPoolExecutor(max_workers=PARALLEL) as pool:
        fut_map = {}
        for i, chunk in enumerate(chunks):
            fut = pool.submit(translate_one_chunk, chunk, i+1, len(chunks))
            fut_map[fut] = i

        done = 0
        for fut in as_completed(fut_map):
            idx = fut_map[fut]
            res = fut.result()
            if res:
                results[idx] = res
            else:
                print(f"    ❌ 块 {idx+1} 失败，用原文", flush=True)
                results[idx] = chunks[idx]
            done += 1
            print(f"  进度: {done}/{len(chunks)}", flush=True)

    # 按原始顺序拼接
    body_parts = []
    for i in range(len(chunks)):
        r = results.get(i, chunks[i])
        r = r.replace('<body>', '').replace('</body>', '')
        body_parts.append(r)
    translated_body = '\n'.join(body_parts)

    xhtml = f'''<?xml version='1.0' encoding='utf-8'?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
  <title></title>
  <link href="../Styles/Style0001.css" type="text/css" rel="stylesheet"/>
</head>
<body>
{translated_body}
</body>
</html>'''

    out_path = os.path.join(OUT_DIR, f'OEBPS/Text/{fname}')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(xhtml)

    # === XHTML 后处理：修复 API 输出的语法问题 ===
    # 1. <br> → <br/>
    xhtml = xhtml.replace('<br>', '<br/>').replace('</br>', '')
    # 2. 裸文本行（无 <p> 包裹但有 <br/>）→ 用 <p> 包裹
    body_match = re.search(r'<body>(.*?)</body>', xhtml, re.DOTALL)
    if body_match:
        b = body_match.group(1)
        lines = b.split('\n')
        fixed = []
        for line in lines:
            s = line.strip()
            if s and not s.startswith('<') and '<br/>' in s:
                fixed.append(f'<p>{s}</p>')
            else:
                fixed.append(line)
        new_b = '\n'.join(fixed)
        xhtml = xhtml.replace(b, new_b)
    # 3. 平衡 <p> / </p> 标签
    body_match = re.search(r'<body>(.*?)</body>', xhtml, re.DOTALL)
    if body_match:
        b = body_match.group(1)
        opens = b.count('<p>')
        closes = b.count('</p>')
        if opens > closes:
            xhtml = xhtml.replace('</body>', '</p>' * (opens - closes) + '\n</body>')
        elif closes > opens:
            xhtml = xhtml.replace('<body>', '<body>\n' + '<p>' * (closes - opens))

    # 统计翻译比例
    orig_p = body.count('<p>')
    new_p = xhtml.count('<p>')
    print(f"  写入: {fname} ({len(xhtml)}B, <p>: {new_p}/{orig_p})", flush=True)


def build_epub():
    if os.path.exists(EPUB_PATH):
        os.remove(EPUB_PATH)
    with zipfile.ZipFile(EPUB_PATH, 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(os.path.join(OUT_DIR, 'mimetype'), 'mimetype', compress_type=zipfile.ZIP_STORED)
        for root, dirs, files in os.walk(OUT_DIR):
            for file in files:
                if file == 'mimetype':
                    continue
                z.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), OUT_DIR))
    print(f"\n✅ EPUB: {EPUB_PATH} ({os.path.getsize(EPUB_PATH)/1024:.0f}KB)")


if __name__ == '__main__':
    start_all = time.time()
    for sn in sorted(SECTIONS.keys()):
        t0 = time.time()
        translate_section(sn)
        print(f"  耗时: {time.time()-t0:.0f}秒", flush=True)
    build_epub()

    elapsed = time.time() - start_all
    print(f"总耗时: {elapsed:.0f}秒 ({elapsed/60:.1f}分钟)")

    with zipfile.ZipFile(EPUB_PATH, 'r') as z:
        assert z.read('mimetype') == b'application/epub+zip'
        sections = sorted([n for n in z.namelist() if 'Section' in n and n.endswith('.xhtml')])
        print(f"章节: {len(sections)}")
        for s in sections:
            print(f"  {s.split('/')[-1]:25s} {len(z.read(s)):>7,}B")
        print("✅ 验证通过")
