# 太宗实录·白话文翻译管线

## 概述

将《朝鲜王朝实录·太宗实录》原文（文言文）逐章翻译为现代白话文，输出为 EPUB 格式。

**翻译规模：** 太宗16年记录，约 **123万字白话文**  
**翻译方式：** DeepSeek V4 Flash API（`deepseek-v4-flash`）  
**原文来源：** 春秋馆史官编《朝鲜王朝实录》（81.5MB EPUB）

## 目录结构

```
open-book-ai-ecosystem/
├── books/                          # 书目文件
│   ├── 朝鲜王朝实录 ... .epub      # 原文 EPUB
│   ├── 太宗实录_白话文版.epub      # 翻译结果 EPUB
│   └── taejong_output/            # 翻译输出（解包状态，可重新打包）
├── pipeline/                       # 翻译工具
│   └── translate_pipeline_v3.py    # 最终翻译脚本
├── TRANSLATION_NOTE.md             # 翻译方法记录
└── README.md                       # 本文件
```

## 使用方式

### 环境要求

```bash
pip install openai
```

### 配置

脚本内已配置 API Key 和模型：

```python
API_KEY = "sk-e85d7c7c33cd482b92c1531da27a5d3d"
MODEL = "deepseek-v4-flash"
BASE_URL = "https://api.deepseek.com/v1"
```

### 运行

```bash
cd open-book-ai-ecosystem
python3 pipeline/translate_pipeline_v3.py
```

脚本会自动：
1. 读取 books/ 下的原文 EPUB
2. 按章节拆分大段正文
3. 每块约 2500 字节，4路并行调用 API
4. 拼接翻译结果 → XHTML → EPUB

### 单章翻译（调试用）

```python
from pipeline.translate_pipeline_v3 import translate_section, build_epub
translate_section(28)  # 翻译太宗4年
build_epub()
```

## 翻译流程

```
原文 EPUB (81.5MB)
  │  zipfile 读取
  ▼
19 个 XHTML 章节
  │  re 提取 <body>
  ▼
按 ~2500B 拆分为多块
  │  ThreadPoolExecutor(4) 并行
  ▼
DeepSeek V4 Flash API
  │  system prompt + few-shot 样本
  │  temperature=0, max_tokens=32768
  ▼
翻译后 XHTML 片段
  │  XHTML 后处理修复:
  │  1. <br> → <br/>
  │  2. 裸文本行 <p> 包裹
  │  3. <p>/</p> 平衡
  ▼
19 个 XHTML 文件
  │  zipfile
  ▼
白话文版 EPUB
```

## 翻译质量

| 部分 | 章节 | 方式 | 字数 |
|------|------|------|------|
| 总序/附录/标题 | S04/S24/S41 | 手动 | ~1,300 |
| 太宗1~3年 | S25-S27 | 手动逐条 | ~40,500 |
| 太宗4~16年 | S28-S40 | **API 翻译** | **~1,186,000** |
| **合计** | **19章** | | **~1,228,000** |

### 标签覆盖率

API 翻译章节的 `<p>` 标签保留率 > 95%。

## 参考样本（Few-shot）

脚本内置以下对照样本用于稳定翻译质量：

# 翻译管线 README
