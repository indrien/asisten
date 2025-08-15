import logging
from typing import TYPE_CHECKING
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from core.clone_manager import clone_manager
from config.settings import settings

if TYPE_CHECKING:
    from core.bot import TelegramBot

logger = logging.getLogger(__name__)

class CloneHandlers:
    def __init__(self, bot: 'TelegramBot'):
        self.bot = bot
    
    def register_handlers(self):
        """Register clone bot handlers"""
        
        @self.bot.client.on_message(filters.command("createbot"))
        async def createbot_command(client, message: Message):
            # Check if this is the parameter version
            if len(message.command) >= 3:
                await self.handle_create_bot_with_params(message)
            else:
                await self.handle_create_bot(message)
        
        @self.bot.client.on_message(filters.command("mybot"))
        async def mybot_command(client, message: Message):
            await self.handle_my_bot(message)
        
        @self.bot.client.on_message(filters.command("deletebot"))
        async def deletebot_command(client, message: Message):
            await self.handle_delete_bot(message)
        
        @self.bot.client.on_message(filters.command("clonestats"))
        async def clonestats_command(client, message: Message):
            await self.handle_clone_stats(message)
        
        @self.bot.client.on_message(filters.command("bothelp"))
        async def bothelp_command(client, message: Message):
            await self.handle_bot_help(message)
    
    async def handle_create_bot(self, message: Message):
        """Handle /createbot command"""
        try:
            user_id = message.from_user.id
            
            # Check if user already has a clone bot
            user = await self.bot.user_service.get_or_create_user(
                user_id=user_id,
                first_name=message.from_user.first_name,
                username=message.from_user.username
            )
            
            if user.has_clone_bot:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ **Anda sudah memiliki bot clone!**\n\nSetiap user hanya boleh membuat 1 bot clone.\n\nGunakan `/mybot` untuk melihat bot Anda atau `/deletebot` untuk menghapusnya."
                )
                return
            
            # Show create bot tutorial
            tutorial_text = f"""
🤖 **Membuat Bot Clone - Tutorial**

🎯 **Yang Anda Butuhkan:**
1. **Bot Token** - Dapatkan dari @BotFather
2. **Admin ID** - ID Telegram Anda sebagai admin

📋 **Langkah-langkah:**

**1. Buat Bot di BotFather:**
• Chat @BotFather di Telegram
• Ketik `/newbot`
• Pilih nama dan username bot
• Copy **Bot Token** yang diberikan

**2. Dapatkan Admin ID:**
• Chat @userinfobot atau @myidbot
• Copy **User ID** Anda

**3. Buat Clone Bot:**
• Gunakan command: `/createbot <bot_token> <admin_id>`

**Contoh:**
`/createbot 1234567890:ABC-DEF1234567890 987654321`

⚠️ **Penting:**
• Bot token harus valid dan belum digunakan
• Admin ID harus berupa angka
• Setiap user hanya boleh 1 bot clone
• Bot akan otomatis aktif setelah dibuat

🎁 **Keuntungan Bot Clone:**
• Fitur sama seperti bot official
• Memory terpisah per bot
• Sistem poin independen
• Admin penuh kontrol

❓ **Butuh bantuan?** Gunakan `/bothelp`
            """.strip()
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📖 Tutorial Video", url="https://t.me/your_channel")],
                [InlineKeyboardButton("🤖 Chat BotFather", url="https://t.me/BotFather")],
                [InlineKeyboardButton("🆔 Get Your ID", url="https://t.me/userinfobot")]
            ])
            
            await self.bot.client.send_message(
                message.chat.id,
                tutorial_text,
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
            
        except Exception as e:
            logger.error(f"Error in create bot command: {e}")
            await self.bot.send_message_safe(
                message.chat.id,
                "Terjadi kesalahan saat menampilkan tutorial."
            )
    
    async def handle_create_bot_with_params(self, message: Message):
        """Handle create bot with parameters"""
        try:
            if len(message.command) < 3:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ **Format Salah**\n\nGunakan: `/createbot <bot_token> <admin_id>`\n\nContoh:\n`/createbot 1234567890:ABC-DEF 987654321`"
                )
                return
            
            bot_token = message.command[1]
            
            try:
                admin_id = int(message.command[2])
            except ValueError:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ Admin ID harus berupa angka."
                )
                return
            
            user_id = message.from_user.id
            
            # Validate bot token format
            if ':' not in bot_token or len(bot_token.split(':')[0]) < 8:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ **Format Bot Token Salah**\n\nBot token harus dalam format:\n`1234567890:ABC-DEF1234567890`\n\nDapatkan dari @BotFather"
                )
                return
            
            # Check if user already has a clone bot
            user = await self.bot.user_service.get_or_create_user(
                user_id=user_id,
                first_name=message.from_user.first_name,
                username=message.from_user.username
            )
            
            if user.has_clone_bot:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ Anda sudah memiliki bot clone!"
                )
                return
            
            # Send creating message
            creating_msg = await self.bot.client.send_message(
                message.chat.id,
                "🤖 **Sedang membuat bot clone...**\n\n⏳ Mohon tunggu sebentar..."
            )
            
            try:
                # Create clone bot
                clone_bot = await clone_manager.create_clone_bot(
                    bot_token=bot_token,
                    creator_id=user_id,
                    admin_id=admin_id
                )
                
                # Start the clone bot
                success = await clone_manager.start_clone_bot(bot_token)
                
                if success:
                    success_text = f"""
✅ **Bot Clone Berhasil Dibuat!**

🤖 **Informasi Bot:**
• Username: @{clone_bot.bot_username}
• Nama: {clone_bot.bot_name}
• Admin: Anda (`{admin_id}`)

🎯 **Status:** Aktif dan siap digunakan!

📋 **Fitur Bot Clone:**
• Semua fitur seperti bot official
• Memory percakapan terpisah
• Sistem poin independen
• Kontrol admin penuh

⚙️ **Manajemen:**
• `/mybot` - Info dan statistik bot
• `/deletebot` - Hapus bot (permanent)

🎉 **Selamat! Bot Anda sudah online.**
Coba chat langsung ke @{clone_bot.bot_username}
                    """.strip()
                    
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton(f"💬 Chat Bot", url=f"https://t.me/{clone_bot.bot_username}")],
                        [InlineKeyboardButton("📊 Statistik", callback_data=f"clone_stats_{user_id}")]
                    ])
                    
                    await self.bot.client.edit_message_text(
                        message.chat.id,
                        creating_msg.id,
                        success_text,
                        reply_markup=keyboard
                    )
                    
                else:
                    await self.bot.client.edit_message_text(
                        message.chat.id,
                        creating_msg.id,
                        "❌ **Bot berhasil dibuat tetapi gagal dijalankan.**\n\nBot mungkin sedang dalam maintenance. Coba lagi nanti."
                    )
                
            except ValueError as ve:
                await self.bot.client.edit_message_text(
                    message.chat.id,
                    creating_msg.id,
                    f"❌ **Gagal membuat bot:**\n\n{str(ve)}\n\n💡 **Tips:**\n• Pastikan bot token valid\n• Bot belum pernah digunakan\n• Anda belum punya bot clone"
                )
                
            except Exception as e:
                logger.error(f"Error creating clone bot: {e}")
                await self.bot.client.edit_message_text(
                    message.chat.id,
                    creating_msg.id,
                    "❌ **Terjadi kesalahan saat membuat bot.**\n\nSilakan coba lagi atau hubungi admin jika masalah berlanjut."
                )
            
        except Exception as e:
            logger.error(f"Error in create bot with params: {e}")
            await self.bot.send_message_safe(
                message.chat.id,
                "Terjadi kesalahan saat memproses permintaan."
            )
    
    async def handle_my_bot(self, message: Message):
        """Handle /mybot command"""
        try:
            user_id = message.from_user.id
            
            # Get user's clone bot info
            clone_stats = await clone_manager.get_clone_bot_stats(user_id)
            
            if not clone_stats:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ **Anda belum memiliki bot clone.**\n\nGunakan `/createbot` untuk membuat bot clone Anda sendiri!"
                )
                return
            
            clone_bot = clone_stats['clone_bot']
            is_running = clone_stats['is_running']
            
            status_emoji = "🟢" if is_running else "🔴"
            status_text = "Online" if is_running else "Offline"
            
            my_bot_text = f"""
🤖 **Bot Clone Anda**

📱 **Informasi:**
• Username: @{clone_bot.bot_username}
• Nama: {clone_bot.bot_name}
• Status: {status_emoji} {status_text}

📊 **Statistik:**
• Total Users: {clone_bot.total_users:,}
• Total Messages: {clone_bot.total_messages:,}
• Total Images: {clone_bot.total_images:,}

📅 **Tanggal:**
• Dibuat: {clone_bot.created_at.strftime('%d/%m/%Y %H:%M')}
• Aktivitas Terakhir: {clone_bot.last_activity.strftime('%d/%m/%Y %H:%M')}

⚙️ **Admin ID:** `{clone_bot.admin_id}`
🆔 **Bot ID:** `{clone_bot.bot_username}`

💡 **Tips:** 
• Bot akan otomatis restart jika ada masalah
• Bagikan @{clone_bot.bot_username} ke teman-teman
• Gunakan fitur referral untuk mendapat lebih banyak user
            """.strip()
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(f"💬 Chat Bot", url=f"https://t.me/{clone_bot.bot_username}"),
                    InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_mybot_{user_id}")
                ],
                [
                    InlineKeyboardButton("📊 Detail Stats", callback_data=f"detail_clone_stats_{user_id}"),
                    InlineKeyboardButton("⚙️ Settings", callback_data=f"clone_settings_{user_id}")
                ],
                [
                    InlineKeyboardButton("🗑️ Delete Bot", callback_data=f"confirm_delete_bot_{user_id}")
                ]
            ])
            
            await self.bot.client.send_message(
                message.chat.id,
                my_bot_text,
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error in my bot command: {e}")
            await self.bot.send_message_safe(
                message.chat.id,
                "Terjadi kesalahan saat mengambil informasi bot."
            )
    
    async def handle_delete_bot(self, message: Message):
        """Handle /deletebot command"""
        try:
            user_id = message.from_user.id
            
            # Check if user has a clone bot
            clone_stats = await clone_manager.get_clone_bot_stats(user_id)
            
            if not clone_stats:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ **Anda tidak memiliki bot clone.**\n\nTidak ada yang bisa dihapus."
                )
                return
            
            clone_bot = clone_stats['clone_bot']
            
            # Confirmation
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Ya, Hapus Permanent", callback_data=f"delete_bot_confirm_{user_id}"),
                    InlineKeyboardButton("❌ Batal", callback_data="delete_bot_cancel")
                ]
            ])
            
            warning_text = f"""
⚠️ **Konfirmasi Hapus Bot Clone**

🤖 **Bot yang akan dihapus:**
• Username: @{clone_bot.bot_username}
• Nama: {clone_bot.bot_name}
• Total Users: {clone_bot.total_users:,}
• Total Messages: {clone_bot.total_messages:,}

🚨 **PERINGATAN:**
• Tindakan ini **TIDAK DAPAT DIBATALKAN**
• Semua data dan statistik akan hilang
• User bot akan kehilangan akses
• Anda bisa membuat bot baru setelah ini

❓ **Yakin ingin menghapus bot ini?**
            """.strip()
            
            await self.bot.client.send_message(
                message.chat.id,
                warning_text,
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error in delete bot command: {e}")
            await self.bot.send_message_safe(
                message.chat.id,
                "Terjadi kesalahan saat memproses permintaan hapus bot."
            )
    
    async def handle_clone_stats(self, message: Message):
        """Handle /clonestats command (owner only)"""
        try:
            if not self.bot.is_owner(message.from_user.id):
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ Command ini hanya untuk owner bot."
                )
                return
            
            # Get global clone statistics
            clone_stats = await clone_manager.get_all_clone_stats()
            
            if not clone_stats:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ Gagal mengambil statistik clone bot."
                )
                return
            
            clone_stats_text = f"""
🤖 **Statistik Global Clone Bot**

📊 **Overview:**
• Total Clone Bots: {clone_stats.get('total_clones', 0):,}
• Active Clones: {clone_stats.get('active_clones', 0):,}
• Running Clones: {clone_stats.get('running_clones', 0):,}

💡 **Status:**
• Success Rate: {(clone_stats.get('running_clones', 0) / max(clone_stats.get('active_clones', 1), 1) * 100):.1f}%
• Total Capacity: {clone_stats.get('total_clones', 0) * 1000:,} users (estimated)

⚙️ **System:**
• Clone Manager: Active
• Auto Restart: Enabled
• Health Monitoring: Active

📈 **Growth:**
• New clones created daily (avg): Coming soon
• Most active clone: Coming soon
• Total clone users: Coming soon
            """.strip()
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 Restart All", callback_data="owner_restart_all_clones"),
                    InlineKeyboardButton("⏹️ Stop All", callback_data="owner_stop_all_clones")
                ],
                [
                    InlineKeyboardButton("📊 Detailed Stats", callback_data="owner_detailed_clone_stats"),
                    InlineKeyboardButton("🔧 Maintenance", callback_data="owner_clone_maintenance")
                ]
            ])
            
            await self.bot.client.send_message(
                message.chat.id,
                clone_stats_text,
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error in clone stats command: {e}")
            await self.bot.send_message_safe(
                message.chat.id,
                "Terjadi kesalahan saat mengambil statistik."
            )
    
    async def handle_bot_help(self, message: Message):
        """Handle /bothelp command"""
        try:
            help_text = f"""
🤖 **Bantuan Clone Bot**

❓ **Apa itu Clone Bot?**
Clone bot adalah salinan dari bot official ini yang bisa Anda miliki sendiri dengan bot token Anda sendiri.

🎯 **Keuntungan:**
• Fitur lengkap sama seperti bot official
• Memory percakapan terpisah
• Sistem poin independen  
• Anda jadi admin penuh
• Gratis selamanya!

📋 **Cara Membuat:**

**1. Buat Bot di BotFather:**
• Chat @BotFather
• Ketik `/newbot`
• Ikuti instruksi
• Copy bot token

**2. Dapatkan User ID:**
• Chat @userinfobot
• Copy User ID Anda

**3. Buat Clone:**
• Gunakan `/createbot <token> <admin_id>`

📖 **Commands:**
• `/createbot` - Tutorial membuat bot
• `/mybot` - Info bot Anda
• `/deletebot` - Hapus bot

❓ **FAQ:**

**Q: Apakah gratis?**
A: Ya, sepenuhnya gratis!

**Q: Berapa bot yang bisa dibuat?**
A: Maksimal 1 bot per user.

**Q: Apakah data aman?**
A: Ya, setiap clone bot memiliki database terpisah.

**Q: Bot mati bagaimana?**
A: Bot akan auto-restart otomatis.

**Q: Bisa custom fitur?**
A: Saat ini belum, tapi akan dikembangkan.

💡 **Tips Sukses:**
• Bagikan bot ke grup/channel Anda
• Gunakan fitur referral untuk grow
• Aktif promosi bot Anda
• Join komunitas bot creator

🆘 **Butuh bantuan?**
Hubungi owner: {settings.OWNER_ID}
            """.strip()
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🤖 BotFather", url="https://t.me/BotFather"),
                    InlineKeyboardButton("🆔 Get ID", url="https://t.me/userinfobot")
                ],
                [
                    InlineKeyboardButton("📖 Tutorial", callback_data="bot_tutorial"),
                    InlineKeyboardButton("💬 Support", url=f"tg://user?id={settings.OWNER_ID}")
                ]
            ])
            
            await self.bot.client.send_message(
                message.chat.id,
                help_text,
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error in bot help command: {e}")
            await self.bot.send_message_safe(
                message.chat.id,
                "Terjadi kesalahan saat menampilkan bantuan."
            )
    
    async def execute_delete_bot(self, user_id: int) -> bool:
        """Execute bot deletion"""
        try:
            success = await clone_manager.delete_clone_bot(user_id)
            
            if success:
                logger.info(f"Clone bot deleted for user {user_id}")
                return True
            else:
                logger.error(f"Failed to delete clone bot for user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing bot deletion for user {user_id}: {e}")
            return False
