import asyncio
import logging
from typing import Dict, Any, Optional
from bale import Bot, Message, InlineKeyboardMarkup, InlineKeyboardButton
from bale.handlers import MessageHandler, CallbackQueryHandler
from bale.filters import Filters
from database import DatabaseManager
from config import Config
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ManagerEvaluationBot:
    def __init__(self):
        self.bot = Bot(Config.BOT_TOKEN)
        self.db = DatabaseManager()
        self.user_states: Dict[int, Dict[str, Any]] = {}
        
        # Hotels data for each city
        self.hotels = {
            'karbala': [
                {'id': 1, 'name': 'هتل زینبیه'},
                {'id': 2, 'name': 'هتل قدس'},
                {'id': 3, 'name': 'هتل امام حسین'},
                {'id': 4, 'name': 'هتل رضوان'},
                {'id': 5, 'name': 'هتل فردوس'}
            ],
            'najaf': [
                {'id': 6, 'name': 'هتل علی'},
                {'id': 7, 'name': 'هتل امام علی'},
                {'id': 8, 'name': 'هتل غدیر'},
                {'id': 9, 'name': 'هتل میثم'},
                {'id': 10, 'name': 'هتل سلام'}
            ]
        }
        
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup message and callback handlers"""
        # Start command handler
        self.bot.add_handler(MessageHandler(self.start_command, Filters.command("start")))
        
        # National ID handler
        self.bot.add_handler(MessageHandler(self.handle_national_id, Filters.text & ~Filters.command))
        
        # Callback query handlers
        self.bot.add_handler(CallbackQueryHandler(self.handle_city_selection, pattern=r"^city_"))
        self.bot.add_handler(CallbackQueryHandler(self.handle_hotel_confirmation, pattern=r"^hotel_confirm_"))
        self.bot.add_handler(CallbackQueryHandler(self.handle_hotel_selection, pattern=r"^hotel_"))
        self.bot.add_handler(CallbackQueryHandler(self.show_hotel_list, pattern=r"^show_hotels_"))
    
    async def start_command(self, message: Message):
        """Handle /start command"""
        user_id = message.from_user.id
        
        # Initialize user state
        self.user_states[user_id] = {
            'step': 'waiting_national_id',
            'national_id': None,
            'city': None,
            'hotel': None
        }
        
        welcome_text = """
🌟 خوش آمدید 🌟

هدف این بات ارزشیابی مدیران ثابت است.

لطفاً کد ملی خود را وارد کنید:
        """
        
        await message.reply(welcome_text)
    
    async def handle_national_id(self, message: Message):
        """Handle national ID input"""
        user_id = message.from_user.id
        
        # Check if user is in correct state
        if user_id not in self.user_states or self.user_states[user_id]['step'] != 'waiting_national_id':
            await message.reply("لطفاً ابتدا /start را بزنید.")
            return
        
        national_id = message.text.strip()
        
        # Validate national ID format (10 digits)
        if not self.is_valid_national_id(national_id):
            await message.reply("❌ کد ملی وارد شده صحیح نمی‌باشد. لطفاً یک کد ملی 10 رقمی معتبر وارد کنید:")
            return
        
        # Check national ID in database
        user_info = await self.db.verify_national_id(national_id)
        
        if not user_info:
            await message.reply("❌ کد ملی شما در سیستم موجود نیست یا مجاز به شرکت در ارزشیابی نمی‌باشید.")
            return
        
        # Update user state
        self.user_states[user_id]['national_id'] = national_id
        self.user_states[user_id]['step'] = 'choosing_city'
        self.user_states[user_id]['user_info'] = user_info
        
        # Show city selection
        await self.show_city_selection(message)
    
    async def show_city_selection(self, message: Message):
        """Show city selection buttons"""
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("کربلا", callback_data="city_karbala")],
            [InlineKeyboardButton("نجف", callback_data="city_najaf")]
        ])
        
        text = "✅ احراز هویت با موفقیت انجام شد.\n\nلطفاً شهری را که می‌خواهید ارزشیابی مدیر ثابت آن را انجام دهید، انتخاب کنید:"
        
        await message.reply(text, reply_markup=keyboard)
    
    async def handle_city_selection(self, callback_query):
        """Handle city selection"""
        user_id = callback_query.from_user.id
        city = callback_query.data.replace("city_", "")
        
        if user_id not in self.user_states:
            await callback_query.answer("لطفاً ابتدا /start را بزنید.")
            return
        
        # Update user state
        self.user_states[user_id]['city'] = city
        self.user_states[user_id]['step'] = 'confirming_hotel'
        
        # Get suggested hotel for user
        suggested_hotel = await self.db.get_suggested_hotel(
            self.user_states[user_id]['national_id'], 
            city
        )
        
        if suggested_hotel:
            await self.show_hotel_confirmation(callback_query, suggested_hotel, city)
        else:
            # If no suggested hotel, show hotel list directly
            await self.show_hotel_list_callback(callback_query)
        
        await callback_query.answer()
    
    async def show_hotel_confirmation(self, callback_query, suggested_hotel: str, city: str):
        """Show hotel confirmation"""
        city_name = "کربلا" if city == "karbala" else "نجف"
        
        text = f"""
📍 شهر انتخابی: {city_name}

🏨 طبق اطلاعات سامانه، شما باید در هتل {suggested_hotel} اقامت داشته باشید.

آیا این اطلاعات صحیح است؟
        """
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ بله، صحیح است", callback_data=f"hotel_confirm_yes_{city}")],
            [InlineKeyboardButton("❌ خیر، هتل دیگری", callback_data=f"show_hotels_{city}")]
        ])
        
        await callback_query.message.edit_text(text, reply_markup=keyboard)
    
    async def handle_hotel_confirmation(self, callback_query):
        """Handle hotel confirmation"""
        user_id = callback_query.from_user.id
        data = callback_query.data
        
        if "hotel_confirm_yes" in data:
            city = data.split("_")[-1]
            suggested_hotel = await self.db.get_suggested_hotel(
                self.user_states[user_id]['national_id'], 
                city
            )
            
            self.user_states[user_id]['hotel'] = suggested_hotel
            self.user_states[user_id]['step'] = 'ready_for_evaluation'
            
            await callback_query.message.edit_text(
                f"✅ اطلاعات تایید شد.\n\n🏨 هتل: {suggested_hotel}\n📍 شهر: {'کربلا' if city == 'karbala' else 'نجف'}\n\n🔄 آماده برای ارزشیابی..."
            )
        
        await callback_query.answer()
    
    async def show_hotel_list(self, callback_query):
        """Show hotel list for manual selection"""
        city = callback_query.data.replace("show_hotels_", "")
        await self.show_hotel_list_callback(callback_query, city)
    
    async def show_hotel_list_callback(self, callback_query, city: str = None):
        """Show hotel list with buttons"""
        if not city:
            city = callback_query.data.replace("show_hotels_", "")
        
        city_name = "کربلا" if city == "karbala" else "نجف"
        hotels = self.hotels[city]
        
        text = f"🏨 لیست هتل‌های {city_name}:\n\nلطفاً هتلی که در آن اقامت دارید را انتخاب کنید:"
        
        keyboard = []
        for hotel in hotels:
            keyboard.append([InlineKeyboardButton(hotel['name'], callback_data=f"hotel_{hotel['id']}_{city}")])
        
        keyboard_markup = InlineKeyboardMarkup(keyboard)
        await callback_query.message.edit_text(text, reply_markup=keyboard_markup)
    
    async def handle_hotel_selection(self, callback_query):
        """Handle manual hotel selection"""
        user_id = callback_query.from_user.id
        data = callback_query.data
        
        # Parse callback data: hotel_id_city
        parts = data.split("_")
        hotel_id = int(parts[1])
        city = parts[2]
        
        # Find hotel name
        hotel_name = None
        for hotel in self.hotels[city]:
            if hotel['id'] == hotel_id:
                hotel_name = hotel['name']
                break
        
        if hotel_name:
            self.user_states[user_id]['hotel'] = hotel_name
            self.user_states[user_id]['step'] = 'ready_for_evaluation'
            
            city_name = "کربلا" if city == "karbala" else "نجف"
            await callback_query.message.edit_text(
                f"✅ انتخاب شما ثبت شد.\n\n🏨 هتل: {hotel_name}\n📍 شهر: {city_name}\n\n🔄 آماده برای ارزشیابی..."
            )
        
        await callback_query.answer()
    
    def is_valid_national_id(self, national_id: str) -> bool:
        """Validate Iranian national ID"""
        if not national_id or len(national_id) != 10:
            return False
        
        if not national_id.isdigit():
            return False
        
        # Check for repeated digits
        if len(set(national_id)) == 1:
            return False
        
        # Iranian national ID checksum validation
        total = sum(int(national_id[i]) * (10 - i) for i in range(9))
        remainder = total % 11
        
        if remainder < 2:
            return remainder == int(national_id[9])
        else:
            return (11 - remainder) == int(national_id[9])
    
    async def start_polling(self):
        """Start the bot"""
        logger.info("Starting bot...")
        await self.bot.run()

# Main execution
if __name__ == "__main__":
    bot = ManagerEvaluationBot()
    asyncio.run(bot.start_polling())
