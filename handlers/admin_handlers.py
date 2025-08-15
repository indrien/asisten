import logging
import asyncio
from typing import TYPE_CHECKING, List
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config.settings import settings

if TYPE_CHECKING:
    from core.bot import TelegramBot

logger = logging.getLogger(__name__)

class AdminHandlers:
    def __init__(self, bot: 'TelegramBot'):
        self.bot = bot
    
    def register_handlers(self):
        """Register all admin handlers"""
        
        @self.bot.client.on_message(filters.command("admin"))
        async def admin_command(client, message: Message):
            await self.handle_admin_panel(message)
        
        @self.bot.client.on_message(filters.command("ban"))
        async def ban_command(client, message: Message):
            await self.handle_ban_user(message)
        
        @self.bot.client.on_message(filters.command("unban"))
        async def unban_command(client, message: Message):
            await self.handle_unban_user(message)
        
        @self.bot.client.on_message(filters.command("stats"))
        async def stats_command(client, message: Message):
            await self.handle_stats(message)
        
        @self.bot.client.on_message(filters.command("broadcast"))
        async def broadcast_command(client, message: Message):
            await self.handle_broadcast(message)
        
        @self.bot.client.on_message(filters.command("users"))
        async def users_command(client, message: Message):
            await self.handle_users_list(message)
        
        @self.bot.client.on_message(filters.command("addadmin"))
        async def addadmin_command(client, message: Message):
            await self.handle_add_admin(message)
        
        @self.bot.client.on_message(filters.command("removeadmin"))
        async def removeadmin_command(client, message: Message):
            await self.handle_remove_admin(message)
        
        @self.bot.client.on_message(filters.command("userinfo"))
        async def userinfo_command(client, message: Message):
            await self.handle_user_info(message)
        
        @self.bot.client.on_message(filters.command("givepoints"))
        async def givepoints_command(client, message: Message):
            await self.handle_give_points(message)
        
        @self.bot.client.on_message(filters.command("resetpoints"))
        async def resetpoints_command(client, message: Message):
            await self.handle_reset_points(message)
        
        @self.bot.client.on_message(filters.command("maintenance"))
        async def maintenance_command(client, message: Message):
            await self.handle_maintenance(message)
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return self.bot.is_admin(user_id) or self.bot.is_owner(user_id)
    
    async def handle_admin_panel(self, message: Message):
        """Handle /admin command"""
        try:
            if not self.is_admin(message.from_user.id):
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ Anda tidak memiliki akses admin."
                )
                return
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
                    InlineKeyboardButton("👥 Users", callback_data="admin_users")
                ],
                [
                    InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
                    InlineKeyboardButton("🔧 Maintenance", callback_data="admin_maintenance")
                ],
                [
                    InlineKeyboardButton("🚫 Ban User", callback_data="admin_ban"),
                    InlineKeyboardButton("✅ Unban User", callback_data="admin_unban")
                ],
                [
                    InlineKeyboardButton("🎯 Give Points", callback_data="admin_give_points"),
                    InlineKeyboardButton("🔄 Reset Points", callback_data="admin_reset_points")
                ]
            ])
            
            admin_text = f"""
👑 **Panel Admin - {self.bot.bot_info.first_name}**

🔐 **Akses Admin Tersedia:**
• Statistik bot dan pengguna
• Manajemen pengguna (ban/unban)
• Broadcast pesan ke semua user
• Berikan/reset poin pengguna
• Maintenance dan optimasi

⚡ **Quick Commands:**
• `/stats` - Statistik lengkap
• `/ban <user_id>` - Ban pengguna
• `/unban <user_id>` - Unban pengguna
• `/broadcast <pesan>` - Broadcast
• `/userinfo <user_id>` - Info pengguna

📋 **Status:** {"Owner" if self.bot.is_owner(message.from_user.id) else "Admin"}
            """.strip()
            
            await self.bot.client.send_message(
                message.chat.id,
                admin_text,
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error in admin panel: {e}")
            await self.bot.send_message_safe(
                message.chat.id,
                "Terjadi kesalahan saat menampilkan panel admin."
            )
    
    async def handle_ban_user(self, message: Message):
        """Handle /ban command"""
        try:
            if not self.is_admin(message.from_user.id):
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ Anda tidak memiliki akses admin."
                )
                return
            
            if len(message.command) < 2:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ **Format Salah**\n\nGunakan: `/ban <user_id> [alasan]`\n\nContoh:\n`/ban 123456789 Spam`"
                )
                return
            
            try:
                user_id = int(message.command[1])
            except ValueError:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ User ID harus berupa angka."
                )
                return
            
            # Check if trying to ban owner
            if self.bot.is_owner(user_id):
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ Tidak dapat memban owner bot."
                )
                return
            
            reason = " ".join(message.command[2:]) if len(message.command) > 2 else "Tidak ada alasan"
            
            # Ban the user
            success = await self.bot.user_service.ban_user(user_id)
            
            if success:
                # Get user info
                user = await self.bot.user_service.get_user(user_id)
                user_name = user.first_name if user else "Unknown"
                
                ban_text = f"""
✅ **Pengguna Telah Dibanned**

👤 **User:** {user_name} (`{user_id}`)
📝 **Alasan:** {reason}
👮 **Admin:** {message.from_user.first_name}

⚠️ User tidak akan bisa menggunakan bot lagi.
                """.strip()
                
                await self.bot.send_message_safe(message.chat.id, ban_text)
                
                # Try to notify the banned user
                try:
                    await self.bot.client.send_message(
                        user_id,
                        f"🚫 **Anda telah dibanned dari bot ini**\n\n📝 **Alasan:** {reason}\n\nJika merasa ini kesalahan, hubungi admin."
                    )
                except:
                    pass  # User might have blocked bot
                    
            else:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ Gagal memban pengguna. User mungkin tidak ditemukan."
                )
            
        except Exception as e:
            logger.error(f"Error in ban command: {e}")
            await self.bot.send_message_safe(
                message.chat.id,
                "Terjadi kesalahan saat memban pengguna."
            )
    
    async def handle_unban_user(self, message: Message):
        """Handle /unban command"""
        try:
            if not self.is_admin(message.from_user.id):
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ Anda tidak memiliki akses admin."
                )
                return
            
            if len(message.command) < 2:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ **Format Salah**\n\nGunakan: `/unban <user_id>`\n\nContoh:\n`/unban 123456789`"
                )
                return
            
            try:
                user_id = int(message.command[1])
            except ValueError:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ User ID harus berupa angka."
                )
                return
            
            # Unban the user
            success = await self.bot.user_service.unban_user(user_id)
            
            if success:
                # Get user info
                user = await self.bot.user_service.get_user(user_id)
                user_name = user.first_name if user else "Unknown"
                
                unban_text = f"""
✅ **Pengguna Telah Diunban**

👤 **User:** {user_name} (`{user_id}`)
👮 **Admin:** {message.from_user.first_name}

✅ User sekarang bisa menggunakan bot lagi.
                """.strip()
                
                await self.bot.send_message_safe(message.chat.id, unban_text)
                
                # Try to notify the unbanned user
                try:
                    await self.bot.client.send_message(
                        user_id,
                        "✅ **Anda telah diunban**\n\nSekarang Anda bisa menggunakan bot lagi. Pastikan mengikuti aturan yang berlaku."
                    )
                except:
                    pass  # User might have blocked bot
                    
            else:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ Gagal mengunban pengguna. User mungkin tidak ditemukan."
                )
            
        except Exception as e:
            logger.error(f"Error in unban command: {e}")
            await self.bot.send_message_safe(
                message.chat.id,
                "Terjadi kesalahan saat mengunban pengguna."
            )
    
    async def handle_stats(self, message: Message):
        """Handle /stats command"""
        try:
            if not self.is_admin(message.from_user.id):
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ Anda tidak memiliki akses admin."
                )
                return
            
            # Send loading message
            loading_msg = await self.bot.client.send_message(
                message.chat.id,
                "📊 **Mengumpulkan statistik...**\n\n⏳ Mohon tunggu sebentar..."
            )
            
            try:
                # Get various statistics
                user_stats = await self.bot.user_service.get_user_stats()
                memory_stats = await self.bot.memory_service.get_global_memory_stats()
                points_stats = await self.bot.point_service.get_points_statistics()
                referral_stats = await self.bot.referral_service.get_referral_statistics()
                
                # Bot uptime
                uptime_text = "Unknown"
                if self.bot.stats.get('uptime_start'):
                    from datetime import datetime
                    uptime_delta = datetime.now() - self.bot.stats['uptime_start']
                    hours, remainder = divmod(int(uptime_delta.total_seconds()), 3600)
                    minutes, _ = divmod(remainder, 60)
                    uptime_text = f"{hours}h {minutes}m"
                
                stats_text = f"""
📊 **Statistik Bot - {self.bot.bot_info.first_name}**

👥 **Pengguna:**
• Total Users: {user_stats.get('total_users', 0):,}
• Active (24h): {user_stats.get('active_users', 0):,}
• Banned: {user_stats.get('banned_users', 0):,}
• Admin: {user_stats.get('admin_users', 0):,}
• Clone Bot Users: {user_stats.get('clone_bot_users', 0):,}

💬 **Percakapan:**
• Total Conversations: {memory_stats.get('total_conversations', 0):,}
• Total Messages: {memory_stats.get('total_messages', 0):,}
• Active Conversations: {memory_stats.get('active_conversations', 0):,}
• Avg Messages/Conv: {memory_stats.get('avg_messages_per_conversation', 0)}

🎯 **Poin & Gambar:**
• Total Points Used: {points_stats.get('total_points_used', 0):,}
• Images Generated: {points_stats.get('total_images_generated', 0):,}
• Users with Points: {points_stats.get('active_users_with_points', 0):,}

🎁 **Referral:**
• Total Referrals: {referral_stats.get('total_referrals', 0):,}
• Referral Points: {referral_stats.get('total_referral_points', 0):,}
• Active Referrers: {referral_stats.get('users_with_referrals', 0):,}

🤖 **Bot Info:**
• Uptime: {uptime_text}
• Bot ID: `{self.bot.bot_info.id}`
• Is Clone: {"Yes" if self.bot.is_clone else "No"}

📈 **Performance:**
• Memory Usage: Optimized
• Database: Connected
• Gemini AI: Active
                """.strip()
                
                # Create keyboard for detailed stats
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("👥 Top Users", callback_data="admin_top_users"),
                        InlineKeyboardButton("🎯 Top Points", callback_data="admin_top_points")
                    ],
                    [
                        InlineKeyboardButton("🎁 Referral Board", callback_data="admin_referral_board"),
                        InlineKeyboardButton("🔄 Refresh", callback_data="admin_refresh_stats")
                    ]
                ])
                
                await self.bot.client.edit_message_text(
                    message.chat.id,
                    loading_msg.id,
                    stats_text,
                    reply_markup=keyboard
                )
                
            except Exception as e:
                logger.error(f"Error getting detailed stats: {e}")
                await self.bot.client.edit_message_text(
                    message.chat.id,
                    loading_msg.id,
                    "❌ Terjadi kesalahan saat mengumpulkan statistik detail."
                )
            
        except Exception as e:
            logger.error(f"Error in stats command: {e}")
            await self.bot.send_message_safe(
                message.chat.id,
                "Terjadi kesalahan saat menampilkan statistik."
            )
    
    async def handle_broadcast(self, message: Message):
        """Handle /broadcast command"""
        try:
            if not self.is_admin(message.from_user.id):
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ Anda tidak memiliki akses admin."
                )
                return
            
            if len(message.command) < 2:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ **Format Salah**\n\nGunakan: `/broadcast <pesan>`\n\nContoh:\n`/broadcast Halo semua! Bot sedang update.`"
                )
                return
            
            broadcast_text = " ".join(message.command[1:])
            
            # Confirm broadcast
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Ya, Kirim", callback_data=f"confirm_broadcast"),
                    InlineKeyboardButton("❌ Batal", callback_data="cancel_broadcast")
                ]
            ])
            
            preview_text = f"""
📢 **Konfirmasi Broadcast**

📝 **Pesan yang akan dikirim:**
{broadcast_text}

⚠️ **Pesan ini akan dikirim ke semua pengguna bot.**
Apakah Anda yakin?
            """.strip()
            
            # Store broadcast text temporarily (you might want to use Redis for this)
            self.bot.pending_broadcast = {
                'text': broadcast_text,
                'admin_id': message.from_user.id
            }
            
            await self.bot.client.send_message(
                message.chat.id,
                preview_text,
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error in broadcast command: {e}")
            await self.bot.send_message_safe(
                message.chat.id,
                "Terjadi kesalahan saat mempersiapkan broadcast."
            )
    
    async def handle_users_list(self, message: Message):
        """Handle /users command"""
        try:
            if not self.is_admin(message.from_user.id):
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ Anda tidak memiliki akses admin."
                )
                return
            
            # Get search query if provided
            search_query = " ".join(message.command[1:]) if len(message.command) > 1 else None
            
            if search_query:
                # Search users
                users = await self.bot.user_service.search_users(search_query, 10)
                title = f"🔍 **Hasil Pencarian: '{search_query}'**"
            else:
                # Get top users
                users = await self.bot.user_service.get_top_users(10)
                title = "👥 **Top 10 Users (by messages)**"
            
            if not users:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ Tidak ada pengguna ditemukan."
                )
                return
            
            users_text = f"{title}\n\n"
            
            for i, user_data in enumerate(users, 1):
                # Handle both User objects and dict data
                if hasattr(user_data, 'user_id'):
                    user_id = user_data.user_id
                    first_name = user_data.first_name
                    username = user_data.username
                    message_count = user_data.message_count
                    is_banned = user_data.is_banned
                    is_admin = user_data.is_admin
                else:
                    user_id = user_data.get('user_id')
                    first_name = user_data.get('first_name', 'Unknown')
                    username = user_data.get('username')
                    message_count = user_data.get('message_count', 0)
                    is_banned = user_data.get('is_banned', False)
                    is_admin = user_data.get('is_admin', False)
                
                status_emoji = "🚫" if is_banned else "✅"
                admin_emoji = " 👑" if is_admin else ""
                username_text = f"@{username}" if username else "No username"
                
                users_text += f"""
{i}. {status_emoji} **{first_name}**{admin_emoji}
   ID: `{user_id}` | {username_text}
   Messages: {message_count:,}
""".strip() + "\n\n"
            
            users_text += "📋 **Commands:**\n"
            users_text += "• `/userinfo <user_id>` - Detail user\n"
            users_text += "• `/users <query>` - Cari user\n"
            users_text += "• `/ban <user_id>` - Ban user\n"
            users_text += "• `/unban <user_id>` - Unban user"
            
            await self.bot.send_message_safe(message.chat.id, users_text)
            
        except Exception as e:
            logger.error(f"Error in users list command: {e}")
            await self.bot.send_message_safe(
                message.chat.id,
                "Terjadi kesalahan saat menampilkan daftar pengguna."
            )
    
    async def handle_add_admin(self, message: Message):
        """Handle /addadmin command"""
        try:
            # Only owner can add admins
            if not self.bot.is_owner(message.from_user.id):
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ Hanya owner yang bisa menambah admin."
                )
                return
            
            if len(message.command) < 2:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ **Format Salah**\n\nGunakan: `/addadmin <user_id>`\n\nContoh:\n`/addadmin 123456789`"
                )
                return
            
            try:
                user_id = int(message.command[1])
            except ValueError:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ User ID harus berupa angka."
                )
                return
            
            # Set admin status
            success = await self.bot.user_service.set_admin(user_id, True)
            
            if success:
                user = await self.bot.user_service.get_user(user_id)
                user_name = user.first_name if user else "Unknown"
                
                await self.bot.send_message_safe(
                    message.chat.id,
                    f"✅ **Admin Ditambahkan**\n\n👤 **User:** {user_name} (`{user_id}`)\n👑 **Status:** Admin"
                )
                
                # Notify the new admin
                try:
                    await self.bot.client.send_message(
                        user_id,
                        "🎉 **Anda telah menjadi admin bot!**\n\nGunakan `/admin` untuk mengakses panel admin."
                    )
                except:
                    pass
                    
            else:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ Gagal menambahkan admin. User mungkin tidak ditemukan."
                )
            
        except Exception as e:
            logger.error(f"Error in add admin command: {e}")
            await self.bot.send_message_safe(
                message.chat.id,
                "Terjadi kesalahan saat menambahkan admin."
            )
    
    async def handle_remove_admin(self, message: Message):
        """Handle /removeadmin command"""
        try:
            # Only owner can remove admins
            if not self.bot.is_owner(message.from_user.id):
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ Hanya owner yang bisa menghapus admin."
                )
                return
            
            if len(message.command) < 2:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ **Format Salah**\n\nGunakan: `/removeadmin <user_id>`\n\nContoh:\n`/removeadmin 123456789`"
                )
                return
            
            try:
                user_id = int(message.command[1])
            except ValueError:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ User ID harus berupa angka."
                )
                return
            
            # Check if trying to remove owner
            if self.bot.is_owner(user_id):
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ Tidak dapat menghapus status admin owner."
                )
                return
            
            # Remove admin status
            success = await self.bot.user_service.set_admin(user_id, False)
            
            if success:
                user = await self.bot.user_service.get_user(user_id)
                user_name = user.first_name if user else "Unknown"
                
                await self.bot.send_message_safe(
                    message.chat.id,
                    f"✅ **Admin Dihapus**\n\n👤 **User:** {user_name} (`{user_id}`)\n👤 **Status:** User biasa"
                )
                
                # Notify the removed admin
                try:
                    await self.bot.client.send_message(
                        user_id,
                        "📢 **Status admin Anda telah dicabut.**\n\nAnda sekarang menjadi user biasa."
                    )
                except:
                    pass
                    
            else:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ Gagal menghapus admin. User mungkin tidak ditemukan."
                )
            
        except Exception as e:
            logger.error(f"Error in remove admin command: {e}")
            await self.bot.send_message_safe(
                message.chat.id,
                "Terjadi kesalahan saat menghapus admin."
            )
    
    async def handle_user_info(self, message: Message):
        """Handle /userinfo command"""
        try:
            if not self.is_admin(message.from_user.id):
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ Anda tidak memiliki akses admin."
                )
                return
            
            if len(message.command) < 2:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ **Format Salah**\n\nGunakan: `/userinfo <user_id>`\n\nContoh:\n`/userinfo 123456789`"
                )
                return
            
            try:
                user_id = int(message.command[1])
            except ValueError:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ User ID harus berupa angka."
                )
                return
            
            # Get user info
            user = await self.bot.user_service.get_user(user_id)
            if not user:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ User tidak ditemukan."
                )
                return
            
            # Get additional info
            conv_stats = await self.bot.memory_service.get_conversation_stats(user_id)
            if not conv_stats:
                conv_stats = {"total_messages": 0, "user_messages": 0, "assistant_messages": 0}
            
            referral_info = await self.bot.referral_service.get_referral_info(user)
            
            # Calculate account age
            from datetime import datetime
            age_delta = datetime.now() - user.join_date.replace(tzinfo=None)
            age_days = age_delta.days
            
            status_emoji = "🚫" if user.is_banned else "✅"
            admin_badge = " 👑" if user.is_admin else ""
            owner_badge = " 🔱" if self.bot.is_owner(user_id) else ""
            clone_badge = " 🤖" if user.has_clone_bot else ""
            
            user_info_text = f"""
👤 **Informasi Pengguna**

🆔 **Data Dasar:**
• ID: `{user.user_id}`
• Nama: {user.first_name}{admin_badge}{owner_badge}{clone_badge}
• Username: @{user.username or 'Tidak ada'}
• Status: {status_emoji} {"Banned" if user.is_banned else "Aktif"}

📅 **Aktivitas:**
• Bergabung: {user.join_date.strftime('%d/%m/%Y')} ({age_days} hari lalu)
• Aktivitas Terakhir: {user.last_activity.strftime('%d/%m/%Y %H:%M')}

💬 **Statistik Chat:**
• Total Pesan Bot: {user.message_count:,}
• Pesan User: {conv_stats['user_messages']:,}
• Pesan AI: {conv_stats['assistant_messages']:,}

🎯 **Poin & Gambar:**
• Poin Harian: {user.daily_points}
• Poin Referral: {user.referral_points}
• Total Poin Digunakan: {user.total_points_used:,}
• Gambar Dibuat: {user.image_generated:,}
• Reset Terakhir: {user.last_reset.strftime('%d/%m/%Y %H:%M') if user.last_reset else 'Never'}

🎁 **Referral:**
• Kode: `{user.referral_code}`
• Teman Diundang: {user.referral_count}
• Diundang oleh: {referral_info.get('referred_by', {}).get('first_name', 'Tidak ada') if referral_info.get('referred_by') else 'Tidak ada'}

🤖 **Bot Clone:**
• Memiliki Clone: {"Ya" if user.has_clone_bot else "Tidak"}
• Clone Bot ID: {user.clone_bot_id or 'Tidak ada'}
            """.strip()
            
            # Create action buttons
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🚫 Ban" if not user.is_banned else "✅ Unban", 
                                       callback_data=f"admin_toggle_ban_{user_id}"),
                    InlineKeyboardButton("👑 Admin" if not user.is_admin else "👤 User", 
                                       callback_data=f"admin_toggle_admin_{user_id}")
                ],
                [
                    InlineKeyboardButton("🎯 Give Points", callback_data=f"admin_give_points_{user_id}"),
                    InlineKeyboardButton("🔄 Reset Points", callback_data=f"admin_reset_points_{user_id}")
                ],
                [
                    InlineKeyboardButton("💬 Send Message", callback_data=f"admin_send_message_{user_id}"),
                    InlineKeyboardButton("🗑️ Clear Memory", callback_data=f"admin_clear_memory_{user_id}")
                ]
            ])
            
            await self.bot.client.send_message(
                message.chat.id,
                user_info_text,
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error in user info command: {e}")
            await self.bot.send_message_safe(
                message.chat.id,
                "Terjadi kesalahan saat mengambil informasi pengguna."
            )
    
    async def handle_give_points(self, message: Message):
        """Handle /givepoints command"""
        try:
            if not self.is_admin(message.from_user.id):
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ Anda tidak memiliki akses admin."
                )
                return
            
            if len(message.command) < 3:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ **Format Salah**\n\nGunakan: `/givepoints <user_id> <jumlah> [type]`\n\nContoh:\n`/givepoints 123456789 5 referral`\n\nType: daily atau referral (default: referral)"
                )
                return
            
            try:
                user_id = int(message.command[1])
                points = int(message.command[2])
                point_type = message.command[3] if len(message.command) > 3 else "referral"
            except ValueError:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ User ID dan jumlah poin harus berupa angka."
                )
                return
            
            if point_type not in ["daily", "referral"]:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ Type poin harus 'daily' atau 'referral'."
                )
                return
            
            if points <= 0 or points > 100:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ Jumlah poin harus antara 1-100."
                )
                return
            
            # Give points
            success = await self.bot.point_service.grant_bonus_points(user_id, points, point_type)
            
            if success:
                user = await self.bot.user_service.get_user(user_id)
                user_name = user.first_name if user else "Unknown"
                
                give_points_text = f"""
✅ **Poin Berhasil Diberikan**

👤 **User:** {user_name} (`{user_id}`)
🎯 **Poin:** +{points} poin {point_type}
👮 **Admin:** {message.from_user.first_name}
                """.strip()
                
                await self.bot.send_message_safe(message.chat.id, give_points_text)
                
                # Notify user
                try:
                    await self.bot.client.send_message(
                        user_id,
                        f"🎉 **Bonus Poin Diterima!**\n\n🎯 **Poin:** +{points} poin {point_type}\n💝 **Dari:** Admin\n\nGunakan `/points` untuk melihat total poin Anda."
                    )
                except:
                    pass
                    
            else:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ Gagal memberikan poin. User mungkin tidak ditemukan."
                )
            
        except Exception as e:
            logger.error(f"Error in give points command: {e}")
            await self.bot.send_message_safe(
                message.chat.id,
                "Terjadi kesalahan saat memberikan poin."
            )
    
    async def handle_reset_points(self, message: Message):
        """Handle /resetpoints command"""
        try:
            if not self.is_admin(message.from_user.id):
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ Anda tidak memiliki akses admin."
                )
                return
            
            if len(message.command) < 2:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ **Format Salah**\n\nGunakan: `/resetpoints <user_id|all>`\n\nContoh:\n`/resetpoints 123456789`\n`/resetpoints all`"
                )
                return
            
            target = message.command[1]
            
            if target.lower() == "all":
                # Reset all users (only owner can do this)
                if not self.bot.is_owner(message.from_user.id):
                    await self.bot.send_message_safe(
                        message.chat.id,
                        "❌ Hanya owner yang bisa reset poin semua user."
                    )
                    return
                
                # Confirm action
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("✅ Ya, Reset Semua", callback_data="confirm_reset_all_points"),
                        InlineKeyboardButton("❌ Batal", callback_data="cancel_reset_points")
                    ]
                ])
                
                await self.bot.client.send_message(
                    message.chat.id,
                    "⚠️ **Konfirmasi Reset Poin Semua User**\n\nApakah Anda yakin ingin mereset poin harian semua pengguna? Tindakan ini tidak dapat dibatalkan.",
                    reply_markup=keyboard
                )
                return
            
            # Reset specific user
            try:
                user_id = int(target)
            except ValueError:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ User ID harus berupa angka atau 'all'."
                )
                return
            
            success = await self.bot.point_service.manual_reset_user_points(user_id)
            
            if success:
                user = await self.bot.user_service.get_user(user_id)
                user_name = user.first_name if user else "Unknown"
                
                await self.bot.send_message_safe(
                    message.chat.id,
                    f"✅ **Poin Direset**\n\n👤 **User:** {user_name} (`{user_id}`)\n🎯 **Poin harian direset ke {settings.DAILY_POINTS}**\n👮 **Admin:** {message.from_user.first_name}"
                )
                
                # Notify user
                try:
                    await self.bot.client.send_message(
                        user_id,
                        f"🔄 **Poin Harian Direset**\n\nPoin harian Anda telah direset ke {settings.DAILY_POINTS} oleh admin."
                    )
                except:
                    pass
                    
            else:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ Gagal mereset poin. User mungkin tidak ditemukan."
                )
            
        except Exception as e:
            logger.error(f"Error in reset points command: {e}")
            await self.bot.send_message_safe(
                message.chat.id,
                "Terjadi kesalahan saat mereset poin."
            )
    
    async def handle_maintenance(self, message: Message):
        """Handle /maintenance command"""
        try:
            if not self.is_admin(message.from_user.id):
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ Anda tidak memiliki akses admin."
                )
                return
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🗑️ Cleanup Old Conversations", callback_data="maintenance_cleanup_conversations"),
                    InlineKeyboardButton("🗑️ Cleanup Inactive Users", callback_data="maintenance_cleanup_users")
                ],
                [
                    InlineKeyboardButton("💾 Optimize Memory", callback_data="maintenance_optimize_memory"),
                    InlineKeyboardButton("🔄 Reset Daily Points", callback_data="maintenance_reset_points")
                ],
                [
                    InlineKeyboardButton("📊 Database Stats", callback_data="maintenance_db_stats"),
                    InlineKeyboardButton("🔧 System Info", callback_data="maintenance_system_info")
                ]
            ])
            
            maintenance_text = """
🔧 **Maintenance Panel**

⚙️ **Available Operations:**
• Cleanup old conversations (90+ days)
• Remove inactive users (90+ days, <5 messages)
• Optimize memory usage for all users
• Manual daily points reset
• View database statistics
• System information

⚠️ **Warning:** Some operations cannot be undone.
Choose carefully.
            """.strip()
            
            await self.bot.client.send_message(
                message.chat.id,
                maintenance_text,
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error in maintenance command: {e}")
            await self.bot.send_message_safe(
                message.chat.id,
                "Terjadi kesalahan saat menampilkan panel maintenance."
            )
    
    async def execute_broadcast(self, broadcast_text: str, admin_id: int) -> dict:
        """Execute broadcast to all users"""
        try:
            # Get all user IDs
            user_ids = await self.bot.user_service.get_users_for_broadcast(exclude_banned=True)
            
            if not user_ids:
                return {"success": 0, "failed": 0, "total": 0}
            
            success_count = 0
            failed_count = 0
            total_count = len(user_ids)
            
            # Send broadcast in batches to avoid rate limits
            batch_size = 30  # Telegram limit
            for i in range(0, len(user_ids), batch_size):
                batch = user_ids[i:i + batch_size]
                
                tasks = []
                for user_id in batch:
                    if user_id != admin_id:  # Don't send to admin who initiated
                        tasks.append(self._send_broadcast_message(user_id, broadcast_text))
                
                # Execute batch
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, Exception):
                        failed_count += 1
                    elif result:
                        success_count += 1
                    else:
                        failed_count += 1
                
                # Small delay between batches
                await asyncio.sleep(1)
            
            return {
                "success": success_count,
                "failed": failed_count,
                "total": total_count
            }
            
        except Exception as e:
            logger.error(f"Error executing broadcast: {e}")
            return {"success": 0, "failed": 0, "total": 0}
    
    async def _send_broadcast_message(self, user_id: int, message: str) -> bool:
        """Send broadcast message to a single user"""
        try:
            await self.bot.client.send_message(
                user_id,
                f"📢 **Broadcast dari Admin**\n\n{message}"
            )
            return True
        except Exception as e:
            logger.debug(f"Failed to send broadcast to {user_id}: {e}")
            return False
