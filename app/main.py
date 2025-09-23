from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from .database import database
from .api.ai_recommendations import router as ai_recommendations_router
from .api.matches import router as matches_router

# 加载环境变量
load_dotenv()

# 创建FastAPI应用实例
app = FastAPI(
    title="My App API",
    description="A simple FastAPI backend for Next.js frontend",
    version="1.0.0"
)

# 配置CORS中间件，允许Next.js前端访问
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(ai_recommendations_router, prefix="/api", tags=["AI Recommendations"])
app.include_router(matches_router, prefix="/api", tags=["Matches"])

# 根路径
@app.get("/")
async def root():
    return {"message": "FastAPI backend is running!"}

# Hello World API
@app.get("/api/hello")
async def hello_world():
    return {"message": "hello world"}

# 健康检查端点
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is working properly"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)