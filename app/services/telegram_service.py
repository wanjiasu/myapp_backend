import logging
import os
import psycopg2
import psycopg2.extras
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import asyncio
from ..database import get_database
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

class TelegramService:
    def __init__(self):
        self.bot_token = os.getenv('BOT_TOKEN')
        self.site_url = os.getenv('SITE_URL', 'http://localhost:3000')
        self.bot_instance = None
        self.application = None
        self.database = get_database()
        
    async def initialize(self):
        """初始化 Telegram bot"""
        if not self.bot_token:
            logger.error("未找到 BOT_TOKEN 环境变量")
            return False
            
        self.bot_instance = Bot(token=self.bot_token)
        self.application = Application.builder().token(self.bot_token).build()
        
        # 添加处理器
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("broadcast", self.handle_broadcast_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        return True
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """处理/start命令，显示欢迎消息和绑定按钮"""
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        # 生成登录链接（带 Telegram 参数）
        login_url = f"{self.site_url}/login?tg_user_id={user.id}&tg_chat_id={chat_id}"
        
        # 欢迎消息
        message = (
            f"🎉 欢迎，{user.first_name}！\n\n"
            f"点击下方按钮绑定您的账户，享受完整服务体验！"
        )
        
        # 创建内联键盘按钮 - 只有一个绑定按钮
        keyboard = [
            [InlineKeyboardButton("🔗 立即绑定", url=login_url)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # 发送消息和按钮
        await update.message.reply_text(message, reply_markup=reply_markup)
        
        # 记录日志
        logger.info(f"用户 {user.id} 启动bot，绑定链接: {login_url}")

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """处理按钮点击回调（现在主要用于处理返回主菜单等操作）"""
        query = update.callback_query
        user = query.from_user
        
        # 确认回调查询
        await query.answer()
        
        if query.data == "back_to_main":
            # 返回主菜单
            chat_id = query.message.chat.id
            
            # 生成登录链接（带 Telegram 参数）
            login_url = f"{self.site_url}/login?tg_user_id={user.id}&tg_chat_id={chat_id}"
            
            message = (
                f"🎉 欢迎，{user.first_name}！\n\n"
                f"点击下方按钮绑定您的账户，享受完整服务体验！"
            )
            
            keyboard = [
                [InlineKeyboardButton("🔗 立即绑定", url=login_url)]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup)
            logger.info(f"用户 {user.id} 返回主菜单")

    async def send_binding_success_message(self, chat_id: int, user_name: str) -> bool:
        """发送绑定成功的祝贺消息"""
        try:
            message = (
                f"🎉 恭喜 {user_name}！\n\n"
                f"✅ 账户绑定成功！\n"
                f"🚀 现在您可以享受完整的服务体验了！\n\n"
                f"感谢您的使用！"
            )
            
            # 创建返回主菜单的按钮
            keyboard = [
                [InlineKeyboardButton("🏠 返回主菜单", callback_data="back_to_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.bot_instance.send_message(
                chat_id=chat_id, 
                text=message, 
                reply_markup=reply_markup
            )
            logger.info(f"已向用户 {chat_id} 发送绑定成功消息")
            return True
        except Exception as e:
            logger.error(f"发送绑定成功消息失败: {e}")
            return False

    async def handle_broadcast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """处理/broadcast命令"""
        # 获取命令后的参数作为广播内容
        broadcast_content = ' '.join(context.args) if context.args else ""
        
        if not broadcast_content:
            await update.message.reply_text("❌ 广播内容不能为空！\n使用方法：/broadcast 您要广播的内容")
            return
        
        # 执行广播
        success_count = await self.broadcast_to_all_users(broadcast_content)
        
        # 回复发送结果
        await update.message.reply_text(
            f"📢 广播消息已发送！\n"
            f"✅ 成功发送给 {success_count} 个用户"
        )

    async def get_all_chat_ids(self):
        """从用户数据库获取所有绑定的chat_id（临时连接FRONT_DATABASE_URL）"""
        connection = None
        try:
            # 临时连接到用户数据库
            front_db_url = os.getenv("FRONT_DATABASE_URL")
            if not front_db_url:
                logger.error("FRONT_DATABASE_URL 环境变量未设置")
                return []
            
            connection = psycopg2.connect(front_db_url)
            connection.autocommit = True
            
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("SELECT telegram_chat_id FROM telegram_binding")
                results = cursor.fetchall()
                return [row['telegram_chat_id'] for row in results]
                
        except Exception as e:
            logger.error(f"获取chat_id列表失败: {e}")
            return []
        finally:
            if connection and not connection.closed:
                connection.close()

    async def broadcast_to_all_users(self, message: str) -> int:
        """向所有用户广播消息"""
        chat_ids = await self.get_all_chat_ids()
        success_count = 0
        
        for chat_id in chat_ids:
            try:
                await self.bot_instance.send_message(
                    chat_id=int(chat_id),
                    text=f"📢 系统广播\n\n{message}"
                )
                success_count += 1
                logger.info(f"成功向用户 {chat_id} 发送广播消息")
                
                # 添加小延迟避免触发Telegram的速率限制
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"向用户 {chat_id} 发送广播消息失败: {e}")
                continue
        
        logger.info(f"广播完成，成功发送给 {success_count}/{len(chat_ids)} 个用户")
        return success_count

    async def start_polling(self):
        """启动 bot 轮询"""
        if self.application:
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()

    async def stop_polling(self):
        """停止 bot 轮询"""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()

# 全局 Telegram 服务实例
telegram_service = TelegramService()