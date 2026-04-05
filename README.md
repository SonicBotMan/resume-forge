# ResumeForge — 简历锻造工坊

> **把十年经历丢进来，锻造成一份好简历。**

AI 驱动的简历锻造工具。不用筛选材料，不用组织语言，一股脑上传你的文档/PPT/PDF——AI 自动提炼经历，生成贴合目标岗位的简历。

## 🎯 解决什么问题？

- 材料太多太散，不知道哪些有价值
- 做了很多事，但不会用"简历语言"包装
- 看到合适的岗位，不知道怎么调整简历去贴合
- 十年没写简历，不知道从哪下手

## ✨ 核心功能

### 第一步：扔材料
- 支持批量上传 PDF / PPT / Word / 图片 / 文本
- **不用筛选，不用分类，全部扔进来**
- AI 自动分类、去重、提取有价值的信息

### 第二步：AI 提炼
- 从海量材料中自动提取项目经历、管理经验、量化成果
- 生成结构化的"经历图谱"（时间线 + 能力维度）
- 你可以审核、修改、补充 AI 提炼的结果

### 第三步：锻简历
- 基于提炼的经历，一键生成完整简历
- 粘贴目标岗位 JD，AI 自动优化措辞
- 多个简历版本，针对不同岗位定制

### 第四步：备面试
- AI 模拟面试官，基于你的真实经历提问
- 自动生成常见面试问题答案
- 标记你的"高光时刻"和"需要注意的点"

## 🛠 技术栈

- **前端**: React + TypeScript + Tailwind CSS
- **后端**: Python FastAPI
- **AI**: litellm（支持 OpenAI / Anthropic / 智谱 / MiniMax）
- **文档解析**: pdfplumber / python-pptx / python-docx / OCR
- **存储**: SQLite

## 📋 项目状态

- [x] PRD + 技术方案（[查看文档](./PRD.md)）
- [ ] MVP 开发中
- [ ] 在线 Demo

## 🚀 快速开始（规划中）

```bash
# 后端
cd backend && pip install -r requirements.txt && uvicorn main:app --reload

# 前端
cd frontend && npm install && npm run dev
```

## 📄 许可证

MIT License
