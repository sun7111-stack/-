# 碳融智核 - ESG智能评估平台

一个集碳排放核算、ESG三维度评估、绿色金融对接、AIGC报告生成于一体的智慧平台。

## 项目结构

```
├── index.html           # 前端主页面
├── style.css            # 前端样式
├── script.js            # 前端逻辑
├── api.js               # 前端API服务层
├── backend/             # FastAPI后端
│   ├── main.py          # 启动入口
│   ├── config.py        # 配置管理
│   ├── database.py      # 数据库连接
│   ├── init_db.py       # 建表 & 种子数据
│   ├── requirements.txt # Python依赖
│   ├── .env.example     # 环境变量模板
│   ├── models/          # 数据模型
│   ├── schemas/         # 请求/响应模型
│   ├── routers/         # API路由
│   └── utils/           # 工具函数
└── .gitignore
```

## 环境要求

- **Python** 3.10+
- **MySQL** 8.0+
- **浏览器**：Chrome / Edge / Firefox 等现代浏览器

## 快速部署指南

### 第一步：安装 MySQL

1. 下载安装 [MySQL 8.0](https://dev.mysql.com/downloads/mysql/)
2. 记住安装时设置的 root 密码

### 第二步：创建数据库

打开 MySQL 命令行或 Navicat 等工具，执行：

```sql
CREATE DATABASE carbon_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 第三步：配置后端环境变量

1. 进入 `backend/` 目录
2. 复制 `.env.example` 为 `.env`
3. 修改 `.env` 中的数据库密码为你自己的：

```
DB_PASSWORD=你的MySQL密码
```

### 第四步：安装 Python 依赖

```bash
cd backend
python -m venv .venv

# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 第五步：初始化数据库（建表 + 插入测试数据）

```bash
cd backend
python init_db.py
```

成功后会看到：
```
所有表创建成功！
排放因子数据已插入
行业基准数据已插入
...
```

### 第六步：启动后端服务

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

启动后访问 http://localhost:8000/docs 可查看API文档。

### 第七步：打开前端页面

直接用浏览器打开项目根目录下的 `index.html` 即可。

## 测试账号

| 邮箱 | 密码 |
|------|------|
| demo@carbon-ai.com | demo123 |

## API 端点一览

| 功能 | 方法 | 路径 |
|------|------|------|
| 用户登录 | POST | /api/auth/login |
| 用户注册 | POST | /api/auth/register |
| 获取个人信息 | GET | /api/auth/me |
| 碳排放核算 | POST | /api/carbon/calculate |
| ESG环境评分 | POST | /api/esg/calculate/environment |
| ESG社会评分 | POST | /api/esg/calculate/social |
| ESG治理评分 | POST | /api/esg/calculate/governance |
| ESG综合评估 | POST | /api/esg/calculate/total |
| 金融产品列表 | GET | /api/finance/products |
| 申请金融产品 | POST | /api/finance/apply |
| 生成报告 | POST | /api/reports/generate |
| 政策法规 | GET | /api/policies |
| 案例研究 | GET | /api/cases |
| OCR识别 | POST | /api/ocr/recognize |

## 技术栈

**前端**：HTML5 + CSS3 + JavaScript + Bootstrap 5.3 + ECharts 5.4 + Chart.js

**后端**：FastAPI + SQLAlchemy + PyMySQL + JWT认证

**数据库**：MySQL 8.0
