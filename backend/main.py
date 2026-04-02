"""
碳融智核平台 - FastAPI后端入口
启动方式: python main.py 或 uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings

# 导入所有路由
from routers import auth, carbon, esg, finance, reports, ocr, enterprise, carbon_manage, dashboard, risk

# 创建FastAPI应用
app = FastAPI(
    title="碳融智核 - ESG数据智能管理平台 API",
    description="""
    专为中小企业打造的ESG数据自动化与绿色金融赋能平台。

    ## 功能模块
    - **用户认证**: 注册、登录、JWT鉴权
    - **碳排放核算**: 排放因子、行业基准、碳排放计算
    - **ESG评分**: 环境(E)、社会(S)、治理(G) 三维度评分
    - **金融产品**: 绿色金融产品浏览与申请
    - **报告生成**: 多模板报告自动生成
    - **OCR识别**: 票据智能识别（模拟）
    - **企业中心**: 企业概览、资质认证、数据权限、账号设置
    - **碳管理**: 数据上传、手动录入、能耗分析
    - **数据驾驶舱**: 碳排放监控、能耗结构、ESG看板、关键指标
    - **数据查询**: 政策法规、客户案例
    """,
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS中间件（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)
app.include_router(carbon.router)
app.include_router(esg.router)
app.include_router(finance.router)
app.include_router(reports.router)
app.include_router(ocr.router)
app.include_router(enterprise.router)
app.include_router(carbon_manage.router)
app.include_router(dashboard.router)
app.include_router(risk.router)


# 根路径
@app.get("/", tags=["系统"])
def root():
    return {
        "name": "碳融智核 API",
        "version": "2.2.0",
        "status": "running",
        "docs": "/docs",
    }


# 健康检查
@app.get("/health", tags=["系统"])
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_DEBUG,
    )
