from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..services.telegram_service import telegram_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class BindingSuccessRequest(BaseModel):
    chat_id: int
    user_name: str

@router.post("/telegram/binding-success")
async def handle_binding_success(request: BindingSuccessRequest):
    """处理绑定成功通知"""
    try:
        success = await telegram_service.send_binding_success_message(
            request.chat_id, 
            request.user_name
        )
        
        if success:
            return {"status": "success", "message": "Binding success message sent"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send message")
            
    except Exception as e:
        logger.error(f"处理绑定成功通知失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/telegram/status")
async def get_telegram_status():
    """获取 Telegram bot 状态"""
    return {
        "status": "running" if telegram_service.bot_instance else "stopped",
        "bot_token_configured": bool(telegram_service.bot_token)
    }