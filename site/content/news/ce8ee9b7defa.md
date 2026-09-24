+++
title = "智谱把 ZCode 开源了，然后呢？，这意味着什么？"
description = "智谱把 ZCode 开源了，然后呢？，这意味着什么？。来源：InfoQ AI。"
seo_title = "智谱把 ZCode 开源了，然后呢？，这意味着什么？｜AI资讯解读 - AI热榜"
seo_description = "智谱把 ZCode 开源了，然后呢？，这意味着什么？。来源：InfoQ AI。"
seo_keywords = "智谱把 ZCode 开源了，然后呢？，这意味着什么？, InfoQ AI, AI新闻, AI资讯, AI热榜"
slug = "ce8ee9b7defa"
type = "news"

[params]
id = "ce8ee9b7defa"
name = "智谱把 ZCode 开源了，然后呢？，这意味着什么？"
title_en = "智谱把 ZCode 开源了，然后呢？，这意味着什么？"
original_url = "https://www.infoq.cn/article/qEHi6k5ycwXUiasvfNKH?utm_source=rss&utm_medium=article"
source = "InfoQ AI"
published = "2026-09-23T14:43:22"
lang = "zh"
intro = "智谱把 ZCode 开源了，然后呢？，这意味着什么？。来源：InfoQ AI。"
ai_summary = ""
summary = ""
summary_zh = ""
tags = []
list_page = 5
+++

<!-- AUTO-GENERATED: news page -->

一场由 ZCode 本地目录异常膨胀引发的排查，最后把一个 AI Coding 产品推到了安全和信任问题的中心。

9 月 18 日，开发者 ferstar 在清理 MacBook 磁盘空间时，注意到
~/.zcode
本地目录占用了不少空间。

继续逆向客户端和分析网络请求后，他发现，智谱旗下 AI 编程工具 ZCode 会生成本地工作区快照，其中不只有当前代码文件，还包括
.git
历史、Git LFS 缓存、reflog 等内容，并存在将加密快照上传到阿里云 OSS 的链路。

ferstar 随后把
完整排查过程和证据链
公开在个人博客上。

在他进一步分析的一次具体快照中，归档文件大小约 313MB，包含 42,411 个文件，其中约 87% 来自
.git

## 🔗 原始来源

如果你要核对细节，可以再看原文：
[InfoQ AI原文链接](https://www.infoq.cn/article/qEHi6k5ycwXUiasvfNKH?utm_source=rss&utm_medium=article)

