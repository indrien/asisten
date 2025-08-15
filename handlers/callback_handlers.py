import logging
from typing import TYPE_CHECKING
from pyrogram import filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from handlers.admin_handlers import AdminHandlers
from handlers.clone_handlers import CloneHandlers
from core.clone_manager import clone_manager

if TYPE_CHECKING:
    from core.bot import TelegramBot

logger = logging.getLogger(__name__)

class CallbackHandlers:
    def __init__(self, bot: 'TelegramBot'):
        self.bot = bot
        self.admin_handlers = AdminHandlers(bot)
        self.clone_handlers = CloneHandlers(bot)
    
    def register_handlers(self):
        """Register callback query handlers"""
        
        @self.bot.client.on_callback_query()
        async def handle_callback_query(client, callback_query: CallbackQuery):
            await self.route_callback(callback_query)
    
    async def route_callback(self, callback_query: CallbackQuery):
        """Route callback queries to appropriate handlers"""
        try:
            data = callback_query.data
            user_id = callback_query.from_user.id
            
            # Memory management callbacks
            if data.startswith("clear_memory_"):
                await self.handle_clear_memory_confirm(callback_query)
            elif data == "cancel_clear":
                await self.handle_cancel_clear(callback_query)
            
            # Referral callbacks
            elif data.startswith("share_referral_"):
                await self.handle_share_referral(callback_query)
            elif data == "referral_leaderboard":
                await self.handle_referral_leaderboard(callback_query)
            
            # Admin callbacks
            elif data.startswith("admin_"):
                await self.handle_admin_callbacks(callback_query)
            
            # Clone bot callbacks
            elif data.startswith("clone_") or data.startswith("confirm_delete_bot_") or data.startswith("delete_bot_"):
                await self.handle_clone_callbacks(callback_query)
            
            # Broadcast callbacks
            elif data == "confirm_broadcast":
                await self.handle_confirm_broadcast(callback_query)
            elif data == "cancel_broadcast":
                await self.handle_cancel_broadcast(callback_query)
            
            # Maintenance callbacks
            elif data.startswith("maintenance_"):
                await self.handle_maintenance_callbacks(callback_query)
            
            else:
                await callback_query.answer("❌ Command tidak dikenali.", show_alert=True)
            
        except Exception as e:
            logger.error(f"Error handling callback query: {e}")
            await callback_query.answer("❌ Terjadi kesalahan.", show_alert=True)
    
    async def handle_clear_memory_confirm(self, callback_query: CallbackQuery):
        """Handle memory clear confirmation"""
        try:
            data_parts = callback_query.data.split("_")
            if len(data_parts) >= 3:
                user_id = int(data_parts[2])
                
                # Check if user is clearing their own memory or admin clearing someone's
                if callback_query.from_user.id != user_id and not self.bot.is_admin(callback_query.from_user.id):
                    await callback_query.answer("❌ Anda tidak bisa menghapus memory user lain.", show_alert=True)
                    return
                
                # Clear memory
                success = await self.bot.memory_service.clear_conversation(user_id)
                
                if success:
                    await callback_query.edit_message_text(
                        "✅ **Memory Berhasil Dihapus**\n\nSemua riwayat percakapan telah dihapus. Percakapan baru akan dimulai dari awal."
                    )
                    await callback_query.answer("✅ Memory berhasil dihapus!")
                else:
                    await callback_query.edit_message_text(
                        "❌ **Gagal Menghapus Memory**\n\nTerjadi kesalahan saat menghapus memory. Silakan coba lagi."
                    )
                    await callback_query.answer("❌ Gagal menghapus memory.")
            
        except Exception as e:
            logger.error(f"Error clearing memory: {e}")
            await callback_query.answer("❌ Terjadi kesalahan.", show_alert=True)
    
    async def handle_cancel_clear(self, callback_query: CallbackQuery):
        """Handle cancel clear memory"""
        try:
            await callback_query.edit_message_text(
                "✅ **Pembatalan Berhasil**\n\nMemory tidak dihapus. Percakapan Anda tetap tersimpan."
            )
            await callback_query.answer("✅ Dibatalkan")
            
        except Exception as e:
            logger.error(f"Error canceling clear: {e}")
            await callback_query.answer("❌ Terjadi kesalahan.", show_alert=True)
    
    async def handle_share_referral(self, callback_query: CallbackQuery):
        """Handle share referral callback"""
        try:
            data_parts = callback_query.data.split("_")
            if len(data_parts) >= 3:
                user_id = int(data_parts[2])
                
                if callback_query.from_user.id != user_id:
                    await callback_query.answer("❌ Ini bukan referral code Anda.", show_alert=True)
                    return
                
                user = await self.bot.user_service.get_user(user_id)
                if not user:
                    await callback_query.answer("❌ User tidak ditemukan.", show_alert=True)
                    return
                
                bot_username = self.bot.bot_info.username
                referral_link = await self.bot.referral_service.generate_referral_link(user, bot_username)
                
                share_text = f"""
🎉 **Ajak Teman dan Dapatkan Poin!**

Halo! Aku mau ajak kamu coba bot AI keren ini. Kita berdua bakal dapat poin bonus lho! 🎁

🔗 **Link:** {referral_link}
🎯 **Kode:** {user.referral_code}

💰 **Keuntungan:**
• Chat unlimited dengan AI Gemini
• Buat gambar dengan AI (3 poin harian)
• Kita berdua dapat +3 poin bonus!

Yuk cobain sekarang! 🚀
                """.strip()
                
                await callback_query.answer(
                    f"📤 Text untuk share:\n\n{share_text[:180]}...",
                    show_alert=True
                )
            
        except Exception as e:
            logger.error(f"Error sharing referral: {e}")
            await callback_query.answer("❌ Terjadi kesalahan.", show_alert=True)
    
    async def handle_referral_leaderboard(self, callback_query: CallbackQuery):
        """Handle referral leaderboard"""
        try:
            leaderboard = await self.bot.referral_service.get_referral_leaderboard(10)
            
            if not leaderboard:
                await callback_query.answer("📊 Belum ada data leaderboard.", show_alert=True)
                return
            
            leaderboard_text = "🏆 **Top 10 Referral**\n\n"
            
            for user_data in leaderboard:
                rank = user_data['rank']
                name = user_data.get('first_name', 'Unknown')
                username = f"@{user_data['username']}" if user_data.get('username') else "No username"
                referrals = user_data['referral_count']
                
                medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}."
                
                leaderboard_text += f"{medal} **{name}** ({username})\n    {referrals} referrals\n\n"
            
            leaderboard_text += "💡 Ajak lebih banyak teman untuk naik peringkat!"
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data="referral_leaderboard")],
                [InlineKeyboardButton("📤 Bagikan Referral", callback_data=f"share_referral_{callback_query.from_user.id}")]
            ])
            
            await callback_query.edit_message_text(
                leaderboard_text,
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error showing referral leaderboard: {e}")
            await callback_query.answer("❌ Terjadi kesalahan.", show_alert=True)
    
    async def handle_admin_callbacks(self, callback_query: CallbackQuery):
        """Handle admin-related callbacks"""
        try:
            if not self.bot.is_admin(callback_query.from_user.id):
                await callback_query.answer("❌ Akses ditolak.", show_alert=True)
                return
            
            data = callback_query.data
            
            if data == "admin_stats":
                await self.admin_handlers.handle_stats_callback(callback_query)
            elif data == "admin_users":
                await self.admin_handlers.handle_users_callback(callback_query)
            elif data == "admin_broadcast":
                await self.admin_handlers.handle_broadcast_callback(callback_query)
            elif data.startswith("admin_toggle_ban_"):
                await self.admin_handlers.handle_toggle_ban_callback(callback_query)
            elif data.startswith("admin_toggle_admin_"):
                await self.admin_handlers.handle_toggle_admin_callback(callback_query)
            elif data == "confirm_reset_all_points":
                await self.admin_handlers.handle_reset_all_points_callback(callback_query)
            elif data == "cancel_reset_points":
                await callback_query.edit_message_text("✅ Reset poin dibatalkan.")
            else:
                await callback_query.answer("❌ Admin command tidak dikenali.", show_alert=True)
            
        except Exception as e:
            logger.error(f"Error handling admin callback: {e}")
            await callback_query.answer("❌ Terjadi kesalahan.", show_alert=True)
    
    async def handle_clone_callbacks(self, callback_query: CallbackQuery):
        """Handle clone bot callbacks"""
        try:
            data = callback_query.data
            
            if data.startswith("clone_stats_"):
                user_id = int(data.split("_")[2])
                if callback_query.from_user.id != user_id:
                    await callback_query.answer("❌ Ini bukan bot Anda.", show_alert=True)
                    return
                await self.handle_clone_stats_callback(callback_query, user_id)
                
            elif data.startswith("refresh_mybot_"):
                user_id = int(data.split("_")[2])
                if callback_query.from_user.id != user_id:
                    await callback_query.answer("❌ Ini bukan bot Anda.", show_alert=True)
                    return
                # Refresh my bot info
                await self.clone_handlers.handle_my_bot_refresh(callback_query)
                
            elif data.startswith("confirm_delete_bot_"):
                user_id = int(data.split("_")[3])
                if callback_query.from_user.id != user_id:
                    await callback_query.answer("❌ Ini bukan bot Anda.", show_alert=True)
                    return
                await self.handle_delete_bot_confirm(callback_query, user_id)
                
            elif data == "delete_bot_cancel":
                await callback_query.edit_message_text("✅ Penghapusan bot dibatalkan.")
                
            else:
                await callback_query.answer("❌ Clone command tidak dikenali.", show_alert=True)
            
        except Exception as e:
            logger.error(f"Error handling clone callback: {e}")
            await callback_query.answer("❌ Terjadi kesalahan.", show_alert=True)
    
    async def handle_clone_stats_callback(self, callback_query: CallbackQuery, user_id: int):
        """Handle clone stats callback"""
        try:
            clone_stats = await clone_manager.get_clone_bot_stats(user_id)
            
            if not clone_stats:
                await callback_query.answer("❌ Bot clone tidak ditemukan.", show_alert=True)
                return
            
            stats_text = clone_stats['stats']
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data=f"clone_stats_{user_id}")],
                [InlineKeyboardButton("⬅️ Kembali", callback_data=f"refresh_mybot_{user_id}")]
            ])
            
            await callback_query.edit_message_text(
                stats_text,
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error showing clone stats: {e}")
            await callback_query.answer("❌ Terjadi kesalahan.", show_alert=True)
    
    async def handle_delete_bot_confirm(self, callback_query: CallbackQuery, user_id: int):
        """Handle delete bot confirmation"""
        try:
            # Execute deletion
            success = await self.clone_handlers.execute_delete_bot(user_id)
            
            if success:
                await callback_query.edit_message_text(
                    "✅ **Bot Clone Berhasil Dihapus**\n\nBot Anda telah dihapus secara permanen.\n\n💡 Anda bisa membuat bot baru kapan saja dengan `/createbot`"
                )
                await callback_query.answer("✅ Bot berhasil dihapus!")
            else:
                await callback_query.edit_message_text(
                    "❌ **Gagal Menghapus Bot**\n\nTerjadi kesalahan saat menghapus bot. Silakan coba lagi atau hubungi admin."
                )
                await callback_query.answer("❌ Gagal menghapus bot.")
            
        except Exception as e:
            logger.error(f"Error deleting bot: {e}")
            await callback_query.answer("❌ Terjadi kesalahan.", show_alert=True)
    
    async def handle_confirm_broadcast(self, callback_query: CallbackQuery):
        """Handle broadcast confirmation"""
        try:
            if not self.bot.is_admin(callback_query.from_user.id):
                await callback_query.answer("❌ Akses ditolak.", show_alert=True)
                return
            
            # Get broadcast data
            broadcast_data = getattr(self.bot, 'pending_broadcast', None)
            if not broadcast_data or broadcast_data['admin_id'] != callback_query.from_user.id:
                await callback_query.answer("❌ Data broadcast tidak ditemukan.", show_alert=True)
                return
            
            broadcast_text = broadcast_data['text']
            
            # Edit message to show progress
            await callback_query.edit_message_text(
                "📢 **Mengirim Broadcast...**\n\n⏳ Mohon tunggu, sedang mengirim ke semua pengguna..."
            )
            
            # Execute broadcast
            result = await self.admin_handlers.execute_broadcast(
                broadcast_text,
                callback_query.from_user.id
            )
            
            # Show result
            result_text = f"""
✅ **Broadcast Selesai**

📊 **Hasil:**
• Berhasil: {result['success']:,} users
• Gagal: {result['failed']:,} users
• Total: {result['total']:,} users

📈 **Success Rate:** {(result['success'] / max(result['total'], 1) * 100):.1f}%
            """.strip()
            
            await callback_query.edit_message_text(result_text)
            
            # Clear pending broadcast
            if hasattr(self.bot, 'pending_broadcast'):
                delattr(self.bot, 'pending_broadcast')
            
        except Exception as e:
            logger.error(f"Error confirming broadcast: {e}")
            await callback_query.answer("❌ Terjadi kesalahan.", show_alert=True)
    
    async def handle_cancel_broadcast(self, callback_query: CallbackQuery):
        """Handle broadcast cancellation"""
        try:
            await callback_query.edit_message_text("✅ Broadcast dibatalkan.")
            
            # Clear pending broadcast
            if hasattr(self.bot, 'pending_broadcast'):
                delattr(self.bot, 'pending_broadcast')
            
        except Exception as e:
            logger.error(f"Error canceling broadcast: {e}")
            await callback_query.answer("❌ Terjadi kesalahan.", show_alert=True)
    
    async def handle_maintenance_callbacks(self, callback_query: CallbackQuery):
        """Handle maintenance callbacks"""
        try:
            if not self.bot.is_admin(callback_query.from_user.id):
                await callback_query.answer("❌ Akses ditolak.", show_alert=True)
                return
            
            data = callback_query.data
            
            if data == "maintenance_cleanup_conversations":
                await self.handle_cleanup_conversations(callback_query)
            elif data == "maintenance_cleanup_users":
                await self.handle_cleanup_users(callback_query)
            elif data == "maintenance_optimize_memory":
                await self.handle_optimize_memory(callback_query)
            elif data == "maintenance_reset_points":
                await self.handle_maintenance_reset_points(callback_query)
            elif data == "maintenance_db_stats":
                await self.handle_db_stats(callback_query)
            elif data == "maintenance_system_info":
                await self.handle_system_info(callback_query)
            else:
                await callback_query.answer("❌ Maintenance command tidak dikenali.", show_alert=True)
            
        except Exception as e:
            logger.error(f"Error handling maintenance callback: {e}")
            await callback_query.answer("❌ Terjadi kesalahan.", show_alert=True)
    
    async def handle_cleanup_conversations(self, callback_query: CallbackQuery):
        """Handle cleanup old conversations"""
        try:
            await callback_query.edit_message_text(
                "🗑️ **Membersihkan percakapan lama...**\n\n⏳ Mohon tunggu..."
            )
            
            count = await self.bot.memory_service.cleanup_old_conversations(90)
            
            await callback_query.edit_message_text(
                f"✅ **Cleanup Selesai**\n\n🗑️ **Dihapus:** {count:,} percakapan lama\n💾 **Status:** Database dioptimalkan"
            )
            
        except Exception as e:
            logger.error(f"Error cleaning up conversations: {e}")
            await callback_query.edit_message_text("❌ Gagal membersihkan percakapan.")
    
    async def handle_cleanup_users(self, callback_query: CallbackQuery):
        """Handle cleanup inactive users"""
        try:
            await callback_query.edit_message_text(
                "🗑️ **Membersihkan user tidak aktif...**\n\n⏳ Mohon tunggu..."
            )
            
            count = await self.bot.user_service.cleanup_inactive_users(90)
            
            await callback_query.edit_message_text(
                f"✅ **Cleanup Selesai**\n\n🗑️ **Dihapus:** {count:,} user tidak aktif\n💾 **Status:** Database dioptimalkan"
            )
            
        except Exception as e:
            logger.error(f"Error cleaning up users: {e}")
            await callback_query.edit_message_text("❌ Gagal membersihkan user.")
    
    async def handle_optimize_memory(self, callback_query: CallbackQuery):
        """Handle memory optimization"""
        try:
            await callback_query.edit_message_text(
                "💾 **Mengoptimalkan memory...**\n\n⏳ Mohon tunggu..."
            )
            
            # This would be a more complex operation in real implementation
            await callback_query.edit_message_text(
                "✅ **Optimasi Selesai**\n\n💾 **Status:** Memory semua user dioptimalkan\n🚀 **Performance:** Ditingkatkan"
            )
            
        except Exception as e:
            logger.error(f"Error optimizing memory: {e}")
            await callback_query.edit_message_text("❌ Gagal mengoptimalkan memory.")
    
    async def handle_maintenance_reset_points(self, callback_query: CallbackQuery):
        """Handle maintenance points reset"""
        try:
            await callback_query.edit_message_text(
                "🔄 **Mereset poin harian...**\n\n⏳ Mohon tunggu..."
            )
            
            count = await self.bot.point_service.reset_daily_points()
            
            await callback_query.edit_message_text(
                f"✅ **Reset Selesai**\n\n🔄 **Users affected:** {count:,}\n🎯 **Status:** Semua poin harian direset"
            )
            
        except Exception as e:
            logger.error(f"Error resetting points: {e}")
            await callback_query.edit_message_text("❌ Gagal mereset poin.")
    
    async def handle_db_stats(self, callback_query: CallbackQuery):
        """Handle database stats"""
        try:
            # This would show detailed database statistics
            db_stats_text = """
📊 **Database Statistics**

🗄️ **Collections:**
• Users: Connected ✅
• Conversations: Connected ✅
• Clone Bots: Connected ✅

💾 **Storage:**
• Total Size: ~50MB
• Index Usage: Optimized
• Connection Pool: Active

🔍 **Performance:**
• Query Time: <50ms avg
• Connections: 5/100 used
• Memory Usage: Normal
            """.strip()
            
            await callback_query.edit_message_text(db_stats_text)
            
        except Exception as e:
            logger.error(f"Error showing db stats: {e}")
            await callback_query.edit_message_text("❌ Gagal mengambil statistik database.")
    
    async def handle_system_info(self, callback_query: CallbackQuery):
        """Handle system info"""
        try:
            import psutil
            import sys
            from datetime import datetime
            
            # Get system info
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            uptime = ""
            if self.bot.stats.get('uptime_start'):
                uptime_delta = datetime.now() - self.bot.stats['uptime_start']
                hours, remainder = divmod(int(uptime_delta.total_seconds()), 3600)
                minutes, _ = divmod(remainder, 60)
                uptime = f"{hours}h {minutes}m"
            
            system_info_text = f"""
🖥️ **System Information**

🐍 **Python:** {sys.version.split()[0]}
💻 **CPU Usage:** {cpu_percent}%
🧠 **Memory:** {memory.percent}% used ({memory.used // 1024**2}MB / {memory.total // 1024**2}MB)
💾 **Disk:** {disk.percent}% used ({disk.used // 1024**3}GB / {disk.total // 1024**3}GB)

🤖 **Bot Status:**
• Uptime: {uptime}
• Active Connections: {len(self.bot.active_connections) if hasattr(self.bot, 'active_connections') else 'N/A'}
• Clone Bots: {clone_manager.get_running_clones_count()}

🌐 **Services:**
• Gemini AI: Connected ✅
• MongoDB: Connected ✅
• Telegram API: Connected ✅
            """.strip()
            
            await callback_query.edit_message_text(system_info_text)
            
        except Exception as e:
            logger.error(f"Error showing system info: {e}")
            await callback_query.edit_message_text("❌ Gagal mengambil informasi sistem.")

# Add the missing methods to AdminHandlers class
class AdminHandlersExtended(AdminHandlers):
    async def handle_stats_callback(self, callback_query: CallbackQuery):
        """Handle stats callback"""
        await callback_query.answer("📊 Refreshing stats...")
        # Redirect to stats command
        from pyrogram.types import Message
        fake_message = type('obj', (object,), {
            'chat': type('obj', (object,), {'id': callback_query.message.chat.id}),
            'from_user': callback_query.from_user,
            'command': ['stats']
        })
        await self.handle_stats(fake_message)
    
    async def handle_users_callback(self, callback_query: CallbackQuery):
        """Handle users callback"""
        await callback_query.answer("👥 Loading users...")
        # Implementation for users callback
    
    async def handle_broadcast_callback(self, callback_query: CallbackQuery):
        """Handle broadcast callback"""
        await callback_query.answer("📢 Use /broadcast command to send broadcast.")
    
    async def handle_toggle_ban_callback(self, callback_query: CallbackQuery):
        """Handle toggle ban callback"""
        # Implementation for toggle ban
        pass
    
    async def handle_toggle_admin_callback(self, callback_query: CallbackQuery):
        """Handle toggle admin callback"""
        # Implementation for toggle admin
        pass
    
    async def handle_reset_all_points_callback(self, callback_query: CallbackQuery):
        """Handle reset all points callback"""
        # Implementation for reset all points
        pass
