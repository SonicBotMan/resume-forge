# ResumeForge（简历锻造工坊）— PRD & 技术方案

> **一句话定位：** 把你散落各处的材料扔进来，AI 帮你提炼、组织、包装成一份专业简历。

---

## 1. 产品定位和愿景

### 1.1 定位

ResumeForge 是一个**本地优先**的 AI 简历锻造工具。用户只需把所有职业材料（文档、PPT、PDF、截图、随手记的笔记）一股脑上传，系统自动从中提炼出结构化的职业经历，并生成符合目标岗位要求的专业简历。

**核心差异：**
- 不需要用户自己整理材料——AI 负责从混乱中找金子
- 不需要用户懂"简历语言"——AI 负责把日常工作描述转化为简历表达
- 不需要用户操心格式——所见即所得，一键导出

### 1.2 愿景

让每个人都能用 30 分钟，从一堆散乱材料变成一份量身定制的专业简历。

### 1.3 不做什么

- **不做在线简历托管**（隐私敏感）
- **不做简历模板市场**（核心是内容锻造，不是排版）
- **不做招聘匹配平台**（不碰求职链路的其他环节）

---

## 2. 用户画像和痛点分析

### 2.1 核心用户：资深产品经理

| 维度 | 描述 |
|------|------|
| 年龄 | 30-40 岁 |
| 经验 | 10 年+互联网/科技行业 |
| 材料 | 几十个 PPT（产品规划、竞品分析）、PRD 文档、项目复盘、绩效自评、年终总结 |
| 技术水平 | 会用工具，但不写代码；能用 AI 但不擅长 prompt 工程 |
| 痛点 | 经历丰富但不知从何说起；材料散落在各处；不会用"简历语言"包装 |

**典型场景：** 想跳槽看机会，打开招聘网站看到心仪岗位，但发现自己连一份能看的简历都没有。过去的十年做了一大堆事，可要说"我做了什么、取得了什么成果"，脑子里一片空白。

### 2.2 扩展用户：任何需要写简历的人

- 刚毕业的学生：有实习经历和项目，但不知道怎么组织
- 转行的人：有相关经验但不知道怎么关联到新领域
- 不经常写简历的人：上次写简历是 5 年前，格式和表达都过时了

### 2.3 痛点优先级

| 痛点 | 严重程度 | 频率 | MVP 是否解决 |
|------|---------|------|-------------|
| 材料太多太散，不知从何整理 | ⭐⭐⭐⭐⭐ | 高 | ✅ 批量上传 + AI 提炼 |
| 不知道怎么用"简历语言"描述经历 | ⭐⭐⭐⭐⭐ | 高 | ✅ AI 生成 |
| 一份简历投所有岗位，命中率低 | ⭐⭐⭐⭐ | 中 | ✅ JD 匹配优化 |
| 不会写自我介绍/项目描述 | ⭐⭐⭐⭐ | 中 | ✅ STAR 模板 |
| 担心隐私泄露 | ⭐⭐⭐ | 低 | ✅ 本地优先 |

---

## 3. 核心功能设计

### 3.1 材料上传（P0）

**目标：** 用户不用思考，把所有东西扔进来就行。

**支持格式：**
- PDF（报告、简历、证书）
- PPT/PPTX（产品规划、汇报、培训材料）
- Word/DOCX（PRD、文档、总结）
- 图片（PNG/JPG/JPEG，截图、照片——走 OCR）
- 纯文本（Markdown、TXT）

**交互设计：**
```
┌─────────────────────────────────────────────┐
│                                             │
│        📂 拖拽文件到这里，或者点击选择        │
│                                             │
│     支持 PDF / PPT / Word / 图片 / 文本      │
│          可一次上传多个文件                   │
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  产品规划  │  │ 竞品分析  │  │  年终总结  │  │
│  │  2.3 MB  │  │  5.1 MB  │  │  1.2 MB  │  │
│  │   PPT    │  │   PDF    │  │   DOCX   │  │
│  └──────────┘  └──────────┘  └──────────┘  │
│                                             │
│  已选 3 个文件，共 8.6 MB    [开始锻造 →]    │
│                                             │
└─────────────────────────────────────────────┘
```

**技术要点：**
- 前端：react-dropzone，拖拽 + 点击上传
- 后端：文件存储在 `uploads/{session_id}/` 目录
- 大文件分片上传（>50MB），前端分片，后端合并
- 文件类型校验 + 大小限制（单文件 100MB，总计 500MB）

### 3.2 AI 经历提炼（P0）— 核心功能

**目标：** 从海量材料中自动提取结构化的职业经历。

**提炼维度：**

```typescript
interface ExtractedExperience {
  // 基本信息
  companies: Company[];           // 工作过的公司
  roles: Role[];                  // 担任过的职位
  timeRange: { start: string; end: string };  // 整体时间线

  // 项目经历
  projects: Project[];            // 参与的项目（STAR 结构）

  // 技能
  skills: Skill[];                // 技术技能
  methodologies: string[];        // 方法论（敏捷、OKR、A/B测试等）
  tools: string[];                // 工具（Axure、JIRA、SQL等）

  // 管理
  teamSize?: number;              // 管理团队规模
  managementScope?: string;       // 管理范围描述

  // 成果
  achievements: Achievement[];    // 量化成果
  keyDecisions: string[];         // 关键决策
  impact: string[];               // 影响力描述

  // 教育
  education?: Education[];
}

interface Project {
  name: string;
  company?: string;
  timeRange: { start: string; end: string };
  role: string;
  // STAR 结构
  situation: string;   // 背景和挑战
  task: string;        // 任务和目标
  action: string;      // 采取的行动
  result: string;      // 量化的成果
  // 元数据
  sourceFiles: string[];  // 来自哪些原始材料
  confidence: number;     // AI 置信度 0-1
}
```

**交互设计：**
- 上传后自动开始分析，无需手动触发
- 实时进度展示：当前正在分析第几个文件 / 共几个文件
- 分析完成后展示提炼结果卡片，支持逐项编辑、删除、合并

### 3.3 简历生成（P0）

**目标：** 基于提炼的经历，一键生成结构化简历。

**生成内容：**
1. **个人总结** — 2-3 句话概括核心优势（AI 自动生成，可编辑）
2. **工作经历** — 按时间倒序，每段经历包含公司、职位、时间、核心职责
3. **项目经历** — 按 STAR 法则组织，最多 5 个最相关项目
4. **技能标签** — 分为技术技能、方法论、工具三类
5. **数据成果** — 量化的关键成果（如"DAU 提升 40%"、"团队从 3 人扩展到 15 人"）

**简历编辑器：**
- 左侧：结构化编辑面板（每个模块可展开/折叠/编辑）
- 右侧：实时预览（所见即所得）
- 支持拖拽排序模块顺序
- 支持调整每个项目经历的详细程度（精简/标准/详细）

### 3.4 岗位匹配优化（P0）

**目标：** 粘贴目标岗位 JD，AI 自动调整简历措辞。

**流程：**
```
用户粘贴 JD → AI 分析岗位关键词和要求 → 
对比当前简历 → 生成优化建议 + 自动改写版本
```

**优化策略：**
- **关键词对齐：** 确保 JD 中的关键词出现在简历中（如"数据驱动""B端产品""商业化"）
- **措辞调整：** 将通用描述调整为贴合岗位的表达
- **优先级重排：** 把最相关的经历排到前面
- **补充缺失：** 如果 JD 要求某能力但简历未体现，给出补充建议（而非编造）

**交互：**
- 左侧：JD 输入框 + 岗位关键词提取结果
- 右侧：优化前/后对比（diff 视图）
- 用户可逐条接受/拒绝优化建议

### 3.5 导出（P0）

**支持格式：**
- **PDF** — 使用 WeasyPrint（Python 端）或浏览器 print
- **Word (DOCX)** — 使用 python-docx 生成
- **纯文本 (TXT)** — Markdown 格式导出

**模板：**
- MVP 提供 2 个内置模板（简洁版 / 详细版）
- 模板定义简历的排版样式，不影响内容结构

### 3.6 面试模拟（P1）

- AI 扮演面试官，基于用户真实经历生成面试问题
- 对话式交互，用户回答后 AI 给出评价和改进建议
- 问题类型：行为面试（STAR）、技术深度、情景模拟

### 3.7 常见问题准备（P1）

- 自动生成高频面试题的标准答案
- 题目来源：用户提炼的经历 + 常见面试题库
- 支持自定义问题

### 3.8 简历版本管理（P2）

- 同一份材料，针对不同岗位生成多个简历版本
- 版本间可对比差异
- 历史版本可回滚

### 3.9 能力图谱 vs 岗位对比（P2）

- 可视化展示个人能力雷达图
- 支持叠加多个岗位要求进行对比
- 帮助用户发现能力差距

---

## 4. 信息架构

### 4.1 页面结构

```
ResumeForge
├── /                    # 首页（项目介绍 + 新建会话）
├── /workspace/:id       # 工作区（核心页面）
│   ├── 上传面板          # 材料上传区域
│   ├── 分析进度          # AI 提炼进度
│   ├── 经历提炼结果      # 结构化经历展示
│   ├── 简历编辑器        # 左编辑 + 右预览
│   ├── 岗位匹配          # JD 输入 + 优化建议
│   └── 导出             # 格式选择 + 下载
├── /settings            # 设置（API Key、默认模型、导出偏好）
└── /history             # 历史会话列表
```

### 4.2 导航设计

采用**单页工作区**模式，不搞多页面跳转：

```
┌──────────────────────────────────────────────────┐
│  ResumeForge    [会话: 网易产品经理]    [设置] ⚙️  │
├────────┬─────────────────────────────────────────┤
│        │                                         │
│  📤上传 │          主工作区                        │
│  🔍分析 │      （根据当前步骤动态切换）             │
│  ✏️编辑 │                                         │
│  🎯匹配 │                                         │
│  📥导出 │                                         │
│        │                                         │
│        │                                         │
├────────┴─────────────────────────────────────────┤
│  状态栏：已上传 12 个文件 | 已提炼 8 个项目 | ...  │
└──────────────────────────────────────────────────┘
```

左侧步骤导航引导用户走完整个流程，当前步骤高亮，完成的步骤打勾。

---

## 5. AI 蒸馏流程（核心）

这是整个产品的大脑。从散乱材料到结构化经历，分 4 个阶段。

### 5.1 整体 Pipeline

```
┌─────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ 原始材料  │───→│ 文档解析  │───→│ 文本分段  │───→│ AI 提炼  │───→│ 结构化存储│
│ PDF/PPT  │    │ PDF→Text │    │ 智能分块  │    │ Prompt   │    │ SQLite   │
│ Word/图片│    │ PPT→Text │    │ 去重去噪  │    │ Chain    │    │ JSON     │
│ 文本     │    │ OCR      │    │ 语义分段  │    │          │    │          │
└─────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
```

### 5.2 阶段一：文档解析

**目标：** 把各种格式统一转为纯文本。

| 格式 | 工具 | 处理策略 |
|------|------|---------|
| PDF | pdfplumber | 逐页提取文本，保留表格结构 |
| PPTX | python-pptx | 提取每页文本 + 备注 |
| DOCX | python-docx | 提取正文 + 表格 + 页眉页脚 |
| 图片 | PaddleOCR | 中文 OCR，保留布局信息 |
| 文本 | 直接读取 | 去除多余空白和特殊字符 |

**解析后输出格式：**
```json
{
  "file_name": "产品规划2024.pptx",
  "file_type": "pptx",
  "pages": [
    {
      "page_num": 1,
      "content": "2024年产品规划\n目标：DAU突破1000万\n...",
      "metadata": { "title": "封面" }
    }
  ],
  "total_chars": 15000
}
```

### 5.3 阶段二：文本分段

**目标：** 把长文本切成适合 AI 处理的语义段落。

**分段策略：**
1. **先按文档结构分** — PPT 按页，PDF/Word 按段落或标题
2. **合并短段落** — 相邻短段落（<100 字）合并
3. **拆分长段落** — 超过 2000 字的段落按语义边界拆分
4. **去重** — 相似度 > 0.9 的段落只保留一份（用 embedding 余弦相似度）
5. **去噪** — 去掉纯格式内容（页码、页眉页脚、"感谢观看"等）

**输出：** 每个分段 200-1500 字，带来源标记。

### 5.4 阶段三：AI 提炼（Prompt Chain）

这是最关键的部分。采用**多轮提炼策略**，逐步从文本中提取结构化信息。

#### Step 1：信息分类

**Prompt 模板：**
```
你是一个专业的简历分析师。以下是用户上传的职业材料中的一个片段。

请判断这个片段包含以下哪些类型的信息：
- A: 公司/职位信息（公司名、职位、在职时间）
- B: 项目经历（项目名、角色、时间、工作内容）
- C: 数据成果（量化指标、KPI 达成情况）
- D: 技能/工具/方法论
- E: 管理经验（团队规模、管理范围）
- F: 教育背景
- G: 其他（请说明）
- N: 无关信息（广告、格式内容等）

片段内容：
---
{chunk_text}
---

请以 JSON 格式输出：
{
  "categories": ["A", "B", "C"],
  "relevance": 0.85,
  "brief_summary": "一段话概括这个片段的核心内容"
}
```

#### Step 2：信息提取

对分类为 A-E 的片段，进行深度提取：

**Prompt 模板（项目经历提取）：**
```
你是一个专业的简历撰写顾问。请从以下材料片段中提取项目经历信息。

提取要求：
1. 项目名称（如果未明确，请根据内容合理概括）
2. 在项目中的角色
3. 项目时间（如果未明确，标注为"未知"）
4. 按以下维度提取（STAR 法则）：
   - Situation（背景）：项目面临的挑战或业务背景
   - Task（任务）：需要达成的目标
   - Action（行动）：采取的关键行动和决策
   - Result（结果）：量化的成果和数据

材料内容：
---
{chunk_text}
---

请以 JSON 格式输出：
{
  "projects": [{
    "name": "项目名称",
    "role": "产品负责人",
    "time_range": {"start": "2023-01", "end": "2023-12"},
    "situation": "...",
    "task": "...",
    "action": "...",
    "result": "..."
  }],
  "skills_mentioned": ["数据驱动", "A/B测试"],
  "tools_mentioned": ["SQL", "Axure"],
  "achievements": ["DAU提升40%", "营收增长2000万"],
  "confidence": 0.8
}

注意：
- 只提取材料中明确提到或可以合理推断的信息
- 不要编造数据
- 如果某字段无法提取，填写 null
- result 尽量包含量化数据
```

#### Step 3：信息合并与去重

多个片段可能提到同一个项目，需要合并：

**Prompt 模板：**
```
以下是 AI 从不同材料中提取的两个关于同一项目的信息：

来源1（来自"产品规划2024.pptx"第3页）：
{project_1}

来源2（来自"年终总结.docx"）：
{project_2}

请合并为一份完整的项目经历，要求：
1. 保留两个来源中所有独特信息
2. 解决冲突（如时间不一致，取更具体的）
3. 使用更专业的"简历语言"重新表述
4. 确保 STAR 结构完整
5. Result 部分优先使用量化数据

输出合并后的 JSON（格式同上）。
```

#### Step 4：简历语言改写

将原始表述转化为专业的简历表达：

**Prompt 模板：**
```
你是一个资深的简历优化专家。请将以下工作描述改写为更专业的简历语言。

改写原则：
1. 动词开头：用"主导""负责""设计""推动""优化"等
2. 量化成果：把模糊描述转为数据（如"提升了用户体验"→"NPS从35提升至52"）
3. 突出影响：强调对业务的影响和决策的作用
4. 精简有力：每条描述控制在2行以内
5. 不夸大不编造：基于原文改写，不添加原文没有的信息

原始描述：
---
{raw_description}
---

改写后的简历描述：
```

### 5.5 阶段四：结构化存储

将 AI 提炼结果存入 SQLite，同时保留与原始材料的关联关系。

---

## 6. 简历生成策略

### 6.1 生成流程

```
结构化经历 ──→ 选择目标岗位 ──→ 经历筛选 ──→ 内容编排 ──→ 语言润色 ──→ 最终简历
                  │               │              │              │
                  │               │              │              └── AI 改写
                  │               │              └── STAR模板填充
                  │               └── 相关性排序（AI 打分）
                  └── JD 关键词提取
```

### 6.2 经历筛选策略

当用户粘贴 JD 时：

1. **提取岗位关键词** — 岗位要求的核心能力（如"数据驱动""商业化""B端产品""团队管理"）
2. **给每个项目经历打分** — 与岗位关键词的匹配度
3. **按匹配度排序** — 最相关的排前面
4. **截取 Top N** — 根据简历长度限制，选择 3-5 个最相关项目

**Prompt（相关性打分）：**
```
以下是目标岗位的 JD 关键词和候选项目经历：

岗位关键词：{jd_keywords}
候选项目：
{project}

请评估这个项目经历与目标岗位的相关性，输出：
{
  "relevance_score": 0.85,
  "matching_points": ["数据驱动决策", "商业化经验"],
  "gaps": ["缺少 B 端经验"],
  "suggested_adjustments": "突出商业化成果，弱化 C 端内容"
}
```

### 6.3 简历模板系统

模板定义简历的**视觉排版**，不影响内容结构：

```typescript
interface ResumeTemplate {
  id: string;
  name: string;
  sections: SectionConfig[];  // 各模块的显示配置
  style: {
    fontFamily: string;
    colors: { primary: string; secondary: string };
    spacing: 'compact' | 'normal' | 'relaxed';
  };
}

interface SectionConfig {
  type: 'summary' | 'experience' | 'projects' | 'skills' | 'education';
  visible: boolean;
  maxItems: number;  // 最多显示几个
  detailLevel: 'brief' | 'standard' | 'detailed';
}
```

MVP 提供两个模板：
- **简洁版：** 1 页，精简描述，适合初级岗位
- **详细版：** 2 页，STAR 完整展开，适合资深岗位

---

## 7. 技术架构

### 7.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                      Browser (React)                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ 上传组件  │ │ 编辑器    │ │ 预览组件  │ │ 导出组件  │   │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘   │
│       └─────────────┴────────────┴────────────┘         │
│                         │ HTTP/SSE                       │
├─────────────────────────┼───────────────────────────────┤
│                   FastAPI Backend                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ 文件上传  │ │ 文档解析  │ │ AI 引擎   │ │ 简历生成  │   │
│  │ /upload  │ │ Parser   │ │ LLM Chain │ │ Generator│   │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘   │
│       │            │            │              │         │
│  ┌────┴─────┐ ┌────┴─────┐     │        ┌────┴─────┐   │
│  │ 文件存储  │ │ 文本分块  │     │        │ 导出引擎  │   │
│  │ uploads/ │ │ Chunker  │     │        │ PDF/Word │   │
│  └──────────┘ └──────────┘     │        └──────────┘   │
│                                │                        │
│                     ┌──────────┴──────────┐             │
│                     │     LiteLLM          │             │
│                     │  OpenAI / Anthropic  │             │
│                     │  智谱 / MiniMax      │             │
│                     └─────────────────────┘             │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │                   SQLite                          │   │
│  │  users | sessions | files | chunks | experiences  │   │
│  │  resumes | projects | skills | achievements       │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 7.2 前端架构

```
src/
├── components/          # UI 组件
│   ├── Upload/          # 文件上传
│   ├── Analysis/        # 分析进度
│   ├── Editor/          # 简历编辑器
│   ├── Preview/         # 实时预览
│   ├── Matching/        # 岗位匹配
│   └── Export/          # 导出
├── hooks/               # 自定义 hooks
│   ├── useUpload.ts
│   ├── useAnalysis.ts   # SSE 连接，实时进度
│   └── useResume.ts
├── stores/              # 状态管理（Zustand）
│   └── sessionStore.ts
├── types/               # TypeScript 类型定义
├── api/                 # API 客户端
└── pages/
    └── Workspace.tsx    # 主工作区
```

### 7.3 后端架构

```
backend/
├── main.py              # FastAPI 入口
├── config.py            # 配置管理
├── api/                 # API 路由
│   ├── upload.py
│   ├── analysis.py
│   ├── resume.py
│   └── export.py
├── services/            # 业务逻辑
│   ├── parser/          # 文档解析
│   │   ├── pdf_parser.py
│   │   ├── pptx_parser.py
│   │   ├── docx_parser.py
│   │   └── ocr_parser.py
│   ├── chunker.py       # 文本分段
│   ├── ai/              # AI 引擎
│   │   ├── client.py    # LiteLLM 封装
│   │   ├── chains.py    # Prompt Chain
│   │   └── prompts.py   # Prompt 模板
│   ├── resume_gen.py    # 简历生成
│   └── exporter/        # 导出引擎
│       ├── pdf_exporter.py
│       ├── docx_exporter.py
│       └── txt_exporter.py
├── models/              # 数据模型（SQLAlchemy）
└── db.py                # 数据库连接
```

---

## 8. 数据模型

### 8.1 核心表结构

```sql
-- 用户（MVP 单用户，后续扩展多用户）
CREATE TABLE users (
    id TEXT PRIMARY KEY DEFAULT 'default',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    settings JSON  -- 默认模型、导出偏好等
);

-- 工作会话（一次简历锻造过程）
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    name TEXT,                    -- 会话名称，如"网易产品经理"
    status TEXT DEFAULT 'upload', -- upload | analyzing | editing | exporting | done
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 上传的原始文件
CREATE TABLE files (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES sessions(id),
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,      -- pdf | pptx | docx | image | text
    file_path TEXT NOT NULL,      -- 本地存储路径
    file_size INTEGER,
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    parse_status TEXT DEFAULT 'pending',  -- pending | parsing | done | error
    parse_error TEXT
);

-- 解析后的文本分段
CREATE TABLE chunks (
    id TEXT PRIMARY KEY,
    file_id TEXT REFERENCES files(id),
    session_id TEXT REFERENCES sessions(id),
    content TEXT NOT NULL,
    chunk_index INTEGER,          -- 在文件中的顺序
    char_count INTEGER,
    categories TEXT,              -- JSON array: ["B", "C", "D"]
    relevance REAL DEFAULT 0.0,   -- AI 判断的相关性
    summary TEXT                  -- AI 生成的简要摘要
);

-- 提炼出的公司/职位经历
CREATE TABLE companies (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES sessions(id),
    company_name TEXT,
    position TEXT,
    start_date TEXT,
    end_date TEXT,
    is_current BOOLEAN DEFAULT FALSE,
    source_chunk_ids TEXT         -- JSON array
);

-- 提炼出的项目经历（核心）
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES sessions(id),
    company_id TEXT REFERENCES companies(id),
    name TEXT NOT NULL,
    role TEXT,
    start_date TEXT,
    end_date TEXT,
    situation TEXT,               -- STAR: 背景
    task TEXT,                    -- STAR: 任务
    action TEXT,                  -- STAR: 行动
    result TEXT,                  -- STAR: 结果
    raw_result TEXT,              -- 原始表述（改写前）
    confidence REAL DEFAULT 0.0,
    source_chunk_ids TEXT,        -- JSON array
    source_file_ids TEXT,         -- JSON array
    is_selected BOOLEAN DEFAULT TRUE,  -- 是否入选简历
    display_order INTEGER
);

-- 提炼出的技能
CREATE TABLE skills (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES sessions(id),
    name TEXT NOT NULL,
    category TEXT,                -- technical | methodology | tool
    source_chunk_ids TEXT,
    proficiency TEXT              -- beginner | intermediate | advanced | expert
);

-- 提炼出的量化成果
CREATE TABLE achievements (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES sessions(id),
    description TEXT NOT NULL,
    metric TEXT,                  -- 如 "DAU提升40%"
    project_id TEXT REFERENCES projects(id),
    source_chunk_ids TEXT
);

-- 生成的简历
CREATE TABLE resumes (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES sessions(id),
    name TEXT,
    target_jd TEXT,               -- 目标岗位 JD
    jd_keywords TEXT,             -- JSON array
    template_id TEXT,
    content JSON NOT NULL,        -- 完整简历内容（结构化）
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 简历中的模块配置
CREATE TABLE resume_sections (
    id TEXT PRIMARY KEY,
    resume_id TEXT REFERENCES resumes(id),
    type TEXT NOT NULL,           -- summary | experience | projects | skills | education
    visible BOOLEAN DEFAULT TRUE,
    display_order INTEGER,
    config JSON                   -- 模块特有配置
);
```

### 8.2 索引

```sql
CREATE INDEX idx_chunks_session ON chunks(session_id);
CREATE INDEX idx_chunks_file ON chunks(file_id);
CREATE INDEX idx_projects_session ON projects(session_id);
CREATE INDEX idx_resumes_session ON resumes(session_id);
```

---

## 9. API 设计

### 9.1 API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| **会话** | | |
| POST | /api/sessions | 创建工作会话 |
| GET | /api/sessions | 列出所有会话 |
| GET | /api/sessions/{id} | 获取会话详情 |
| DELETE | /api/sessions/{id} | 删除会话 |
| **上传** | | |
| POST | /api/sessions/{id}/files | 上传文件（multipart） |
| GET | /api/sessions/{id}/files | 列出已上传文件 |
| DELETE | /api/sessions/{id}/files/{fid} | 删除文件 |
| **分析** | | |
| POST | /api/sessions/{id}/analyze | 触发 AI 分析（返回 task_id） |
| GET | /api/sessions/{id}/analyze/{task_id}/status | 查询分析进度 |
| GET | /api/sessions/{id}/analyze/{task_id}/stream | SSE 实时进度流 |
| **经历** | | |
| GET | /api/sessions/{id}/projects | 列出提炼的项目 |
| PUT | /api/sessions/{id}/projects/{pid} | 编辑项目 |
| DELETE | /api/sessions/{id}/projects/{pid} | 删除项目 |
| POST | /api/sessions/{id}/projects/{pid}/rewrite | AI 改写某条经历 |
| GET | /api/sessions/{id}/skills | 列出提炼的技能 |
| GET | /api/sessions/{id}/achievements | 列出提炼的成果 |
| **简历** | | |
| POST | /api/sessions/{id}/resumes | 生成简历 |
| GET | /api/sessions/{id}/resumes | 列出简历版本 |
| GET | /api/sessions/{id}/resumes/{rid} | 获取简历内容 |
| PUT | /api/sessions/{id}/resumes/{rid} | 更新简历内容 |
| **岗位匹配** | | |
| POST | /api/sessions/{id}/match | 提交 JD，获取匹配分析 |
| POST | /api/sessions/{id}/resumes/{rid}/optimize | AI 优化简历 |
| **导出** | | |
| GET | /api/sessions/{id}/resumes/{rid}/export/pdf | 导出 PDF |
| GET | /api/sessions/{id}/resumes/{rid}/export/docx | 导出 Word |
| GET | /api/sessions/{id}/resumes/{rid}/export/txt | 导出纯文本 |

### 9.2 关键 API 详细设计

#### POST /api/sessions/{id}/analyze

触发 AI 分析，返回 task_id 用于查询进度。

**Response:**
```json
{
  "task_id": "task_abc123",
  "status": "started",
  "total_files": 12,
  "message": "开始分析 12 个文件"
}
```

#### GET /api/sessions/{id}/analyze/{task_id}/stream

SSE 实时进度流：

```
event: progress
data: {"stage": "parsing", "current": 3, "total": 12, "file": "产品规划.pptx"}

event: progress
data: {"stage": "chunking", "current": 45, "total": null}

event: progress
data: {"stage": "analyzing", "current": 10, "total": 45, "project": "用户增长项目"}

event: result
data: {"projects_found": 8, "skills_found": 23, "achievements_found": 15}

event: done
data: {"task_id": "task_abc123", "status": "completed"}
```

#### POST /api/sessions/{id}/match

提交 JD 进行岗位匹配：

**Request:**
```json
{
  "jd_text": "岗位：高级产品经理\n要求：5年以上产品经验，熟悉B端SaaS..."
}
```

**Response:**
```json
{
  "keywords": ["B端", "SaaS", "数据驱动", "商业化", "团队管理"],
  "project_scores": [
    {"project_id": "p1", "name": "企业CRM", "score": 0.92, "reason": "高度匹配 B 端 SaaS 经验"},
    {"project_id": "p2", "name": "用户增长", "score": 0.65, "reason": "数据驱动相关，但偏 C 端"}
  ],
  "suggestions": [
    "建议将企业CRM项目排到第一位",
    "JD要求商业化经验，可在成果部分补充营收数据",
    "缺少 PaaS/中台相关经验，可在技能部分补充"
  ]
}
```

---

## 10. 项目目录结构

```
resume-forge/
├── README.md
├── PRD.md                          # 本文档
├── .env.example                    # 环境变量模板
├── docker-compose.yml              # 可选：Docker 部署
│
├── frontend/                       # React 前端
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── components/
│       │   ├── Layout/
│       │   │   ├── Sidebar.tsx          # 左侧步骤导航
│       │   │   ├── StatusBar.tsx        # 底部状态栏
│       │   │   └── Header.tsx
│       │   ├── Upload/
│       │   │   ├── DropZone.tsx         # 拖拽上传区域
│       │   │   ├── FileList.tsx         # 文件列表
│       │   │   └── UploadProgress.tsx
│       │   ├── Analysis/
│       │   │   ├── ProgressPanel.tsx    # 分析进度面板
│       │   │   └── ExperienceCards.tsx  # 提炼结果卡片
│       │   ├── Editor/
│       │   │   ├── ResumeEditor.tsx     # 简历编辑器主体
│       │   │   ├── SectionEditor.tsx    # 各模块编辑
│       │   │   └── ProjectCard.tsx      # 项目经历编辑卡片
│       │   ├── Preview/
│       │   │   ├── ResumePreview.tsx    # 简历预览
│       │   │   └── TemplateRenderer.tsx # 模板渲染
│       │   ├── Matching/
│       │   │   ├── JDInput.tsx          # JD 输入
│       │   │   ├── MatchResult.tsx      # 匹配结果
│       │   │   └── DiffView.tsx         # 优化前后对比
│       │   └── Export/
│       │       └── ExportPanel.tsx
│       ├── hooks/
│       │   ├── useUpload.ts
│       │   ├── useAnalysis.ts           # SSE 连接
│       │   ├── useResume.ts
│       │   └── useSSE.ts               # 通用 SSE hook
│       ├── stores/
│       │   └── sessionStore.ts          # Zustand store
│       ├── api/
│       │   └── client.ts                # Axios/fetch 封装
│       ├── types/
│       │   └── index.ts                 # 共享类型
│       └── pages/
│           ├── Home.tsx
│           └── Workspace.tsx            # 主工作区
│
├── backend/                        # FastAPI 后端
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── main.py                      # FastAPI app
│   ├── config.py                    # 配置（环境变量）
│   ├── db.py                        # SQLAlchemy setup
│   ├── api/
│   │   ├── __init__.py
│   │   ├── sessions.py
│   │   ├── upload.py
│   │   ├── analysis.py
│   │   ├── projects.py
│   │   ├── resume.py
│   │   ├── matching.py
│   │   └── export.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── parser/
│   │   │   ├── __init__.py
│   │   │   ├── base.py              # Parser 基类
│   │   │   ├── pdf_parser.py
│   │   │   ├── pptx_parser.py
│   │   │   ├── docx_parser.py
│   │   │   ├── image_parser.py       # OCR
│   │   │   └── text_parser.py
│   │   ├── chunker.py               # 文本分段
│   │   ├── dedup.py                 # 去重
│   │   ├── ai/
│   │   │   ├── __init__.py
│   │   │   ├── client.py            # LiteLLM 封装
│   │   │   ├── chains.py            # 提炼 pipeline
│   │   │   ├── prompts/
│   │   │   │   ├── classify.py      # 信息分类 prompt
│   │   │   │   ├── extract.py       # 信息提取 prompt
│   │   │   │   ├── merge.py         # 合并去重 prompt
│   │   │   │   ├── rewrite.py       # 简历语言改写 prompt
│   │   │   │   ├── match.py         # 岗位匹配 prompt
│   │   │   │   └── generate.py      # 简历生成 prompt
│   │   │   └── types.py             # AI 输出类型
│   │   ├── resume_gen.py            # 简历生成逻辑
│   │   └── exporter/
│   │       ├── __init__.py
│   │       ├── pdf_exporter.py
│   │       ├── docx_exporter.py
│   │       └── txt_exporter.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── session.py
│   │   ├── file.py
│   │   ├── chunk.py
│   │   ├── company.py
│   │   ├── project.py
│   │   ├── skill.py
│   │   ├── achievement.py
│   │   └── resume.py
│   ├── tasks/
│   │   ├── __init__.py
│   │   └── analyze.py               # 分析任务（后台执行）
│   └── templates/                   # 简历模板
│       ├── simple.html              # 简洁版
│       └── detailed.html            # 详细版
│
├── data/                           # 运行时数据（gitignore）
│   ├── uploads/                    # 上传文件
│   └── resume_forge.db             # SQLite 数据库
│
└── scripts/
    ├── setup.sh                    # 初始化脚本
    └── seed.py                     # 测试数据填充
```

---

## 11. MVP 范围和迭代计划

### MVP 范围（P0）

| 功能 | 包含 |
|------|------|
| 材料上传 | ✅ 批量上传、拖拽、进度展示 |
| 文档解析 | ✅ PDF、PPTX、DOCX、图片 OCR、文本 |
| AI 提炼 | ✅ 分类 + 提取 + 合并 + 改写 |
| 简历编辑 | ✅ 结构化编辑 + 实时预览 |
| 岗位匹配 | ✅ JD 解析 + 相关性排序 + 优化建议 |
| 导出 | ✅ PDF、Word、纯文本 |
| 模板 | ✅ 2 个内置模板 |

### 按天迭代计划（5 天 MVP）

#### Day 1：基础框架 + 文件上传 + 文档解析

- [ ] 前端项目初始化（Vite + React + TS + Tailwind）
- [ ] 后端项目初始化（FastAPI + SQLAlchemy + SQLite）
- [ ] 文件上传 API（POST /files）
- [ ] 文档解析器：PDF（pdfplumber）、DOCX（python-docx）、纯文本
- [ ] 前端上传组件（react-dropzone）
- [ ] 基础页面布局（Header + Sidebar + 主工作区）

**产出：** 能上传文件并看到解析后的文本内容。

#### Day 2：PPT 解析 + OCR + 文本分段 + AI 基础对接

- [ ] PPTX 解析器（python-pptx）
- [ ] 图片 OCR（PaddleOCR 或调用视觉模型 API）
- [ ] 文本分段服务（按文档结构 + 智能分块）
- [ ] LiteLLM 集成（多模型支持）
- [ ] AI 信息分类 Prompt（Step 1）
- [ ] 分析进度 SSE 推送

**产出：** 上传材料后能自动分段，AI 能判断每段的内容类型。

#### Day 3：AI 提炼完整 Pipeline

- [ ] AI 信息提取 Prompt（Step 2：项目、技能、成果）
- [ ] AI 合并去重 Prompt（Step 3）
- [ ] AI 简历语言改写 Prompt（Step 4）
- [ ] 结构化存储（写入 SQLite）
- [ ] 提炼结果展示（项目卡片、技能标签、成果列表）
- [ ] 基础编辑功能（修改、删除、排序）

**产出：** 上传材料后能自动提炼出结构化的职业经历。

#### Day 4：简历生成 + 岗位匹配

- [ ] 简历生成逻辑（经历筛选 + 内容编排）
- [ ] 简历编辑器（左编辑 + 右预览）
- [ ] JD 关键词提取
- [ ] 岗位相关性打分
- [ ] 优化建议生成
- [ ] 简历模板系统（2 个模板）

**产出：** 能生成完整简历，能粘贴 JD 获取优化建议。

#### Day 5：导出 + 打磨

- [ ] PDF 导出（WeasyPrint 或浏览器 print）
- [ ] Word 导出（python-docx）
- [ ] 纯文本导出
- [ ] UI 打磨（动画、交互细节、错误处理）
- [ ] 增量处理（支持追加新材料）
- [ ] 基础设置页面（API Key 配置）
- [ ] 测试 + Bug 修复

**产出：** 可用的 MVP。

---

## 12. 风险和应对

| 风险 | 影响 | 概率 | 应对策略 |
|------|------|------|---------|
| **AI 提炼质量不稳定** | 核心功能不可用 | 中 | 1. Prompt 多轮迭代调优 2. 支持用户手动编辑修正 3. 置信度低的结果标注"待确认" |
| **文档解析失败** | 部分材料无法处理 | 中 | 1. 扫描版 PDF 走 OCR 兜底 2. 解析失败时保留原始文件供用户手动输入 3. 进度条展示失败文件 |
| **LLM API 成本高** | 用户使用成本超预期 | 低 | 1. 文本分段减少 token 消耗 2. 支持本地模型（Ollama）3. 分类阶段用便宜模型，改写阶段用贵模型 |
| **材料中信息不足** | 生成的简历太空洞 | 中 | 1. 在编辑器中提示用户补充信息 2. 提供"补充说明"输入框 3. 不编造，诚实标注"待补充" |
| **中文 OCR 质量差** | 图片材料提取失败 | 中 | 1. 用 PaddleOCR（中文优化）2. 失败时提示用户手动转录 3. 支持直接粘贴文本作为补充 |
| **大文件处理慢** | 用户体验差 | 低 | 1. 后台异步处理 + SSE 实时进度 2. 支持分片上传 3. 文件大小限制提示 |
| **隐私泄露** | 用户不信任产品 | 低 | 1. 本地优先，材料不上传到第三方 2. LLM API 调用仅发送文本片段 3. 支持纯本地模式（Ollama） |

### 降级方案

如果 AI 提炼完全失败（比如 LLM 不可用），系统仍然可以：
1. 正常上传和解析文档
2. 展示解析后的文本内容
3. 用户手动复制粘贴到简历模板中
4. 至少提供一个"文本转简历模板"的格式化工具

---

## 附录

### A. 技术选型明细

| 类别 | 选择 | 理由 |
|------|------|------|
| 前端框架 | React + TypeScript | 罡哥有 TS 经验，生态成熟 |
| 构建工具 | Vite | 快，开箱即用 |
| 样式 | Tailwind CSS | 快速开发，设计一致 |
| 状态管理 | Zustand | 轻量，比 Redux 简单 |
| UI 组件 | Radix UI + shadcn/ui | 高质量、可定制 |
| 后端框架 | FastAPI | 异步、类型安全、自动文档 |
| ORM | SQLAlchemy 2.0 | 成熟、异步支持 |
| LLM 接入 | LiteLLM | 统一接口，支持多模型 |
| PDF 解析 | pdfplumber | 表格支持好 |
| PPT 解析 | python-pptx | 官方推荐 |
| Word 生成 | python-docx | 功能完整 |
| OCR | PaddleOCR | 中文识别优秀 |
| PDF 导出 | WeasyPrint | CSS 转 PDF |
| 任务队列 | 内置 asyncio（MVP） | 不引入 Celery 等重依赖 |

### B. 环境变量

```env
# LLM 配置
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
ZHIPU_API_KEY=
MINIMAX_API_KEY=
DEFAULT_MODEL=zhipu/glm-4

# 应用配置
DATABASE_URL=sqlite:///data/resume_forge.db
UPLOAD_DIR=data/uploads
MAX_FILE_SIZE=104857600  # 100MB
MAX_TOTAL_SIZE=524288000  # 500MB

# 可选：本地模型
OLLAMA_BASE_URL=http://localhost:11434
```

### C. 开发命令速查

```bash
# 后端
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev  # http://localhost:5173

# 数据库迁移（如果用 Alembic）
alembic upgrade head
```
