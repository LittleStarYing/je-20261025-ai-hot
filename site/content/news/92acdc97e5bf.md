+++
title = "Dropbox 升级 Riviera 平台，支持 AI 工作负载，这意味着什么？"
description = "Dropbox 升级 Riviera 平台，支持 AI 工作负载，这意味着什么？。来源：InfoQ AI。"
seo_title = "Dropbox 升级 Riviera 平台，支持 AI 工作负载，这意味着什么？｜AI资讯解读 - AI热榜"
seo_description = "Dropbox 升级 Riviera 平台，支持 AI 工作负载，这意味着什么？。来源：InfoQ AI。"
seo_keywords = "Dropbox 升级 Riviera 平台，支持 AI 工作负载，这意味着什么？, InfoQ AI, AI新闻, AI资讯, AI热榜"
slug = "92acdc97e5bf"
type = "news"

[params]
id = "92acdc97e5bf"
name = "Dropbox 升级 Riviera 平台，支持 AI 工作负载，这意味着什么？"
title_en = "Dropbox 升级 Riviera 平台，支持 AI 工作负载，这意味着什么？"
original_url = "https://www.infoq.cn/article/jJAcfJO5e0ElPhIxwwxo?utm_source=rss&utm_medium=article"
source = "InfoQ AI"
published = "2026-09-23T15:47:00"
lang = "zh"
intro = "Dropbox 升级 Riviera 平台，支持 AI 工作负载，这意味着什么？。来源：InfoQ AI。"
ai_summary = ""
summary = ""
summary_zh = ""
tags = []
list_page = 8
+++

<!-- AUTO-GENERATED: news page -->

Dropbox 已将 Riviera 从一个文件预览服务演进为一个通用内容处理平台，支持超过 300 种文件格式和 100 多种转换能力。

该平台现在每秒执行数十万次转换，并支持 Search、Replay、Sign 和 Dash，让 AI 工作负载能够复用为早期产品开发的内容处理基础设施。

Riviera 最初是 Dropbox 内部用于跨文件格式生成预览的服务。

工程师们没有为单个格式和输出创建单独的处理服务，而是将内容处理分解为可复用的转换单元。

例如，PowerPoint 预览可以通过将演示文稿转换为 PDF，然后将 PDF 页面转换为图像来生成。

这些转换单元随后可以被组合成其他处理管道。

Riviera 的可组合转换管道（来源：Dropbox 博客文章）
该架构将编排与执行分离。

一个中心组件负责验证请求、组合转换管道、将工作分派给后端工作进程并管理缓存。

各个工作进程实现了特定的转换能力，而插件模型可以在不更改核心编排层的情况下增加新的能力。

Riviera 在 Dropbox 产品和核心界面中的集成（来源：Dropbox 博客文章）
在最新一轮扩展之前，Riviera 已经被用于 AI 处理场景。

Dropbox 此前曾描述过链式转换，将内容转换为文本和嵌入向量，用于 AI 驱动的摘要和问答功能。

当时，该平台支持约 300 种文件类型，每天处理约 25 亿个请求，数据量接近 1 艾字节。

缓存的中间结果让多个 AI 操作可以复用先前生成的内容。

Dash 引入了额外的内容预处理需求，因为它的搜索和 AI 能力需要处理来自 Dropbox 及已连接服务的内容。

Riviera 提供了用于提取和规范化内容的转换操作，在建立索引之前完成内容提取与标准化，让 Dash 能够复用现有的处理管道。

Dropbox 还通过公共 API 开放 Riviera 的能力。

开发者文档描述了用于将文档转换为 Markdown、转录音频和视频以及提取结构化元数据的异步接口。

Markdown API 支持的应用场景包括索引、渲染，以及将文档作为大语言模型的输入。

应用程序提交作业并使用异步作业标识符进行轮询，任务完成和失败状态会分开返回。

该平台也开始出现在外部开发者工具中。

Dropbox 社区的一位开发者发布了 conductor-dropbox，一个用于 Conductor OSS 和 Orkes 的开源集成组件，包含用于文档和 RAG 工作流的异步 Riviera Markdown 提取。

该项目将 Dropbox 操作与工作流编排相结合，用于文档和 AI 处理。

Riviera 不同于 Apache Tika 等通用提取框架，Tika 提供用于检测、解析和提取各种文件格式的文本和元数据的 API。

Riviera 将转换插件与管道组合、异步执行、缓存和集中式编排结合在一起。

## 🔗 原始来源

如果你要核对细节，可以再看原文：
[InfoQ AI原文链接](https://www.infoq.cn/article/jJAcfJO5e0ElPhIxwwxo?utm_source=rss&utm_medium=article)

