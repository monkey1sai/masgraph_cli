---
# https://vitepress.dev/reference/default-theme-home-page
layout: home

hero:
  name: "MASFactory"
  text: "一个以图为中心的多智能体系统编排框架"
  tagline: "Vibe Graphing：从自然语言意图到可执行 MAS 工作流"
  image:
    light: /svg/hero-logo.svg
    dark: /svg/hero-logo-dark.svg
    alt: MASFactory
  actions:
    - theme: brand
      text: 快速入门
      link: /zh/start/introduction
    - theme: alt
      text: API 文档
      link: /zh/api_reference
    - theme: alt
      text: 论文
      link: https://arxiv.org/abs/2603.06007
    - theme: alt
      text: 源代码
      link: https://github.com/BUPT-GAMMA/MASFactory

features:
  - title: 🎨 Vibe Graphing：自然语言驱动的设计体验
    details: 从行动者到设计者，在于AI的对话中实现多智能体系统的设计与迭代。
  
  - title: 🧩 图结构“搭积木”：原子节点与复合组件
    details: 以图为核心组织能力模块，把常见流程沉淀为可组合的结构单元；支持将子图封装为节点并复用，通过声明式开发更低成本地搭建复杂系统。
  
  - title: 🔍 可视化与白盒调试
    details: 配套 MASFactory Visualizer，提供拓扑预览与运行时追踪能力，更快理解系统行为、定位流程问题，并以更低成本迭代优化。
  
  - title: 🧠 上下文协议适配
    details: 面向多来源上下文（记忆、检索、外部知识与工具结果）提供统一的组织方式，让上下文更可控、可管理、可追溯。
---
