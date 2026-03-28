# 碳融智核 - FastAPI 后端

## 项目结构

```
backend/
├── main.py              # FastAPI入口（启动文件）
├── config.py            # 配置管理
├── database.py          # 数据库连接
├── init_db.py           # 数据库初始化 & 种子数据
├── requirements.txt     # Python依赖
├── .env                 # 环境变量配置
├── models/              # SQLAlchemy 数据模型
│   ├── user.py          # 用户表
│   ├── carbon.py        # 排放因子/行业基准/碳记录
│   ├── esg.py           # ESG评分记录
│   ├── finance.py       # 金融产品/申请
│   └── report.py        # 报告/政策/案例/联系
├── schemas/             # Pydantic 请求/响应模型
│   ├── user.py
│   ├── carbon.py
│   ├── esg.py
│   ├── finance.py
│   └── report.py
├── routers/             # API路由
│   ├── auth.py          # 注册 / 登录 / 个人信息
│   ├── carbon.py        # 碳排放核算
│   ├── esg.py           # ESG三维度评分
│   ├── finance.py       # 金融产品
│   ├── reports.py       # 报告 / 政策 / 案例 / 联系
│   └── ocr.py           # OCR票据识别
└── utils/
    ├── auth.py          # JWT / 密码工具
    └── calculator.py    # ESG计算引擎
```

## 快速启动

### 1. 安装 Python 依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 安装并配置 MySQL

确保本机已安装 MySQL，然后创建数据库：

```sql
CREATE DATABASE carbon_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. 修改 .env 配置

编辑 `.env` 文件，修改数据库密码等：

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=你的MySQL密码
DB_NAME=carbon_platform
JWT_SECRET_KEY=换一个安全的随机字符串
```

### 4. 初始化数据库

```bash
python init_db.py
```

这会自动创建所有表并插入种子数据（排放因子、行业基准、金融产品、政策、案例、演示用户）。

### 5. 启动后端

```bash
python main.py
```

服务将运行在 `http://localhost:8000`

### 6. 查看 API 文档

打开浏览器访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 接口总览

### 用户认证
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/login` | 用户登录 |
| GET  | `/api/auth/me` | 获取当前用户信息 |
| PUT  | `/api/auth/me` | 更新个人信息 |

### 碳排放核算
| 方法 | 路径 | 说明 |
|------|------|------|
| GET  | `/api/carbon/emission-factors` | 获取排放因子列表 |
| GET  | `/api/carbon/industry-benchmarks` | 获取行业基准数据 |
| POST | `/api/carbon/calculate` | 执行碳核算 |
| GET  | `/api/carbon/records` | 获取碳核算历史 |
| GET  | `/api/carbon/records/{id}` | 获取某条记录 |
| DELETE | `/api/carbon/records/{id}` | 删除某条记录 |

### ESG评分
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/esg/calculate/environment` | 计算环境(E)得分 |
| POST | `/api/esg/calculate/social` | 计算社会(S)得分 |
| POST | `/api/esg/calculate/governance` | 计算治理(G)得分 |
| POST | `/api/esg/calculate/total` | 综合ESG评估并保存 |
| GET  | `/api/esg/history` | 获取ESG评分历史 |
| GET  | `/api/esg/history/{id}` | 获取ESG评分详情 |

### 金融产品
| 方法 | 路径 | 说明 |
|------|------|------|
| GET  | `/api/finance/products` | 获取金融产品列表 |
| GET  | `/api/finance/products/{id}` | 获取产品详情 |
| POST | `/api/finance/apply` | 申请金融产品 |
| GET  | `/api/finance/applications` | 获取我的申请 |

### 报告 & 数据
| 方法 | 路径 | 说明 |
|------|------|------|
| GET  | `/api/reports/templates` | 获取报告模板 |
| POST | `/api/reports/generate` | 生成报告 |
| GET  | `/api/reports` | 获取报告历史 |
| GET  | `/api/reports/{id}` | 报告详情 |
| GET  | `/api/policies` | 获取政策法规 |
| GET  | `/api/cases` | 获取客户案例 |
| POST | `/api/contact` | 提交咨询消息 |

### OCR识别
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/ocr/recognize` | 上传票据OCR识别 |
| GET  | `/api/ocr/sample/{type}` | 获取示例识别结果 |

## 演示账号

- 邮箱: `demo@carbon-ai.com`
- 密码: `demo123`

## 前端对接

将前端 `script.js` 中的 `CONFIG.API_BASE_URL` 修改为后端地址：

```javascript
const CONFIG = {
    API_BASE_URL: 'http://localhost:8000',
    // ...
};
```

然后将前端的模拟API调用（如 `DataService.users.find(...)` ）替换为 `fetch()` 请求。
