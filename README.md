# 开放图书馆资源调研报告

> 记录日期: 2026-06-23
> 目标: 调研 Z-Library 替代方案、无限制 EPUB 下载平台、Anna's Archive 使用及下载方法

---

## 目录

1. [Z-Library 现状](#1-z-library-现状)
2. [GitHub 上的 Z-Library 相关项目](#2-github-上的-z-library-相关项目)
3. [zlibrary.koplugin 源码分析](#3-zlibrarykoplugin-源码分析)
4. [免费 EPUB 下载平台对比](#4-免费-epub-下载平台对比)
5. [Anna's Archive 深度分析](#5-annas-archive-深度分析)
6. [Anna's Archive 藏书验证](#6-annas-archive-藏书验证)
7. [绕过 DDoS-Guard 的下载方案](#7-绕过-ddos-guard-的下载方案)
8. [总结与推荐](#8-总结与推荐)

---

## 1. Z-Library 现状

### 1.1 下载限制
- 普通用户每日有下载数量限制（通常 5-10 本/天）
- 注册账户或捐赠后可获得更多额度
- 访问域名经常变动，需通过官方渠道获取最新地址

### 1.2 书目格式
- 不全是 EPUB 版本
- 常见格式包括: PDF、ePub、MOBI、AZW3 等
- 格式取决于上传者提供的原始文件

---

## 2. GitHub 上的 Z-Library 相关项目

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

## 3. zlibrary.koplugin 源码分析

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

## 4. 免费 EPUB 下载平台对比

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

## 5. Anna's Archive 深度分析

### 5.1 访问方式

| 方式 | 地址 | 说明 |
|------|------|------|
| 主站 | `https://annas-archive.org` | 需代理/Tor 访问 |
| 镜像站(已验证) | `https://annas-archive.gl` | DDoS-Guard 防护 |
| 镜像站 | `https://annas-archive.pk` | — |
| 镜像站 | `https://annas-archive.gd` | — |
| 博客 | `https://annas-blog.org` | 状态更新和公告 |
| Tor 隐藏服务 | `annas-archive.li` | 需 Tor 浏览器 |

### 5.2 首页分析 (`annas-archive.gl`)

- **标题**: "Anna's Archive: LibGen, Sci-Hub, Z-Library in one place"
- **服务商**: DDoS-Guard (JS 质询防护)
- **域名别名**: `annas-archive.gl`, `annas-archive.pk`, `annas-archive.gd`
- **功能入口**: 搜索、捐赠、🧬 SciDB（科学论文数据库）
- **多语言支持**: 60+ 语言

### 5.3 llms-txt.html 分析

博客文章: **"If you're an LLM, please read this"** (2026-02-18)

核心内容:
1. **数据完全开源** — 所有代码和元数据在 GitLab (`software.annas-archive.gl`)
2. **批量下载方式**:
   - 元数据和全文 → Torrents 页面 (`/torrents`)
   - Torrent 程序化下载 → JSON API (`/dyn/torrents.json`)
   - 单文件下载 → 捐赠后使用 API
3. **明文邀请 LLM/爬虫** 使用其数据训练，并呼吁捐赠支持

---

## 6. Anna's Archive 藏书验证

### 6.1 中文轻小说搜索结果

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

### 6.2 古代中文文本搜索结果

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

### 6.3 结论
Anna's Archive 的中文古籍和轻小说馆藏非常丰富，
热门作品基本都有中文翻译版，完全免费、无硬性下载限制（仅有 CAPTCHA 防滥用）。

---

## 7. 绕过 DDoS-Guard 的下载方案

### 7.1 问题
Anna's Archive 使用 DDoS-Guard 防护，直接通过 `slow_download` 或 `fast_download` 端点下载需要：
- 解决 JS 质询（DDoS-Guard）
- CAPTCHA 验证
- 登录/捐赠（fast download）

### 7.2 KindleFetch 的发现

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

### 7.3 验证结果

该方案经验证可行:
```
请求:  https://libgen.li/ads.php?md5=9c3f625004d476e389f5b437cf2979e8
响应:  包含 get.php?md5=...&key=... 链接
下载:  https://libgen.li/get.php?md5=9c3f625004d476e389f5b437cf2979e8&key=XXX
结果:  成功获取 EPUB 文件
```

### 7.4 下载工作流

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

## 8. 总结与推荐

### 8.1 各场景最佳选择

| 需求 | 推荐方案 |
|------|---------|
| 公版书/经典文学 | Standard Ebooks（品质最高）或 Project Gutenberg（数量最多） |
| 学术论文/科学文献 | Sci-Hub 或 Anna's Archive |
| 中文轻小说/网络小说 | Anna's Archive → LibGen 下载 |
| 中文古籍/经典 | Anna's Archive 或 LibGen |
| 最大覆盖面 | Anna's Archive（6,400万+ 书籍） |
| 零限制批量下载 | Anna's Archive Torrents 或 LibGen 直接下载 |

### 8.2 关键发现

1. **Anna's Archive 是 Z-Library 的最佳替代**，藏书量约为 Z-Library 的 3 倍
2. **数据完全开源**，可通过 Torrent 或 API 无限制批量获取
3. **LibGen 直连下载**可绕过 Anna's Archive 的 DDoS-Guard 防护
4. 中文内容（古籍 + 轻小说）在 Anna's Archive 上储备丰富

### 8.3 相关 GitHub 项目

- **Openlib** (`dstark5/Openlib`) ⭐2,384 — iOS App 访问 Anna's Archive
- **KindleFetch** (`justrals/KindleFetch`) ⭐286 — Kindle 设备 CLI 下载
- **cal-annas** (`a-peirogon/cal-annas`) ⭐10 — Calibre 插件（最近推送 2026-06-21）
- **bookdl** (`billmal071/bookdl`) ⭐15 — Go 语言 CLI 工具

---

> **免责声明**: 本文档仅供技术研究和教育目的。请尊重版权法，合理使用资源。
