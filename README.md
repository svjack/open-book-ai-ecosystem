# 开放图书馆 EPUB 下载方案 & 调研报告

> **核心**: 使用 cmux 浏览器（macOS 终端内置浏览器）配合 Anna's Archive + LibGen 完成下载  
> **记录日期**: 2026-06-23 | **最后更新**: 2026-06-24  
> **目标**: 调研 Z-Library 替代方案、无限制 EPUB 下载平台、Anna's Archive 使用及下载方法

---

## 快速开始：标准下载流程（cmux 浏览器）

以下流程是验证过最可靠的下载方式。只需 cmux 浏览器（macOS 终端内），无需 curl、Python 脚本或 Calibre。

### 场景 A：LibGen 上存在的书目（推荐，最简单）

```bash
# 1. 在 Anna's Archive 搜索，加 &src=lgli 只显示 LibGen 源的书籍
cmux --json browser open \
  "https://annas-archive.gl/search?q={书名}&src=lgli&lang=zh" \
  --workspace "${CMUX_WORKSPACE_ID}"

# 2. 点击目标书籍进入详情页，地址栏中提取 /md5/{32位md5}

# 3. 在 cmux 浏览器中打开 LibGen 直连页
cmux browser surface:N goto \
  "https://libgen.li/ads.php?md5={md5}"

# 4. 点击页面上唯一的 "GET" 按钮 → 文件自动下载到 ~/Downloads/
```

✅ DDoS-Guard 由浏览器自动处理  
✅ LibGen 无防护，无需任何登录  
✅ 文件直达 `~/Downloads/`（不显示在 `cmux browser download list` 中）  
✅ EPUB / PDF / MOBI 等格式均可

> **实测**: 以《李朝实录 第二册 太宗实录 第一》(`md5=b078a17ec2...`) 为例，打开 ads.php → 点击 GET → 17MB PDF 自动下载完成。

### 场景 B：Z-Library 独占书目（通过 Anna's Archive 下载通道）

```bash
# 1. 搜索（不加 &src=lgli，让所有来源都出现）
cmux --json browser open \
  "https://annas-archive.gl/search?q={书名}&lang=zh" \
  --workspace "${CMUX_WORKSPACE_ID}"

# 2. 点击结果进入 MD5 详情页

# 3. 在 "browser verification" 区域点击 Slow Partner Server #1
#    浏览器自动通过 DDoS-Guard JS 质询

# 4. 在跳转后的页面点击 "📚 Download now"
#    → 文件自动下载到 ~/Downloads/
```

> ⚠️ **注意**: 下载由浏览器后台完成，`cmux browser download list` 可能检测不到。**直接检查 `~/Downloads/`** 即可找到文件。

> **实测**: 以《朝鲜王朝实录》(`md5=50b42aa8...`) 为例，curl 返回 429，浏览器点击后 **81MB EPUB 成功下载**。浏览器内置 cookie 管理绕过了 CDN 限速。

### 完整示意图

```
┌─ 场景 A: LibGen 存在 ───────────────────────┐
│                                               │
│  AA 搜索 (&src=lgli) ──→ libgen.li/ads.php   │
│       │                       │               │
│  DDoS-Guard              无防护                │
│  浏览器自动过              GET 按钮点击         │
│       │                       │               │
│       └──── 提取 md5 ────────┘               │
│                                │               │
│                           ~/Downloads/         │
├─ 场景 B: Z-Library 独占 ─────────────────────┐
│                                               │
│  AA 搜索 ──→ /md5/{md5} 详情页                │
│       │                       │               │
│  DDoS-Guard            Slow Partner Server     │
│  浏览器自动过          浏览器自动过 DDoS-Guard  │
│       │                       │               │
│       └── 点击 "Download now" ─┘               │
│                                │               │
│                           ~/Downloads/         │
└───────────────────────────────────────────────┘
```

### 常见问题

**Q: 怎么获取 cmux 浏览器 surface 编号？**  
每次 `cmux --json browser open` 返回的 JSON 中有 `surface_ref`，如 `surface:5`。之后所有操作使用 `cmux browser surface:5 <命令>`。

**Q: 搜索时没反应？**  
首次访问 `.gl` 域名可能需要几秒钟加载 DDoS-Guard 质询，等待 `wait --load-state complete` 后再操作。

**Q: LibGen ads.php 页面没有 "GET" 按钮？**  
说明该 md5 **不在 LibGen 上**（只会出现在 Z-Library/upload 源）。切换到场景 B。

---

## 目录

1. [快速开始：标准下载流程（cmux 浏览器）](#快速开始标准下载流程cmux-浏览器)
2. [Z-Library 现状](#2-z-library-现状)
3. [GitHub 上的 Z-Library 相关项目](#3-github-上的-z-library-相关项目)
4. [zlibrary.koplugin 源码分析](#4-zlibrarykoplugin-源码分析)
5. [免费 EPUB 下载平台对比](#5-免费-epub-下载平台对比)
6. [核心项目: a-peirogon/cal-annas](#6-核心项目-a-peirogoncal-annas)
7. [Anna's Archive 深度分析](#7-annas-archive-深度分析)
8. [Anna's Archive 藏书验证](#8-annas-archive-藏书验证)
9. [绕过 DDoS-Guard 的下载方案](#9-绕过-ddos-guard-的下载方案)
10. [AI EPUB 阅读器对比](#10-ai-epub-阅读器对比)
11. [iOS/iPadOS 开源 AI EPUB 阅读器](#11-iosipados-开源-ai-epub-阅读器)
12. [Apple Intelligence 端侧 AI 架构与限制](#12-apple-intelligence-端侧-ai-架构与限制)
13. [实际下载验证](#13-实际下载验证)
14. [总结与推荐](#14-总结与推荐)

---

## 2. Z-Library 现状

### 1.1 下载限制
- 普通用户每日有下载数量限制（通常 5-10 本/天）
- 注册账户或捐赠后可获得更多额度
- 访问域名经常变动，需通过官方渠道获取最新地址

### 1.2 书目格式
- 不全是 EPUB 版本
- 常见格式包括: PDF、ePub、MOBI、AZW3 等
- 格式取决于上传者提供的原始文件

---

## 3. GitHub 上的 Z-Library 相关项目

### 2.1 热门项目一览 (按 Stars 排序)

| Stars | 项目 | 说明 | 最后推送 |
|-------|------|------|---------|
| ⭐2602 | runningcheese/Awesome-Zlibrary | Z-Library 资源汇总 | 2023-02-17 |
| ⭐2384 | dstark5/Openlib | 基于 Shadow Library 的开源下载/阅读 App (iOS) | 2026-01-18 |
| ⭐1648 | zstmfhy/zlibrary-to-notebooklm | 自动下载并上传到 Google NotebookLM | 2026-01-17 |
| ⭐1563 | z-libraryopp/z-libraryopp.github.io | 官方镜像入口汇总页 | 2026-05-05 |
| ⭐444 | ZlibraryKO/zlibrary.koplugin | KOReader 插件 — 在电子墨水屏阅读器上使用 Z-Library | 2026-06-23 |
| ⭐434 | sertraline/zlibrary | 非官方 Z-Library API | 2025-04-12 |
| ⭐362 | NubPlayz/GoodLib-Zlib-Goodreads-extension | Goodreads 浏览器扩展 | 2026-04-21 |
| ⭐336 | khanhas/zshelf | reMarkable 平板客户端 | 2021-11-29 |

### 2.2 两个仍在积极维护的项目

#### z-libraryopp/z-libraryopp.github.io
- **目的**: Z-Library 官方镜像导航页，汇总可用入口
- **技术栈**: 纯 HTML，部署在 GitHub Pages
- **部署地址**: https://z-libraryopp.github.io/
- **内容**: 镜像网址、桌面端/Android 客户端下载链接、其他电子书资源入口

#### ZlibraryKO/zlibrary.koplugin
- **目的**: KOReader 的 Z-Library 插件，在电子墨水屏阅读器上搜索、浏览、下载书籍
- **技术栈**: Lua (KOReader 插件)
- **最新版本**: v1.0.33 (2026-05-18)
- **特性**: 搜索、筛选、热门推荐、直接下载

---

## 4. zlibrary.koplugin 源码分析

### 3.1 下载限制处理机制

源码文件: `zlibrary/api.lua`

该插件**并未尝试绕过 Z-Library 的下载限制**，而是采取了以下策略：

#### 限额检测 (api.lua)
```lua
-- 检测 "Download limit reached" 错误
if string.find(error_str, "Download limit reached", 1, true) ~= nil then
    return true  -- 触发重新登录重试
end
```

```lua
-- 下载返回 HTML 而非文件 → 判定为达到限制
if content_type and string.find(string.lower(content_type), "text/html") then
    result.error = T("Download limit reached or file is an HTML page")
end
```

#### 配额状态查询 (api.lua)
```lua
-- 调用 /eapi/user/profile 获取今日下载数/限额
function Api.getDownloadQuotaStatus(user_id, user_key)
    return { quota_status = {
        today = data.user.downloads_today,
        limit = data.user.downloads_limit
    }}
end
```

#### 配额缓存与展示 (main.lua)
- `validateDownloadQuota()` 获取配额并缓存 3 小时
- 在"My Books"界面显示 `[已下载/限额]` 如 `[3/10]`
- 成功下载后调用 `resetDownloadQuotaCache()` 清除缓存

### 3.2 结论
插件完全遵循服务端限制，仅有 "Test Mode"（本地模拟下载成功，用于开发调试）。

---

## 5. 免费 EPUB 下载平台对比

### 4.1 综合对比表

| 平台/来源 | 藏书量(近似) | 下载限制 | GitHub 工具 | Stars | 最近推送 | 语言 |
|----------|------------|---------|------------|-------|---------|------|
| **Standard Ebooks** | ~1,000 精校公版 | ❌ 无 | `tamnd/stdebooks-cli` | ⭐0 | 2026-06-20 | Go |
| **Project Gutenberg** | ~72,000 公版 | ❌ 无 | `dictvm/gutenberg-epub-downloader` | ⭐2 | 2023-05-14 | Python |
| **Open Library** | ~3,000,000 借阅 | ⚠️ 借阅+速率限制 | 网页直接 | — | — | — |
| **LibGen** | ~3,500,000 | ❌ 无硬性限制 | `costis94/bookcut` | ⭐196 | 2022-02-12 | Python |
| **Anna's Archive** | **~30,000,000+** 聚合 | ⚠️ 速率限制(无日配额) | `dstark5/Openlib` | ⭐2,384 | 2026-01-18 | Dart |
| | | | `justrals/KindleFetch` | ⭐286 | 2026-03-04 | Shell |
| | | | `warreth/OpenlibExtended` | ⭐393 | 2026-03-04 | Dart |
| | | | `a-peirogon/cal-annas` | ⭐10 | **2026-06-21** | Python |
| | | | `billmal071/bookdl` | ⭐15 | 2026-04-29 | Go |

### 4.2 各平台特点

#### Standard Ebooks
- 高质量精校公版书籍
- 完全无限制下载
- 藏书量较小但品质极高
- GitHub 工具: `tamnd/stdebooks-cli` (Go)

#### Project Gutenberg
- 最大的公版书库
- 完全无限制
- 70,000+ 免费电子书
- GitHub 工具: `dictvm/gutenberg-epub-downloader`

#### Open Library (Internet Archive)
- 数百万册可借阅
- 借阅制，非无限制下载
- 可直接在浏览器阅读

#### Library Genesis (LibGen)
- 约 350 万册书籍
- 无硬性下载限制
- 界面较简陋但功能完整
- GitHub 工具: `costis94/bookcut` (Python CLI)

#### Anna's Archive
- **最大**: 6,400 万+ 书籍 + 9,500 万+ 论文
- 聚合 LibGen、Z-Library、Sci-Hub
- 有速率限制但无每日固定配额
- 数据完全开源，可通过 Torrent 批量下载
- 需处理 DDoS-Guard 防护

---

## 6. 核心项目: a-peirogon/cal-annas

### 5.1 项目概述

此项目是本调研的**核心源头项目** — 一个 Calibre 商店插件，用于从 Anna's Archive 搜索和下载图书。

- **GitHub**: https://github.com/a-peirogon/cal-annas
- **Stars**: ⭐10
- **语言**: Python
- **最近推送**: 2026-06-21
- **许可证**: GPL-3.0

```python
# 源码: annas_archive.py — 约 1251 行
# 核心模块:
#   annas_archive.py  — Calibre 商店插件主逻辑（搜索 + 下载拦截器）
#   config.py         — Qt 配置界面（镜像管理、搜索过滤）
#   constants.py      — 默认镜像、缓存实现、搜索选项定义
```

### 5.2 搜索结果解析

*`a-peirogon/cal-annas/annas_archive.py`*

插件通过以下方式从 Anna's Archive 搜索页面提取结果:

```python
# 提取 MD5 (line 422-431)
@staticmethod
def _extract_md5(result_div) -> Optional[str]:
    links = result_div.xpath('.//a[starts-with(@href, "/md5/")]/@href')
    if links:
        md5 = links[0].split('/')[-1].split('?')[0].split('#')[0]
        return md5 or None
```

```python
# 提取标题 — 4 种回退策略 (line 433-479)
@staticmethod
def _extract_title(result_div) -> Optional[str]:
    # Strategy 1: js-vim-focus 锚点链接
    # Strategy 2: fallback cover div 中的 data-content
    # Strategy 3: 任意 data-content div
    # Strategy 4: 任意 md5 锚点文本
```

```python
# 提取作者 (line 481-504)
@staticmethod
def _extract_author(result_div, title: str) -> str:
    # Strategy 1: fallback cover div 的第二个 data-content
    # Strategy 2: icon-based 作者链接 (mdi--user-edit)
    # Strategy 3: 与标题不同的任意 data-content
```

```python
# 提取格式 (line 506-536)
@staticmethod
def _extract_formats(result_div) -> str:
    # 优先短标签元素 (≤6 字符, 如 EPUB/PDF/MOBI)
    # 回退: 前 200 字符全文匹配
    # 支持: EPUB, PDF, MOBI, AZW3, CBR, CBZ, FB2, DJVU, TXT
```

```python
# 提取文件大小 (line 658-668)
@staticmethod
def _extract_size(result_div) -> Optional[str]:
    text = ' '.join(result_div.xpath('.//text()'))
    m = _SIZE_RE.search(text)  # 匹配 "3.2 MB" 等模式
```

搜索结果类 (`SearchResult`) 包含:
- `detail_item` → MD5 hash（用于后续下载）
- `title` → 书名（附带文件大小标注）
- `author` → 作者
- `formats` → 所有格式（逗号分隔）
- `cover_url` → Google Books ISBN 封面或 Qt 生成的本地缩略图
- `price` → 固定为 `$0.00`
- `drm` → `DRM_UNLOCKED`

### 5.3 镜像管理与 SLUM 集成

插件使用 **SLUM**（Shadow Library Uptime Monitor, https://open-slum.org）实时监控各镜像可用性:

```python
# constants.py (line 35-42)
DEFAULT_MIRRORS = [
    'https://annas-archive.gl',
    'https://annas-archive.pk',
    'https://annas-archive.gd',
]

# SLUM 端点 (line 99-100)
_SLUM_PAGE_API = 'https://open-slum.org/api/status-page/shadow-libraries'
_SLUM_HB_API   = 'https://open-slum.org/api/status-page/heartbeat/shadow-libraries'
```

```python
# 镜像健康检查 (line 307-336)
@staticmethod
def _check_mirror_health(mirror: str, timeout: int = 5) -> bool:
    # HTTP HEAD 请求验证连通性
    # 结果缓存 5 分钟 (TTLCache)
    # 4xx = Cloudflare 质询但主机在线（视为健康）
```

```python
# 镜像选择策略 (line 338-376)
def _select_working_mirror(self, mirrors: List[str]) -> str:
    # 优先级:
    # 1. 上次工作的镜像（加速重复搜索）
    # 2. SLUM 报告为 UP 的镜像
    # 3. SLUM 未知的镜像
    # 4. SLUM 报告为 DOWN 的镜像
```

### 5.4 下载功能 — create_browser() 核心下载拦截器

**这是全书目下载的入口**。Calibre 在用户点击下载按钮时调用此方法。

```python
# annas_archive.py (line 1114-1240)
def create_browser(self):
    """
    当 Calibre 准备下载时调用。
    拦截 slow_download URL 并按以下顺序解析:

    Step 1 — 从 /md5/ 页面提取直接下载链接
             尝试所有 SLUM 报告为 UP 的 Libgen 镜像 + Sci-Hub
             
    Step 2 — 回退: follow slow_download redirect
             跟随 Anna's Archive 的 HTTP 重定向到 CDN
    """
```

#### Step 1: 直接链接提取

```python
# line 1156-1194
# 1. 获取 SLUM 活跃的 Libgen 镜像列表
libgen_mirrors = plugin_self._active_libgen_mirrors()

# 2. 获取 /md5/{md5} 页面
with closing(br.open(f'{primary}/md5/{md5}', timeout=20)) as f:
    doc = html.fromstring(f.read())

# 3. 提取所有外部下载链接
ext_links = doc.xpath(
    '//a[starts-with(@href,"http") and ('
    'contains(@href,"libgen") or contains(@href,"sci-hub"))]'
)
```

#### 各来源链接提取

**LibGen.li** (`_get_libgen_li_link`, line 1060-1071):
```python
# 打开 LibGen 页面 → 查找 "GET" 按钮的 href
with closing(br.open(url)) as resp:
    doc    = html.fromstring(resp.read())
    parsed = urlparse(resp.geturl())
    base   = f'{parsed.scheme}://{parsed.netloc}'
href = ''.join(doc.xpath('//a[h2[text()="GET"]]/@href'))
return f'{base}/{href.lstrip("/")}'
```

**LibGen.rs** (`_get_libgen_rs_link`, line 1073-1081):
```python
# 打开 LibGen 页面 → 查找 h2/a[text()="GET"] 的 href
with closing(br.open(url)) as resp:
    doc = html.fromstring(resp.read())
return ''.join(doc.xpath('//h2/a[text()="GET"]/@href'))
```

**Sci-Hub** (`_get_scihub_link`, line 1083-1094):
```python
# 打开 Sci-Hub 页面 → 查找 embed#pdf 的 src
with closing(br.open(url)) as resp:
    doc    = html.fromstring(resp.read())
pdf_url = ''.join(doc.xpath('//embed[@id="pdf"]/@src'))
```

**Z-Library** (`_get_zlib_link`, line 1096-1108):
```python
# 打开 Z-Library 页面 → 查找 addDownloadedBook 链接
href = ''.join(doc.xpath('//a[contains(@class,"addDownloadedBook")]/@href'))
```

#### Step 2: slow_download 回退

```python
# line 1206-1231
for mirror in mirrors:
    slow_url = f'{mirror}/slow_download/{md5}/0/0'
    with closing(br.open(slow_url, timeout=30)) as resp:
        final_url    = resp.geturl()
        content_type = resp.info().get_content_type()
    
    aa_netloc = urlparse(mirror).netloc
    redirected_away = urlparse(final_url).netloc != aa_netloc
    is_file_download = content_type.startswith('application/')
    
    if redirected_away or is_file_download:
        # 成功获取到文件
        return original_open(final_url, *args, **kwargs)
```

### 5.5 get_details() — 非阻塞式下载注册

```python
# line 979-1004
def get_details(self, search_result: SearchResult, timeout: int = 15):
    # 注册 slow_download 占位符（不发起 HTTP 请求）
    slow_url = f'{mirror}/slow_download/{search_result.detail_item}/0/0'
    search_result.downloads[f"Anna's Archive.{fmt}"] = slow_url
    
    # 后台线程预热 cookies
    threading.Thread(
        target=self._prewarm_cookies,
        args=(mirror,), daemon=True
    ).start()
```

### 5.6 下载流程图

```
用户搜索 → Anna's Archive 搜索页面 → 解析结果 (md5 + 元数据)
                      │
用户点击下载 → get_details() 注册 slow_download URL (非阻塞)
                      │
                 create_browser() → 拦截器 intercepting_open()
                      │
              ┌───────┴───────┐
              ▼               ▼
      Step 1: /md5/ 页面    Step 2: slow_download
      提取外部下载链接        HTTP 重定向跟随
              │               │
      ┌───────┼───────┐       │
      ▼       ▼       ▼       ▼
  LibGen  Sci-Hub  Z-Lib   AA CDN
      │       │       │       │
      └───────┴───────┴───────┘
              │
              ▼
          文件下载成功
```

### 5.7 关键数据结构: 源码中定义的搜索选项

来源: `constants.py` — 支持以下过滤维度:

| 选项 | URL 参数 | 值示例 |
|------|---------|--------|
| Order | `sort` | `newest`, `largest`, `random` |
| Content | `content` | `book_fiction`, `book_comic` |
| Access | `acc` | `aa_download`, `torrents_available` |
| FileType | `ext` | `epub`, `pdf`, `mobi` |
| Source | `src` | `lgli`(LibGen), `zlib`, `ia`(Internet Archive) |
| Language | `lang` | `zh`, `en`, `ja` (60+ 语言) |

### 5.8 与 KindleFetch 方案对比

| 特性 | cal-annas | KindleFetch |
|------|----------|------------|
| 下载源 | LibGen → Sci-Hub → slow_download (3 级回退) | LibGen 仅 |
| 镜像发现 | SLUM 实时监控 + 健康检查 | 硬编码列表 + find_working_url |
| LibGen 解析 | 解析 "GET" 按钮链接 | 解析 get.php 链接 |
| 多格式支持 | 完整 (EPUB, PDF, MOBI, AZW3 等) | 依赖搜索返回 |
| 缓存 | TTL-based (搜索结果 + 镜像健康) | 无 |
| CAPTCHA 处理 | 浏览器头部模拟 + cookie 预热 | 无特别处理 |

### 5.9 本报告源码参考

以下分析基于本地克隆仓库:
```
/Users/svjack/temp/cal-annas/
├── annas_archive.py   (1251 行 — 主逻辑)
├── config.py           (403 行 — Qt 配置界面)
├── constants.py        (241 行 — 常量 + 缓存)
├── __init__.py         (728 字节 — 插件入口)
└── README.md           (37 行)
```


## 7. Anna's Archive 深度分析

> 注: 本节及后续章节基于 [a-peirogon/cal-annas](#5-核心项目-a-peirogoncal-annas) 项目的代码分析和实际验证。

### 7.1 访问方式

| 方式 | 地址 | 说明 |
|------|------|------|
| 主站 | `https://annas-archive.org` | 需代理/Tor 访问 |
| 镜像站(已验证) | `https://annas-archive.gl` | DDoS-Guard 防护 |
| 镜像站 | `https://annas-archive.pk` | — |
| 镜像站 | `https://annas-archive.gd` | — |
| 博客 | `https://annas-blog.org` | 状态更新和公告 |
| Tor 隐藏服务 | `annas-archive.li` | 需 Tor 浏览器 |

### 7.2 首页分析 (`annas-archive.gl`)

- **标题**: "Anna's Archive: LibGen, Sci-Hub, Z-Library in one place"
- **服务商**: DDoS-Guard (JS 质询防护)
- **域名别名**: `annas-archive.gl`, `annas-archive.pk`, `annas-archive.gd`
- **功能入口**: 搜索、捐赠、🧬 SciDB（科学论文数据库）
- **多语言支持**: 60+ 语言

### 7.3 llms-txt.html 分析

博客文章: **"If you're an LLM, please read this"** (2026-02-18)

核心内容:
1. **数据完全开源** — 所有代码和元数据在 GitLab (`software.annas-archive.gl`)
2. **批量下载方式**:
   - 元数据和全文 → Torrents 页面 (`/torrents`)
   - Torrent 程序化下载 → JSON API (`/dyn/torrents.json`)
   - 单文件下载 → 捐赠后使用 API
3. **明文邀请 LLM/爬虫** 使用其数据训练，并呼吁捐赠支持

---

## 8. Anna's Archive 藏书验证

### 8.1 中文轻小说搜索结果

| 搜索关键词 | 结果数 | 中文条目 | 代表作品 |
|----------|-------|---------|---------|
| 轻小说 | 500+ | 大量 | 物语系列、幼女战记、义妹生活、魔女之旅 |
| 刀剑神域 | 455 | 53 | 进击篇、幽灵子弹、官方同人志 |
| 无职转生 | 192 | 53 | 全卷中文翻译 |
| 关于我转生 | 198 | 53 | 转生史莱姆全系列 |
| 间谍过家家 | 16 | 35 | 卷1-10 中文版 |
| 葬送的芙莉莲 | 24 | 36 | 话36-110 中文翻译 |

**来源**: 迷糊轻小说(yidm.com)、台湾角川、东立出版社、cj5、epub掌上书苑
**格式**: EPUB 为主，也有 PDF、MOBI、AZW3

### 8.2 古代中文文本搜索结果

| 典籍 | 总结果 | 中文条目 | 说明 |
|------|-------|---------|------|
| 论语 | 500+ | 43 | 多个版本/注释本 |
| 道德经 | 500+ | 41 | 含英译本 |
| 史记 | 500+ | 37 | 含中华书局等版本 |
| 红楼梦 | 500+ | 44 | 含脂评本等 |
| 三国演义 | 500+ | 49 | 各版本 |
| 资治通鉴 | 500+ | 36 | 含 EPUB |
| 诗经 | 500+ | 45 | EPUB 丰富 |
| 楚辞 | 500+ | 37 | EPUB 11 |
| 全唐诗 | 500+ | 38 | EPUB 11 |
| 孙子兵法 | 500+ | 49 | 中英对照 |
| 黄帝内经 | 500+ | 43 | 医学经典 |
| 周易 | 500+ | 44 | 多个注本 |
| 山海经 | 500+ | 46 | PDF 为主 |
| 说文解字 | 500+ | 42 | 字书 |
| 四库全书 | 500+ | 29 | 大部头 |
| 古文观止 | 500+ | 49 | 古文选集 |

### 8.3 结论
Anna's Archive 的中文古籍和轻小说馆藏非常丰富，
热门作品基本都有中文翻译版，完全免费、无硬性下载限制（仅有 CAPTCHA 防滥用）。

---

## 9. 绕过 DDoS-Guard 的下载方案

### 9.1 问题
Anna's Archive 使用 DDoS-Guard 防护，直接通过 `slow_download` 或 `fast_download` 端点下载需要：
- 解决 JS 质询（DDoS-Guard）
- CAPTCHA 验证
- 登录/捐赠（fast download）

### 9.2 KindleFetch 的发现

通过分析 `justrals/KindleFetch` 项目源码，发现其下载方案：

**核心思路**: 不经过 Anna's Archive 的 partner server，而是直接从 **Library Genesis (LibGen)** 下载。

#### 源码关键部分 (lgli_download.sh)

```sh
# 1. 通过 LibGen 的 ads.php 获取下载信息
curl -s -L "$LGLI_URL/ads.php?md5=$md5"

# 2. 提取 get.php 链接
download_link=$(echo "$html" | grep -o -m1 'href="[^"]*get\.php[^"]*"')

# 3. 下载实际文件
curl -# -L -o "$final_location" "$download_url"
```

#### 镜像站配置 (link_config)
```
ANNAS_MIRROR_URLS="https://annas-archive.gl https://annas-archive.vg https://annas-archive.pk https://annas-archive.gd"
LGLI_MIRROR_URLS="https://libgen.li https://libgen.la https://libgen.gl"
ZLIB_MIRROR_URLS="https://z-library.sk https://z-lib.fm https://1lib.sk https://z-library.ec"
```

### 9.3 验证结果

该方案经验证可行:
```
请求:  https://libgen.li/ads.php?md5=9c3f625004d476e389f5b437cf2979e8
响应:  包含 get.php?md5=...&key=... 链接
下载:  https://libgen.li/get.php?md5=9c3f625004d476e389f5b437cf2979e8&key=XXX
结果:  成功获取 EPUB 文件
```

### 9.4 下载工作流

```
1. Anna's Archive 搜索
   https://annas-archive.gl/search?q=轻小说&ext=epub&lang=zh
   → 提取 md5 hash (嵌入在页面 JS 中)

2. LibGen 直接下载
   https://libgen.li/ads.php?md5={md5}
   → 提取 get.php 链接

   https://libgen.li/get.php?md5={md5}&key={key}
   → 下载 EPUB 文件
```

**优势**:
- 无 DDoS-Guard 防护
- 无 CAPTCHA
- 无需登录
- 无下载限制

**注意事项**:
- 依赖 LibGen 镜像可用性
- 部分仅存在于 Z-Library 的书籍可能无法通过 LibGen 获取
- 需合理控制请求频率

---

## 10. AI EPUB 阅读器对比

调研过程中发现两个同名的 AI 阅读器项目 Marginalia，均以"书页边缘 AI 对话"为核心概念。

### 10.1 功能对比

| 维度 | eddmann/Marginalia | EurFelux/marginalia |
|------|------------------|-------------------|
| **技术栈** | Tauri v2 + Rust + Next.js + TypeScript | Electron + React + TypeScript |
| **成熟度** | v0.0.2, 7 commits, 2 releases | **v0.16.0, 1,150 commits, 15 releases** |
| **格式** | EPUB, PDF, MOBI, AZW3, FB2, CBZ, TXT, MD | **EPUB, PDF** |
| **AI 模型** | Claude (Opus/Sonnet), GPT-5.4 | **OpenAI / Anthropic / Google / 任意兼容端点** |
| **API Key 配置** | ❌ 自动加载 Claude Code/Codex CLI 凭据，不可自配 | ✅ **用户自行配置，支持任意 OpenAI 兼容端点** |
| **翻译** | ❌ | ✅ **一键 Explain / Translate / Summarize** |
| **TTS 朗读** | ❌ | ✅ **Web Speech API，跨平台，无需配置** |
| **上下文透明** | ❌ | ✅ 可视化 context chips（选中段/章节/全书摘要） |
| **AI 记忆** | ❌ | ✅ 跨对话持久化，可读/编辑/删除 |
| **Persona** | ❌ | ✅ 自定义助手名称、人格、常驻指令 |
| **批注** | ✅ 高亮、书签、标注 (Markdown 导出) | ✅ 5 色高亮 + 下划线 + 便签 + Markdown 笔记本 |
| **全库搜索** | ✅ | ❌ |
| **库视图** | 列表 | ✅ Apple Books 风格书墙，拖拽导入 |
| **本地优先** | ✅ | ✅ |
| **平台** | macOS + Linux | **macOS**（Homebrew + dmg） |
| **中文** | ❌ | ✅ **双语界面**（English / 简体中文） |
| **许可证** | AGPL-3.0 | GPL-3.0 |

### 10.2 安装过程 (macOS)

**方式一: Homebrew（推荐）**
```bash
brew tap eurfelux/tap
brew trust eurfelux/tap          # 首次需信任非官方 tap
brew install --cask marginalia
```

**方式二: 手动下载**
从 [GitHub Releases](https://github.com/EurFelux/marginalia/releases) 下载最新的 `.dmg`，打开后将 marginalia 拖入 Applications。

首次启动 macOS 会提示"无法验证开发者"——因 ad-hoc 签名未经过 Apple 公证。解决方法：
- 系统设置 → 隐私与安全性 → 仍要打开
- 或终端执行: `xattr -d com.apple.quarantine /Applications/marginalia.app`

安装验证:
```bash
ls /Applications/marginalia.app
# → 应显示 Contents 目录
```

**注意**: 本项目基于 Electron，**目前只有 macOS 桌面版**。从 `forge.config.ts` 可见打包目标仅包含 `darwin-arm64` 和 `darwin-x64`，无 iOS/Android 版本。

### 10.3 EurFelux/marginalia TTS 原理

- **驱动**: Web Speech API（`window.speechSynthesis`）
- **跨平台**: macOS (NSSpeechSynthesizer) / Windows (SAPI5) / Linux (speech-dispatcher)
- **配置**: **零配置**，开箱即用，使用系统自带语音
- **音色推荐**: 目前仅 macOS 做了精选（英文 Samantha/Alex/Karen/Daniel，中文 Tingting/婷婷/Meijia/美佳）
- **数据安全**: 不上传任何数据，"speaks with the voices already on your machine"

### 10.4 选择建议

| 需求 | 推荐 |
|------|------|
| 格式种类多、搜索全库 | **eddmann/Marginalia**（支持 8 种格式） |
| AI 翻译 + TTS + 中文 | **EurFelux/marginalia**（双语 + 朗读） |
| 自定义 API Key | **EurFelux/marginalia**（任意 OpenAI 兼容端点） |
| 多平台（非 macOS） | **eddmann/Marginalia**（macOS + Linux）或 Koodo Reader |
| 纯阅读 + 批量管理 | **Calibre + cal-annas**（最成熟） |
| **iOS/iPadOS 原生 AI 阅读** | **vreader** 或 **Empty**（见 11.1） |

---

## 11. iOS/iPadOS 开源 AI EPUB 阅读器

除桌面端外，GitHub 上出现了两个较成熟的 iOS 原生开源 AI EPUB 阅读器。

### 11.1 功能对比

| 维度 | vreader | Empty |
|------|---------|-------|
| **GitHub** | [lllyys/vreader](https://github.com/lllyys/vreader) | [DaviRain-Su/empty](https://github.com/DaviRain-Su/empty) |
| **Stars** | ⭐17 | ⭐11 |
| **iOS/iPadOS** | ✅ **iPhone + iPad** | ✅ **iPhone + iPad + visionOS** |
| **macOS** | ❌ | ✅ 完整深读工作台 |
| **技术栈** | Swift 6 + SwiftUI + SwiftData | Swift + SwiftUI |
| **成熟度** | v3.59.18, 1,611 commits, 3 releases | v1.0.0, 98 commits, 1 release |
| **格式** | **EPUB, AZW3/MOBI, PDF, TXT, Markdown** | EPUB, PDF |
| **AI 模型** | OpenAI 兼容 API（BYOK） | **Apple Intelligence 端侧（默认）** + OpenAI/Anthropic BYOK |
| **AI 对话** | ✅ 多轮对话，**每书多会话**，WebDAV 同步 | ✅ 「朱」阅读 Agent，自主调度工具 |
| **翻译** | ✅ **双语对照逐行翻译** + 整书后台翻译，9 种语言 | ✅ 双语对照 + 内联翻译透镜 |
| **TTS 朗读** | ✅ AVSpeechSynthesizer + HTTP 云 TTS | ✅ macOS 端 |
| **防剧透** | ❌ | ✅ **所有 AI 功能只基于已读文本** |
| **摘要** | ✅ 章节/全书/已读部分 | ✅ Chapter Recap + 已读进度标记 |
| **批注** | ✅ 高亮、书签、笔记 | ✅ 精确 UTF-16 锚定高亮 + 笔记 |
| **AI 记忆** | ✅ 跨对话持久化 | ✅ ReaderMemory 跨书主题发现 |
| **词汇学习** | ❌ | ✅ Ebbinghaus 间隔复习闪卡 |
| **全库搜索** | ✅ SQLite FTS5（含 CJK） | ❌ |
| **库视图** | 网格/列表 + OPDS 目录 | Cover 书架 + 继续阅读卡片 |
| **同步** | **WebDAV**（书籍+批注+AI 历史） | .empty-notes 包导出/导入 |
| **本地优先** | ✅ | ✅ |
| **开源协议** | MIT | MIT |

### 11.2 安装方式 (iPad/iPhone)

两个项目均**未提供 App Store / TestFlight / 预构建 IPA**，需通过 Xcode 源码构建部署：

**vreader:**
```bash
git clone https://github.com/lllyys/vreader.git
cd vreader
xcodegen generate
open vreader.xcodeproj
```
选择 iPad/iPhone 真机或模拟器 → `Cmd + R` 运行。

**Empty:**
```bash
git clone https://github.com/DaviRain-Su/empty.git
cd Empty
open Empty.xcodeproj
```
选择 iPad/iPhone 模拟器 → `Cmd + R` 运行。

> **实战构建记录**: 本调研基于 macOS 27.0 + iPadOS 27.0 完成了 Empty 从源码到 iPad 真机安装的全流程，包含 Xcode 版本选择、开发者模式配置、dyld 崩溃修复、签名设置等所有踩坑记录。详见 **[svjack/empty-builder-guide](https://github.com/svjack/empty-builder-guide)**（私有仓库）中的 `BUILD_GUIDE.md`。

> **注意**: 真机部署需要 Apple Developer 账号（免费账号也可，但每 7 天需重新签名）。如有 Mac 开发环境，推荐 **vreader**（功能最全面，支持格式多，有 WebDAV 同步）；如看重隐私和 Apple Intelligence 端侧推理，推荐 **Empty**（防剧透，间隔复习，知识图谱）。

### 11.3 选择建议

| 需求 | 推荐 |
|------|------|
| iOS 上功能最全的 AI 阅读器 | **vreader**（多格式、AI 对话、双语翻译、TTS、全库搜索、WebDAV 同步） |
| 隐私优先 + 端侧 AI | **Empty**（Apple Intelligence 默认，BYOK 可选，防剧透设计） |
| 想直接下载即用（无需 Xcode） | 两者均不满足；考虑 **Readest**（App Store 免费，但无 LLM 对话） |
| 跨书知识管理 + 间隔复习 | **Empty**（知识图谱、闪卡、词汇） |
| 格式支持最多 | **vreader**（EPUB, AZW3/MOBI, PDF, TXT, MD） |
| 有 Mac 也在用 | **Empty**（macOS + iOS 统一体验） |

---

## 12. Apple Intelligence 端侧 AI 架构与限制

### 12.1 什么是 Apple Intelligence

Apple Intelligence 是 Apple 的个人智能系统，核心是 **Foundation Models framework**（`/System/Library/Frameworks/FoundationModels.framework`），提供端侧 ~3B 参数语言模型，专为 Apple Silicon 优化。

| 维度 | 端侧模型 | 服务器模型 |
|------|---------|-----------|
| 参数量 | **~3B** | PT-MoE（并行轨道路由器专家混合） |
| 量化 | **2-bit QAT**（量化感知训练） | 3.56-bit ASTC |
| 内存优化 | KV-cache 共享（省 37.5%） | 同步开销降低 87.5% |
| 上下文 | ~65K tokens | ~65K tokens |
| 多模态 | 文本 + 图像（ViTDet-L 300M） | 文本 + 图像（ViT-g 1B） |
| 运行位置 | **设备本地**（Apple Silicon） | **Private Cloud Compute**（Apple 隐私云） |
| 开发者接口 | **FoundationModels 框架**（`@Generable` 约束解码） | 仅 Apple 系统功能使用 |

### 12.2 Empty 如何调用端侧 AI

Empty 通过 `FoundationModelsAIService.swift` 调用 Apple 端侧模型，核心链路：

```
FoundationModelsService.make()
       ↓
#if canImport(FoundationModels)    ← 编译时检查框架
  FoundationModelsAIService()
       ↓
SystemLanguageModel.default        ← 检查端侧模型可用性
  .isAvailable
       ↓
LanguageModelSession(instructions:) ← 创建会话
       ↓
session.respond(to: prompt)        ← 发起推理
       ↓
@Generable 约束解码                 ← 直接产出 Swift 类型
```

关键特性：
- **免费、离线、隐私** — 不联网，不上传数据
- **`@Generable` 宏** — Swift 类型约束解码，保证输出格式
- **`LanguageModelSession`** — 每次请求新建会话，避免上下文泄露
- **自动回退** — 端侧不可用时 fallback 到用户配置的 BYOK 云 API

### 12.3 地区限制（重要）

Apple Intelligence **不在中国大陆提供**。当系统语言/地区为 `zh_CN` 时：

- 系统设置中无 Apple Intelligence 开关
- `Assistant Enabled = 0`（Siri 禁用）
- Empty 的 `FoundationModelsAIService.availability` 返回 `.unavailable`
- 端侧 `~3B` 模型无法下载

**解决方案**：在 Empty 中使用 BYOK 云 API（OpenAI/Anthropic/任意兼容端点）
- 侧栏 **AI 状态** → 配置 API Key
- 功能完整（翻译、摘要、伴读对话、词汇闪卡等）
- Empty 自动 fallback 到云端

### 12.4 macOS 使用指南

Empty 在 macOS 上提供完整四面板深读工作台：

1. **开启图书**：打开 Empty → import EPUB/PDF
2. **呼出伴读**：阅读视图顶部工具栏 → Picker 选择 **「导读」**（companion 模式）
3. **划词 AI**：选中文字 → 弹出工具栏（解释/翻译/总结）
4. **AI 配置**：侧栏 **AI 状态** → 选择 on-device（仅限支持地区）或配置云 API Key

| 需求 | 配置方式 |
|------|---------|
| 中国大陆用户 | BYOK 云 API（OpenAI/Anthropic/兼容端点） |
| 海外用户 | Apple Intelligence 端侧（默认免费离线）或 BYOK 云 API |


## 13. 实际下载验证

> ⚠️ **适用范围说明**: 本节验证的 3 级下载策略（LibGen → Sci-Hub → slow_download）**仅对存在于 LibGen 上的书目有效**。对于 Z-Library 独占的书目（未上传至 LibGen），Step 1 和 Step 2 必然失败，Step 3（slow_download）因 DDoS-Guard 阻挡也无法通过 CLI 完成。**《朝鲜王朝实录》** 和 **《两班：朝鲜王朝的特权阶层》** 即为反例（详见 §13.4）。

基于 [cal-annas](#5-核心项目-a-peirogoncal-annas) 的 3 级下载策略，编写了完整的 Python 下载脚本，成功下载两类各 3 本 EPUB。

### 13.1 下载脚本

脚本位置: `/tmp/cal_annas_download.py`（基于调研过程中的实际执行版本）

```python
"""
cal-annas 下载方案实现

3 级回退:
  Step 1 — LibGen 直连 (从 /md5/ 页面提取外部链接)
  Step 2 — Sci-Hub
  Step 3 — slow_download HTTP 重定向跟随

参考工程:
  - a-peirogon/cal-annas (核心参考)
  - justrals/KindleFetch (辅助参考)
"""
```

#### 核心下载流水线

```python
# Step 0: 搜索获取 md5
def search_annas(query, ext="epub", lang="zh"):
    url = f"https://annas-archive.gl/search?q={quote(query)}&ext={ext}&lang={lang}"
    html = fetch(url)
    md5s = list(dict.fromkeys(re.findall(r'md5:([a-f0-9]{32})', html)))
    return md5s

# Step 1: LibGen 直连 (对应 cal-annas._get_libgen_li_link)
def download_via_libgen(md5, output_path):
    mirrors = ["https://libgen.li", "https://libgen.rs", "https://libgen.la"]
    for mirror in mirrors:
        ads_url = f"{mirror}/ads.php?md5={md5}"
        html = fetch(ads_url)
        get_match = re.search(r'href="([^"]*get\.php[^"]*)"', html)
        if get_match:
            get_url = f"{mirror}/{get_match.group(1)}"
            data = fetch_binary(get_url)
            if data and len(data) > 10000:
                save(output_path, data)
                return True
    return False

# Step 2: /md5/ 页面外部链接 (对应 cal-annas create_browser Step 1)
def download_via_extlinks(md5, ext_links, output_path):
    for link in ext_links:
        real_url = resolve_external_link(link)  # 解析 LibGen/Sci-Hub GET 按钮
        data = fetch_binary(real_url)
        if data and len(data) > 10000:
            save(output_path, data)
            return True
    return False

# Step 3: slow_download 重定向跟随 (对应 cal-annas create_browser Step 2)
def download_via_slow(md5, output_path):
    mirrors = ["https://annas-archive.gl", "https://annas-archive.pk", "https://annas-archive.gd"]
    for mirror in mirrors:
        slow_url = f"{mirror}/slow_download/{md5}/0/0"
        code, headers, data = http_request(slow_url)
        if code == 200 and headers.get("Content-Type", "").startswith("application/"):
            save(output_path, data)
            return True
    return False
```

#### 外部链接解析（对应 cal-annas 的各来源提取器）

```python
def resolve_external_link(url):
    """解析外部下载链接, 返回真实文件 URL"""
    html = fetch(url)
    
    # LibGen.li: h2[text()="GET"] → href
    m = re.search(r'<h2[^>]*>GET</h2>.*?<a[^>]*href="([^"]+)"', html, re.DOTALL)
    if m: return resolve_relative(m.group(1), url)
    
    # LibGen.rs: h2/a[text()="GET"] → href
    m = re.search(r'<h2>.*?<a[^>]*href="([^"]+)"[^>]*>GET</a>', html, re.DOTALL)
    if m: return m.group(1)
    
    # Sci-Hub: embed#pdf → src
    m = re.search(r'<embed[^>]*id="pdf"[^>]*src="([^"]+)"', html)
    if m: return resolve_relative(m.group(1), url)
    
    return None
```

### 13.2 参考工程源码位置

以下仓库已克隆至本地用于源码分析:

```
/Users/svjack/temp/cal-annas/
├── annas_archive.py   (1251 行 — 搜索 + 3 级下载拦截器)
├── config.py           (403 行 — Qt 配置界面)
├── constants.py        (241 行 — 镜像列表 + TTL 缓存)
├── __init__.py         (728 字节 — Calibre 插件入口)
└── README.md           (37 行 — 插件安装说明)
```

关键函数映射:

| cal-annas 函数 | 行号 | 功能 | 对应脚本实现 |
|---------------|------|------|------------|
| `_search()` | 787 | 分页搜索 + 镜像故障转移 | `search_annas()` |
| `_parse_search_result()` | 670 | 解析搜索结果 div → SearchResult | `get_book_info()` |
| `_get_libgen_li_link()` | 1060 | LibGen.li GET 链接提取 | `resolve_external_link()` |
| `_get_libgen_rs_link()` | 1073 | LibGen.rs GET 链接提取 | `resolve_external_link()` |
| `_get_scihub_link()` | 1083 | Sci-Hub PDF 链接提取 | `resolve_external_link()` |
| `_get_zlib_link()` | 1096 | Z-Library 链接提取 | 未实现(需登录) |
| `create_browser()` | 1114 | 下载拦截器(Step 1+2) | `download_via_libgen()` + `download_via_slow()` |
| `_active_libgen_mirrors()` | 273 | SLUM 活跃 LibGen 镜像列表 | `["libgen.li","libgen.rs","libgen.la"]` |
| `_prewarm_cookies()` | 1006 | 后台预热 DDoS-Guard cookies | 未实现(CLI 无需) |

### 13.3 下载结果

脚本执行于 2026-06-23，保存至 `books/` 目录。

#### 第一类: 中文轻小说 (3 本)

| 文件 | 大小 | 来源 | 下载方式 |
|------|------|------|---------|
| `light_novel_刀剑神域_Progressive_005.epub` | 10.5 MB | Anna's Archive → LibGen | Step 1 成功 |
| `light_novel_义妹生活_第六卷.epub` | 3.2 MB | Anna's Archive → LibGen | Step 1 成功 |
| `light_novel_Re_从零开始.epub` | 0.5 MB | Anna's Archive → LibGen | Step 1 成功 |

#### 第二类: 中国古代文本 (3 本)

| 文件 | 大小 | 来源 | 下载方式 |
|------|------|------|---------|
| `classical_许译中国经典诗文集.epub` | 9.8 MB | Anna's Archive → LibGen | Step 1 成功 |
| `classical_论语译注.epub` | 0.4 MB | Anna's Archive → LibGen | Step 1 成功 |
| `classical_道德经.epub` | 0.8 MB | Anna's Archive → LibGen | Step 1 成功 |

#### 下载统计

| 指标 | 数值 |
|------|------|
| 搜索尝试 | 6 组关键词, 每组分批获取 |
| 候选 md5 | 约 150 个 (每组 50 个) |
| 尝试下载 | 6 本 |
| Step 1 (LibGen) 成功 | 6/6 (100%) |
| Step 2 (ExtLinks) | 未触发 (Step 1 全成功) |
| Step 3 (slow_download) | 未触发 (Step 1 全成功) |
| 总下载量 | 约 25 MB |

### 13.4 关键结论

#### 成功案例: LibGen 可见的书目

6 本书全部通过 LibGen `ads.php → get.php` 路径成功下载。验证了这些书在 Anna's Archive 上均标注了 `lgli` 来源:

- **刀剑神域 Progressive 005** ✅ `159dd343` → LibGen 直连
- **义妹生活 第六卷** ✅ `e09274cd` → LibGen 直连
- **Re:从零开始** ✅ LibGen 直连
- **许译中国经典诗文集** ✅ `ae0a5766` → LibGen 直连
- **论语译注** ✅ `9209bfac` → LibGen 直连
- **道德经** ✅ LibGen 直连

#### 失败案例: Z-Library 独占书目

| 书名 | MD5 | 来源标记 | LibGen 验证 | CLI 下载结果 |
|------|-----|---------|-----------|------------|
| 《朝鲜王朝实录》 | `50b42aa8...` | `zlib/` | ❌ `ads.php` 返回 "File not found" | ❌ 仅得到 898 字节的 DDoS-Guard HTML |
| 《两班：朝鲜王朝的特权阶层》 | — | `upload` (AA 上传) | ❌ 不在 LibGen | ❌ 同上 |

根本原因: 这些书**只存在于 Z-Library 源**，不在 LibGen 上。CLI 脚本的 Step 1 (LibGen) 无路可走，Step 3 (`/slow_download/`) 被 DDoS-Guard 阻挡，返回 HTML 质询页面而非真实 EPUB。

> ✅ **cmux 浏览器可以解决**: 这两本失败案例已通过 cmux 浏览器成功下载（详见[快速开始 - 场景 B](#场景-bz-library-独占书目通过-annas-archive-下载通道)）。《朝鲜王朝实录》81MB EPUB 和《李朝实录》17MB PDF 均已保存至 `books/` 目录。

#### 验证过的朝鲜史相关书目（均可在 LibGen 下载）

通过 cmux 浏览器搜索 `&src=lgli` 共找到 **36 个 md5**，按书名去重后有:

| 书名 | 作者 | 格式 | 大小 |
|------|------|------|------|
| **真景:文物中的朝鲜王朝史** (甲骨文系列) | 申炳周 | EPUB | ~15MB |
| **朝鲜王朝仪轨** | 韩永愚 | EPUB | — |
| **大明旗号与小中华意识:朝鲜王朝尊周思明问题研究(1637—1800)** | 孙卫国 | EPUB | — |
| **朝鲜王朝面面观(修訂一版)** | — | EPUB | — |
| **从「尊明」到「奉清」:朝鲜王朝对清意识的嬗变(1627-1910)** | — | EPUB | — |
| **两班:朝鲜王朝的特权阶层** | — | EPUB | — |
| **朝鲜王朝前期的故事编纂** | — | EPUB | — |
| **海东五百年:朝鲜王朝(1392-1910)兴衰史** | — | EPUB | 57MB ✅ 已下载 |
| **李朝实录 第二册 太宗实录 第一** | 学习院东洋文化研究所刊 | PDF | 17MB ✅ 已下载 |
| **李朝实录 第三册 太宗实录 第二** | — | — | — |
| **李朝实录 第四册 太宗实录 第三** | — | — | — |

#### 最终结论

1. **cmux 浏览器是标准下载工具**: 见顶部的[快速开始](#快速开始标准下载流程cmux-浏览器)标准流程。LibGen 存在的书用场景 A（3 步），Z-Library 独占书用场景 B（4 步）
2. **LibGen 直连是 CLI 自动化路径**: 对 LibGen 存在的书目，Python 脚本通过 `ads.php → get.php` 成功率为 100%
3. **慢速下载通道不可 CLI 自动化**: DDoS-Guard + CDN 限速双重阻挡，curl/Python 均不可用
4. **格式支持**: 下载的 EPUB/PDF 均可在标准阅读器中正常打开

### 13.5 新增实践: Z-Library 独占书目的场景 B 完整演示

2026-06-24 以《构建Agentic AI系统：打造能推理、可规划、自适应的AI智能体》（清华大学出版社，2026，PDF 26.1MB）为例，完整走通了 Z-Library 独占书目的下载流程。

#### 关键步骤

```bash
# 1. Anna's Archive 搜索（不加 &src=lgli，让 zlib 源也出现）
cmux --json browser open \
  "https://annas-archive.gl/search?q=构建Agentic+AI系统+打造能推理&lang=zh" \
  --workspace "${CMUX_WORKSPACE_ID}"
```

搜索结果的 PDF 项 `md5=10e320702f5072a8827fe1cec302907b`（zlib 源）。

```bash
# 2. 在详情页点击 "Slow Partner Server #1"
#    DDoS-Guard 由浏览器自动处理
```

跳转到 `slow_download/{md5}/0/0` 页面。

```bash
# 3. 点击 "📚 Download now"
```

浏览器打开 partner server（`wbsg8v.xyz`）的新标签页，但该标签页**显示空白**（浏览器无法内联渲染 partner server 返回的 PDF）。

```bash
# 4. 从 slow_download 页面 DOM 中提取直链，用 curl 完成下载
curl -L -o 构建Agentic_AI系统.pdf \
  -H "User-Agent: Mozilla/5.0" \
  -H "Referer: https://annas-archive.gl/" \
  "https://wbsg8v.xyz/d3/y/.../构建Agentic%20AI系统...10e320702f50...pdf"
```

#### 为什么 curl 能成功而不被 DDoS-Guard 阻挡

| 阶段 | 方式 | DDoS-Guard |
|------|------|-----------|
| 获取直链 | cmux 浏览器请求 `slow_download` | ✅ 浏览器自动通过 JS 质询 |
| 下载文件 | curl 请求 partner server 直链 | ✅ 直链已通过验证，不再触达 DDoS-Guard |

**核心要点**: 浏览器只负责**过 DDoS-Guard 并获取临时直链**，直链提取后可由任意 HTTP 客户端下载。`slow_download` 页面显示 "📚 Download now" 时，页面 DOM 中已经包含 `wbsg8v.xyz` 的直链（可通过 `cmux browser surface:N eval "document.body.innerText"` 提取）。

#### 注意事项

- partner server 有**并发限制**（"Too many downloads at the same time from the same IP"），首次点 "Download now" 打开的新标签页会触发限流；关闭多余标签页后重试即可
- 新标签页打开后可能显示空白，这是 PDF 在内嵌浏览器中无法渲染的预期行为，不影响文件本身的完整性
- PDF 大小 26.1MB，MD5 校验通过，文件格式为 `PDF document v1.3`

#### 下载统计

| 指标 | 数值 |
|------|------|
| 搜索尝试 | 1 次 |
| 候选 md5 | 1 个（zlib 源） |
| cmux 浏览器耗时（DDoS-Guard + 导航） | ~30s |
| curl 下载耗时 | ~76s（~335KB/s） |
| 最终文件 | `构建Agentic AI系统.pdf` (24.9MB) |


## 14. 总结与推荐

> **标准下载流程** → 见文档顶部[快速开始](#快速开始标准下载流程cmux-浏览器)（场景 A / 场景 B），使用 cmux 浏览器即可完成。

### 14.1 各场景最佳选择

| 需求 | 推荐方案 |
|------|---------|
| 快速下载（推荐） | **cmux 浏览器 + [快速开始](#快速开始标准下载流程cmux-浏览器)标准流程** |
| 公版书/经典文学 | Standard Ebooks（品质最高）或 Project Gutenberg（数量最多） |
| 学术论文/科学文献 | Sci-Hub 或 Anna's Archive |
| 中文轻小说/网络小说 | Anna's Archive → LibGen 下载（仅限 LibGen 已有书目） |
| 中文古籍/经典 | Anna's Archive 或 LibGen |
| 最大覆盖面 | Anna's Archive（6,400万+ 书籍） |
| 零限制批量下载 | Anna's Archive Torrents 或 LibGen 直接下载 |

### 14.2 关键发现

1. **cmux 浏览器 + Anna's Archive + LibGen 是最普适的下载方案** — 对 LibGen 存在的书走场景 A（3 步完成），对 Z-Library/upload 独占书走场景 B（4 步完成），文件自动保存到 `~/Downloads/`
2. **Anna's Archive 是 Z-Library 的最佳替代**，藏书量约为 Z-Library 的 3 倍
3. **数据完全开源**，可通过 Torrent 或 API 无限制批量获取
4. **LibGen 直连可绕过 DDoS-Guard**，但仅对 LibGen 上存在的书目有效 — 对 Z-Library 独占书，cmux 浏览器可走 slow_download 通道解决
5. 中文内容（古籍 + 轻小说）在 Anna's Archive 上储备丰富

### 14.3 相关 GitHub 项目

- **Openlib** (`dstark5/Openlib`) ⭐2,384 — iOS App 访问 Anna's Archive
- **KindleFetch** (`justrals/KindleFetch`) ⭐286 — Kindle 设备 CLI 下载
- **cal-annas** (`a-peirogon/cal-annas`) ⭐10 — Calibre 插件（最近推送 2026-06-21）
- **bookdl** (`billmal071/bookdl`) ⭐15 — Go 语言 CLI 工具
- **vreader** (`lllyys/vreader`) ⭐17 — iOS/iPadOS AI EPUB 阅读器（AI 对话、双语翻译、TTS、WebDAV）
- **Empty** (`DaviRain-Su/empty`) ⭐11 — macOS + iOS/iPadOS 防剧透 AI 伴读（端侧 AI / BYOK）
  - 本地构建 & 真机安装实战记录: **[svjack/empty-builder-guide](https://github.com/svjack/empty-builder-guide)**
- **vRain** (`shanleiguang/vRain`) — 中文古籍刻本风格直排 PDF 生成工具
  - 安装/配置/标记系统指南: **[svjack/vRain-guide](https://github.com/svjack/vRain-guide)**



---

> **免责声明**: 本文档仅供技术研究和教育目的。请尊重版权法，合理使用资源。
