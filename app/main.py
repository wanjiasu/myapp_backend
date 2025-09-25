from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import asyncio
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from .database import database
from .api.ai_recommendations import router as ai_recommendations_router
from .api.matches import router as matches_router
from .api.telegram import router as telegram_router
from .services.telegram_service import telegram_service

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化 Telegram bot
    logger.info("正在初始化 Telegram bot...")
    if await telegram_service.initialize():
        # 在后台任务中启动 bot 轮询
        asyncio.create_task(telegram_service.start_polling())
        logger.info("Telegram bot 启动成功")
    else:
        logger.warning("Telegram bot 初始化失败")
    
    yield
    
    # 关闭时停止 Telegram bot
    logger.info("正在停止 Telegram bot...")
    await telegram_service.stop_polling()
    logger.info("Telegram bot 已停止")

# 创建FastAPI应用实例
app = FastAPI(
    title="My App API",
    description="A FastAPI backend with integrated Telegram bot",
    version="1.0.0",
    lifespan=lifespan
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
app.include_router(telegram_router, prefix="/api", tags=["Telegram"])

# 根路径
@app.get("/")
async def root():
    return {"message": "FastAPI backend with Telegram bot is running!"}

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