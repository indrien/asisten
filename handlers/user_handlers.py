import logging
import os
import asyncio
from typing import TYPE_CHECKING
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from gtts import gTTS
import tempfile

if TYPE_CHECKING:
    from core.bot import TelegramBot

logger = logging.getLogger(__name__)

class UserHandlers:
    def __init__(self, bot: 'TelegramBot'):
        self.bot = bot
    
    def register_handlers(self):
        """Register all user handlers"""
        
        @self.bot.client.on_message(filters.command("start"))
        async def start_command(client, message: Message):
            await self.handle_start(message)
        
        @self.bot.client.on_message(filters.command("help"))
        async def help_command(client, message: Message):
            await self.handle_help(message)
        
        @self.bot.client.on_message(filters.command("points"))
        async def points_command(client, message: Message):
            await self.handle_points(message)
        
        @self.bot.client.on_message(filters.command("referral"))
        async def referral_command(client, message: Message):
            await self.handle_referral(message)
        
        @self.bot.client.on_message(filters.command("invite"))
        async def invite_command(client, message: Message):
            await self.handle_invite(message)
        
        @self.bot.client.on_message(filters.command("profile"))
        async def profile_command(client, message: Message):
            await self.handle_profile(message)
        
        @self.bot.client.on_message(filters.command("memory"))
        async def memory_command(client, message: Message):
            await self.handle_memory(message)
        
        @self.bot.client.on_message(filters.command("clear"))
        async def clear_command(client, message: Message):
            await self.handle_clear_memory(message)
        
        @self.bot.client.on_message(filters.command("image") | filters.command("img"))
        async def image_command(client, message: Message):
            await self.handle_image_generation(message)
        
        @self.bot.client.on_message(filters.command("voice") | filters.command("tts"))
        async def voice_command(client, message: Message):
            await self.handle_voice_generation(message)
        
        # Handle regular text messages
        @self.bot.client.on_message(filters.text & ~filters.command(None))
        async def text_message(client, message: Message):
            await self.handle_text_message(message)
        
        # Handle photo messages
        @self.bot.client.on_message(filters.photo)
        async def photo_message(client, message: Message):
            await self.handle_photo_message(message)
    
    async def handle_start(self, message: Message):
        """Handle /start command"""
        try:
            user_id = message.from_user.id
            first_name = message.from_user.first_name
            username = message.from_user.username
            
            # Check for referral code in start parameter
            referral_code = None
            if len(message.command) > 1:
                param = message.command[1]
                if param.startswith("ref_"):
                    referral_code = param[4:]  # Remove "ref_" prefix
            
            # Get or create user
            user = await self.bot.user_service.get_or_create_user(
                user_id=user_id,
                first_name=first_name,
                username=username
            )
            
            # Process referral if provided and user is new
            referral_message = ""
            if referral_code and not user.referred_by:
                success, msg = await self.bot.referral_service.process_referral(user_id, referral_code)
                if success:
                    referral_message = f"\n\n🎉 {msg}"
                else:
                    referral_message = f"\n\n⚠️ {msg}"
            
            # Update bot stats
            await self.bot.update_stats("users")
            
            welcome_text = f"""
👋 Halo {first_name}! Selamat datang di **{self.bot.bot_info.first_name}**!

🤖 Saya adalah asisten AI yang didukung oleh Gemini AI 2.5. Saya bisa membantu Anda dengan:

✨ **Fitur Utama:**
• 💬 Chat unlimited dengan AI
• 🖼️ Generasi gambar dengan AI
• 🔊 Text-to-Speech (TTS)
• 📷 Analisis gambar
• 💾 Memory percakapan tersimpan

🎯 **Sistem Poin:**
• Dapatkan 3 poin harian untuk generasi gambar
• Reset otomatis setiap jam 12 malam WIB
• Bonus poin dari referral teman

🎁 **Referral:**
• Ajak teman dan dapatkan poin bonus
• Gunakan `/referral` untuk info lengkap

📋 **Perintah:**
• `/help` - Bantuan lengkap
• `/points` - Cek poin Anda
• `/profile` - Profil Anda
• `/image [prompt]` - Buat gambar
• `/voice [teks]` - Text-to-Speech

Silakan mulai chat dengan saya! 😊{referral_message}
            """.strip()
            
            await self.bot.send_message_safe(message.chat.id, welcome_text)
            
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await self.bot.send_message_safe(
                message.chat.id, 
                "Terjadi kesalahan. Silakan coba lagi."
            )
    
    async def handle_help(self, message: Message):
        """Handle /help command"""
        try:
            help_text = f"""
📖 **Bantuan - {self.bot.bot_info.first_name}**

🤖 **Tentang Bot:**
Saya adalah asisten AI yang menggunakan Gemini AI 2.5 untuk memberikan respons yang cerdas dan membantu.

💬 **Chat dengan AI:**
• Ketik pesan apa saja untuk memulai percakapan
• Kirim foto untuk analisis gambar
• Memory percakapan otomatis tersimpan

🖼️ **Generasi Gambar:**
• `/image [deskripsi]` - Buat gambar dari teks
• Contoh: `/image kucing lucu bermain bola`
• Membutuhkan poin (3 poin harian)

🔊 **Text-to-Speech:**
• `/voice [teks]` - Ubah teks jadi suara
• Contoh: `/voice Halo semuanya`

📊 **Sistem Poin:**
• `/points` - Cek poin Anda
• 3 poin harian untuk generasi gambar
• Reset setiap jam 12 malam WIB

🎁 **Referral:**
• `/referral` - Info kode referral Anda
• `/invite` - Bagikan link undangan
• Bonus poin untuk setiap teman yang diundang

👤 **Profil & Memory:**
• `/profile` - Lihat profil Anda
• `/memory` - Statistik percakapan
• `/clear` - Hapus memory percakapan

❓ **Tips:**
• Gunakan bahasa Indonesia untuk hasil terbaik
• Ajukan pertanyaan spesifik untuk jawaban yang lebih baik
• Ajak teman untuk mendapat poin bonus!

💝 **Dukungan:**
Jika ada masalah, hubungi admin melalui bot ini.
            """.strip()
            
            await self.bot.send_message_safe(message.chat.id, help_text)
            
        except Exception as e:
            logger.error(f"Error in help command: {e}")
            await self.bot.send_message_safe(
                message.chat.id, 
                "Terjadi kesalahan saat menampilkan bantuan."
            )
    
    async def handle_points(self, message: Message):
        """Handle /points command"""
        try:
            user = await self.bot.user_service.get_or_create_user(
                user_id=message.from_user.id,
                first_name=message.from_user.first_name,
                username=message.from_user.username
            )
            
            points_info = await self.bot.point_service.get_user_points_info(user)
            
            if not points_info:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "Gagal mengambil informasi poin. Silakan coba lagi."
                )
                return
            
            points_text = f"""
🎯 **Informasi Poin Anda**

💎 **Poin Tersedia:**
• Poin Harian: {points_info['daily_points']} 
• Poin Referral: {points_info['referral_points']}
• **Total Poin: {points_info['total_points']}**

📊 **Statistik:**
• Total Poin Terpakai: {points_info['total_points_used']}
• Gambar Dibuat: {points_info['images_generated']}

⏰ **Reset Berikutnya:**
{points_info['time_until_reset']['text']} lagi
(Setiap jam 12 malam WIB)

🎯 **Status:** {"✅ Bisa buat gambar" if points_info['can_generate'] else "❌ Poin habis"}

💡 **Cara Mendapat Poin:**
• Otomatis: 3 poin setiap hari
• Referral: Undang teman dengan `/invite`
• Bonus: Ikuti event khusus

📋 **Info Lengkap:** `/help`
            """.strip()
            
            await self.bot.send_message_safe(message.chat.id, points_text)
            
        except Exception as e:
            logger.error(f"Error in points command: {e}")
            await self.bot.send_message_safe(
                message.chat.id,
                "Terjadi kesalahan saat mengambil informasi poin."
            )
    
    async def handle_referral(self, message: Message):
        """Handle /referral command"""
        try:
            user = await self.bot.user_service.get_or_create_user(
                user_id=message.from_user.id,
                first_name=message.from_user.first_name,
                username=message.from_user.username
            )
            
            referral_info = await self.bot.referral_service.get_referral_info(user)
            
            if not referral_info:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "Gagal mengambil informasi referral. Silakan coba lagi."
                )
                return
            
            # Prepare referred users list
            referred_list = ""
            if referral_info['referred_users']:
                referred_list = "\n👥 **Teman yang Diundang:**\n"
                for i, ref_user in enumerate(referral_info['referred_users'][:5], 1):
                    name = ref_user.get('first_name', 'Unknown')
                    username = f"@{ref_user['username']}" if ref_user.get('username') else "No username"
                    referred_list += f"{i}. {name} ({username})\n"
                
                if len(referral_info['referred_users']) > 5:
                    referred_list += f"... dan {len(referral_info['referred_users']) - 5} lainnya\n"
            
            referrer_info = ""
            if referral_info['referred_by']:
                ref_by = referral_info['referred_by']
                ref_name = ref_by.get('first_name', 'Unknown')
                ref_username = f"@{ref_by['username']}" if ref_by.get('username') else "No username"
                referrer_info = f"\n🙏 **Diundang oleh:** {ref_name} ({ref_username})"
            
            referral_text = f"""
🎁 **Sistem Referral Anda**

🔑 **Kode Referral:** `{referral_info['referral_code']}`

📊 **Statistik:**
• Teman Diundang: {referral_info['referral_count']} orang
• Poin Referral: {referral_info['referral_points']} poin
• Total Poin Earned: {referral_info['total_points_earned']} poin{referrer_info}

{referred_list}
💰 **Reward per Referral:**
• Anda: +3 poin referral
• Teman: +3 poin referral

📋 **Cara Mengundang:**
1. Gunakan `/invite` untuk link undangan
2. Bagikan ke teman
3. Teman mulai chat dan masukkan kode
4. Anda berdua dapat poin!

💡 **Tips:** Semakin banyak mengundang, semakin banyak poin!
            """.strip()
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 Bagikan Link", callback_data=f"share_referral_{user.user_id}")],
                [InlineKeyboardButton("📊 Leaderboard", callback_data="referral_leaderboard")]
            ])
            
            await self.bot.client.send_message(
                message.chat.id, 
                referral_text,
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error in referral command: {e}")
            await self.bot.send_message_safe(
                message.chat.id,
                "Terjadi kesalahan saat mengambil informasi referral."
            )
    
    async def handle_invite(self, message: Message):
        """Handle /invite command"""
        try:
            user = await self.bot.user_service.get_or_create_user(
                user_id=message.from_user.id,
                first_name=message.from_user.first_name,
                username=message.from_user.username
            )
            
            bot_username = self.bot.bot_info.username
            referral_link = await self.bot.referral_service.generate_referral_link(user, bot_username)
            
            invite_text = f"""
🎉 **Undang Teman dan Dapatkan Poin!**

🔗 **Link Undangan Anda:**
{referral_link}

🎁 **Keuntungan:**
• Anda: +3 poin referral
• Teman: +3 poin referral

📋 **Cara Kerja:**
1. Bagikan link di atas ke teman
2. Teman klik link dan mulai chat
3. Teman masukkan kode: `{user.referral_code}`
4. Kalian berdua langsung dapat poin!

💡 **Alternatif:**
Teman bisa langsung chat ke @{bot_username} dan ketik:
`/start ref_{user.referral_code}`

🏆 **Tips Sukses:**
• Bagikan ke grup WhatsApp/Telegram
• Posting di media sosial
• Ceritakan manfaat bot ini
• Ajak teman yang suka teknologi AI

📊 Cek progress: `/referral`
            """.strip()
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 Share via Telegram", 
                                    url=f"https://t.me/share/url?url={referral_link}&text=Halo! Aku mau ajak kamu coba bot AI keren ini. Kita berdua bakal dapat poin bonus lho! 🎉")]
            ])
            
            await self.bot.client.send_message(
                message.chat.id,
                invite_text,
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
            
        except Exception as e:
            logger.error(f"Error in invite command: {e}")
            await self.bot.send_message_safe(
                message.chat.id,
                "Terjadi kesalahan saat membuat link undangan."
            )
    
    async def handle_profile(self, message: Message):
        """Handle /profile command"""
        try:
            user = await self.bot.user_service.get_or_create_user(
                user_id=message.from_user.id,
                first_name=message.from_user.first_name,
                username=message.from_user.username
            )
            
            # Get conversation stats
            conv_stats = await self.bot.memory_service.get_conversation_stats(user.user_id)
            if not conv_stats:
                conv_stats = {"total_messages": 0, "user_messages": 0, "assistant_messages": 0}
            
            # Calculate account age
            from datetime import datetime
            age_delta = datetime.now() - user.join_date.replace(tzinfo=None)
            age_days = age_delta.days
            
            status_emoji = "🚫" if user.is_banned else "✅"
            admin_badge = " 👑" if user.is_admin else ""
            clone_badge = " 🤖" if user.has_clone_bot else ""
            
            profile_text = f"""
👤 **Profil Anda**

🆔 **Informasi Dasar:**
• ID: `{user.user_id}`
• Nama: {user.first_name}{admin_badge}{clone_badge}
• Username: @{user.username or 'Tidak ada'}
• Status: {status_emoji} {"Banned" if user.is_banned else "Aktif"}

📅 **Aktivitas:**
• Bergabung: {user.join_date.strftime('%d/%m/%Y')} ({age_days} hari lalu)
• Aktivitas Terakhir: {user.last_activity.strftime('%d/%m/%Y %H:%M')}

💬 **Statistik Chat:**
• Total Pesan: {user.message_count:,}
• Pesan User: {conv_stats['user_messages']:,}
• Pesan AI: {conv_stats['assistant_messages']:,}

🎯 **Poin & Gambar:**
• Poin Harian: {user.daily_points}
• Poin Referral: {user.referral_points}
• Total Poin Digunakan: {user.total_points_used:,}
• Gambar Dibuat: {user.image_generated:,}

🎁 **Referral:**
• Kode: `{user.referral_code}`
• Teman Diundang: {user.referral_count}
• Poin dari Referral: {user.referral_count * 3}

📋 **Quick Actions:**
• `/points` - Cek poin terkini
• `/referral` - Info referral
• `/memory` - Statistik percakapan
            """.strip()
            
            await self.bot.send_message_safe(message.chat.id, profile_text)
            
        except Exception as e:
            logger.error(f"Error in profile command: {e}")
            await self.bot.send_message_safe(
                message.chat.id,
                "Terjadi kesalahan saat mengambil profil."
            )
    
    async def handle_memory(self, message: Message):
        """Handle /memory command"""
        try:
            conv_stats = await self.bot.memory_service.get_conversation_stats(message.from_user.id)
            
            if not conv_stats:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "Anda belum memiliki percakapan dengan bot."
                )
                return
            
            recent_messages = await self.bot.memory_service.get_recent_messages(message.from_user.id, 5)
            
            recent_text = ""
            if recent_messages:
                recent_text = "\n📝 **5 Pesan Terakhir:**\n"
                for i, msg in enumerate(recent_messages[-5:], 1):
                    role_emoji = "👤" if msg.role == "user" else "🤖"
                    content_preview = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
                    recent_text += f"{i}. {role_emoji} {content_preview}\n"
            
            memory_text = f"""
💾 **Memory Percakapan**

📊 **Statistik:**
• Total Pesan: {conv_stats['total_messages']}
• Pesan Anda: {conv_stats['user_messages']}
• Pesan AI: {conv_stats['assistant_messages']}
• Pesan Gambar: {conv_stats.get('image_messages', 0)}
• Pesan Audio: {conv_stats.get('audio_messages', 0)}

{recent_text}
⚙️ **Pengaturan Memory:**
• Memory otomatis tersimpan
• Maksimal 50 pesan terakhir
• Memory dioptimasi secara otomatis

🗑️ **Hapus Memory:** `/clear`
            """.strip()
            
            await self.bot.send_message_safe(message.chat.id, memory_text)
            
        except Exception as e:
            logger.error(f"Error in memory command: {e}")
            await self.bot.send_message_safe(
                message.chat.id,
                "Terjadi kesalahan saat mengambil informasi memory."
            )
    
    async def handle_clear_memory(self, message: Message):
        """Handle /clear command"""
        try:
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Ya, Hapus", callback_data=f"clear_memory_{message.from_user.id}"),
                    InlineKeyboardButton("❌ Batal", callback_data="cancel_clear")
                ]
            ])
            
            await self.bot.client.send_message(
                message.chat.id,
                "⚠️ **Konfirmasi Hapus Memory**\n\nApakah Anda yakin ingin menghapus semua memory percakapan? Tindakan ini tidak dapat dibatalkan.",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error in clear memory command: {e}")
            await self.bot.send_message_safe(
                message.chat.id,
                "Terjadi kesalahan saat memproses permintaan."
            )
    
    async def handle_image_generation(self, message: Message):
        """Handle /image command"""
        try:
            user = await self.bot.user_service.get_or_create_user(
                user_id=message.from_user.id,
                first_name=message.from_user.first_name,
                username=message.from_user.username
            )
            
            # Check if user can generate image
            if not await self.bot.point_service.can_user_generate_image(user):
                points_info = await self.bot.point_service.get_user_points_info(user)
                no_points_text = f"""
❌ **Poin Tidak Cukup**

💎 **Poin Anda:**
• Poin Harian: {points_info['daily_points']}
• Poin Referral: {points_info['referral_points']}

⏰ **Reset Berikutnya:** {points_info['time_until_reset']['text']} lagi

🎁 **Cara Mendapat Poin:**
• Tunggu reset harian (jam 12 malam WIB)
• Undang teman dengan `/invite`

📋 **Info Lengkap:** `/points`
                """.strip()
                
                await self.bot.send_message_safe(message.chat.id, no_points_text)
                return
            
            # Get prompt from command
            if len(message.command) < 2:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ **Format Salah**\n\nGunakan: `/image [deskripsi gambar]`\n\nContoh:\n`/image kucing lucu sedang bermain`"
                )
                return
            
            prompt = " ".join(message.command[1:])
            
            if len(prompt) < 5:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ Deskripsi gambar terlalu pendek. Minimal 5 karakter."
                )
                return
            
            # Use point
            success = await self.bot.point_service.use_point_for_image(user)
            if not success:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ Gagal menggunakan poin. Silakan coba lagi."
                )
                return
            
            # Send processing message
            processing_msg = await self.bot.client.send_message(
                message.chat.id,
                "🎨 **Sedang membuat gambar...**\n\nPrompt: " + prompt + "\n\n⏳ Mohon tunggu sebentar..."
            )
            
            try:
                # Note: Gemini 2.5 doesn't generate images directly
                # This is a placeholder for future image generation
                # You would integrate with other services like DALL-E, Stable Diffusion, etc.
                
                await asyncio.sleep(2)  # Simulate processing time
                
                await self.bot.client.edit_message_text(
                    message.chat.id,
                    processing_msg.id,
                    "❌ **Fitur Sedang Dikembangkan**\n\nGenerasi gambar sedang dalam tahap pengembangan. Poin Anda telah dikembalikan.\n\n💡 **Coming Soon:**\n• Integrasi dengan Stable Diffusion\n• Multiple style options\n• High-quality image generation"
                )
                
                # Return the point (since feature is not implemented yet)
                user.daily_points += 1
                user.total_points_used -= 1
                user.image_generated -= 1
                await self.bot.user_service.update_user(user)
                
            except Exception as e:
                logger.error(f"Error in image generation: {e}")
                await self.bot.client.edit_message_text(
                    message.chat.id,
                    processing_msg.id,
                    "❌ Terjadi kesalahan saat membuat gambar. Poin Anda telah dikembalikan."
                )
                
                # Return the point
                user.daily_points += 1
                user.total_points_used -= 1
                user.image_generated -= 1
                await self.bot.user_service.update_user(user)
            
            # Update stats and add to memory
            await self.bot.update_stats("images")
            await self.bot.memory_service.add_message(
                user.user_id, "user", f"Meminta gambar: {prompt}", "image"
            )
            
        except Exception as e:
            logger.error(f"Error in image generation command: {e}")
            await self.bot.send_message_safe(
                message.chat.id,
                "Terjadi kesalahan saat memproses permintaan gambar."
            )
    
    async def handle_voice_generation(self, message: Message):
        """Handle /voice command"""
        try:
            # Get text from command
            if len(message.command) < 2:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ **Format Salah**\n\nGunakan: `/voice [teks]`\n\nContoh:\n`/voice Halo, apa kabar?`"
                )
                return
            
            text = " ".join(message.command[1:])
            
            if len(text) > 500:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ Teks terlalu panjang. Maksimal 500 karakter."
                )
                return
            
            # Send processing message
            processing_msg = await self.bot.client.send_message(
                message.chat.id,
                "🔊 **Sedang membuat audio...**\n\n⏳ Mohon tunggu sebentar..."
            )
            
            try:
                # Generate TTS
                tts = gTTS(text=text, lang='id', slow=False)
                
                # Save to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                    tts.save(temp_file.name)
                    temp_path = temp_file.name
                
                # Send voice message
                await self.bot.client.send_voice(
                    message.chat.id,
                    temp_path,
                    caption=f"🔊 **Text-to-Speech**\n\nTeks: {text[:100]}{'...' if len(text) > 100 else ''}"
                )
                
                # Delete processing message
                await self.bot.client.delete_messages(message.chat.id, processing_msg.id)
                
                # Clean up temp file
                os.unlink(temp_path)
                
                # Add to memory
                await self.bot.memory_service.add_message(
                    message.from_user.id, "user", f"Meminta TTS: {text}", "audio"
                )
                await self.bot.memory_service.add_message(
                    message.from_user.id, "assistant", "Audio TTS telah dibuat", "audio"
                )
                
            except Exception as e:
                logger.error(f"Error generating voice: {e}")
                await self.bot.client.edit_message_text(
                    message.chat.id,
                    processing_msg.id,
                    "❌ Terjadi kesalahan saat membuat audio. Silakan coba lagi."
                )
            
        except Exception as e:
            logger.error(f"Error in voice generation command: {e}")
            await self.bot.send_message_safe(
                message.chat.id,
                "Terjadi kesalahan saat memproses permintaan audio."
            )
    
    async def handle_text_message(self, message: Message):
        """Handle regular text messages"""
        try:
            user = await self.bot.user_service.get_or_create_user(
                user_id=message.from_user.id,
                first_name=message.from_user.first_name,
                username=message.from_user.username
            )
            
            # Check if user is banned
            if user.is_banned:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ Anda telah dibanned dari menggunakan bot ini."
                )
                return
            
            # Check for referral code pattern
            user_text = message.text.strip()
            if user_text.startswith("ref_") or (len(user_text) == 8 and user_text.isupper()):
                # This might be a referral code
                referral_code = user_text.replace("ref_", "") if user_text.startswith("ref_") else user_text
                
                if not user.referred_by:  # Only if user hasn't used referral before
                    success, msg = await self.bot.referral_service.process_referral(user.user_id, referral_code)
                    await self.bot.send_message_safe(message.chat.id, f"🎁 {msg}")
                    return
            
            # Send typing action
            await self.bot.client.send_chat_action(message.chat.id, "typing")
            
            # Add user message to memory
            await self.bot.memory_service.add_message(
                user.user_id, "user", user_text
            )
            
            # Get conversation history
            history = await self.bot.memory_service.get_conversation_history(user.user_id, 10)
            
            # Generate response using Gemini
            system_prompt = self.bot.gemini_client.get_system_prompt()
            response = await self.bot.gemini_client.generate_text_response(
                prompt=user_text,
                conversation_history=history,
                system_prompt=system_prompt
            )
            
            # Send response
            await self.bot.send_message_safe(message.chat.id, response)
            
            # Add assistant response to memory
            await self.bot.memory_service.add_message(
                user.user_id, "assistant", response
            )
            
            # Update stats
            await self.bot.update_stats("messages")
            
        except Exception as e:
            logger.error(f"Error handling text message: {e}")
            await self.bot.send_message_safe(
                message.chat.id,
                "Maaf, terjadi kesalahan saat memproses pesan Anda. Silakan coba lagi."
            )
    
    async def handle_photo_message(self, message: Message):
        """Handle photo messages"""
        try:
            user = await self.bot.user_service.get_or_create_user(
                user_id=message.from_user.id,
                first_name=message.from_user.first_name,
                username=message.from_user.username
            )
            
            # Check if user is banned
            if user.is_banned:
                await self.bot.send_message_safe(
                    message.chat.id,
                    "❌ Anda telah dibanned dari menggunakan bot ini."
                )
                return
            
            # Send processing message
            processing_msg = await self.bot.client.send_message(
                message.chat.id,
                "📷 **Sedang menganalisis gambar...**\n\n⏳ Mohon tunggu sebentar..."
            )
            
            try:
                # Download the photo
                photo = message.photo
                file_id = photo.file_id
                
                file_info = await self.bot.client.get_file(file_id)
                
                # Create temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                    await self.bot.client.download_media(file_id, temp_file.name)
                    temp_path = temp_file.name
                
                # Get user's prompt if any
                prompt = "Deskripsikan gambar ini secara detail dalam bahasa Indonesia."
                if message.caption:
                    prompt = f"Analisis gambar ini berdasarkan pertanyaan: {message.caption}"
                
                # Analyze image using Gemini Vision
                response = await self.bot.gemini_client.generate_image_description(temp_path, prompt)
                
                # Edit processing message with result
                await self.bot.client.edit_message_text(
                    message.chat.id,
                    processing_msg.id,
                    f"📷 **Analisis Gambar**\n\n{response}"
                )
                
                # Clean up temp file
                os.unlink(temp_path)
                
                # Add to memory
                image_prompt = f"Mengirim gambar{f' dengan caption: {message.caption}' if message.caption else ''}"
                await self.bot.memory_service.add_message(
                    user.user_id, "user", image_prompt, "image"
                )
                await self.bot.memory_service.add_message(
                    user.user_id, "assistant", response, "text"
                )
                
            except Exception as e:
                logger.error(f"Error analyzing image: {e}")
                await self.bot.client.edit_message_text(
                    message.chat.id,
                    processing_msg.id,
                    "❌ Terjadi kesalahan saat menganalisis gambar. Silakan coba lagi."
                )
            
        except Exception as e:
            logger.error(f"Error handling photo message: {e}")
            await self.bot.send_message_safe(
                message.chat.id,
                "Terjadi kesalahan saat memproses gambar."
            )
