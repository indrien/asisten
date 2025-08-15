import google.generativeai as genai
from typing import List, Dict, Any, Optional, Union
import logging
import asyncio
import io
from PIL import Image
import aiofiles
import os
from config.settings import settings

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = None
        self.vision_model = None
        self._setup_client()
    
    def _setup_client(self):
        """Setup Gemini client"""
        try:
            genai.configure(api_key=self.api_key)
            
            # Chat model (Gemini 2.5)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            # Vision model for image analysis
            self.vision_model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            logger.info("Gemini client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise
    
    async def generate_text_response(self, 
                                   prompt: str, 
                                   conversation_history: List[Dict[str, Any]] = None,
                                   system_prompt: str = None) -> str:
        """Generate text response from Gemini"""
        try:
            # Prepare the conversation
            messages = []
            
            # Add system prompt if provided
            if system_prompt:
                messages.append({
                    "role": "user",
                    "parts": [{"text": f"System: {system_prompt}"}]
                })
                messages.append({
                    "role": "model", 
                    "parts": [{"text": "Understood. I'll follow these instructions."}]
                })
            
            # Add conversation history
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add current prompt
            messages.append({
                "role": "user",
                "parts": [{"text": prompt}]
            })
            
            # Start chat with history
            chat = self.model.start_chat(history=messages[:-1] if len(messages) > 1 else [])
            
            # Generate response
            response = await asyncio.to_thread(
                chat.send_message, 
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=2048,
                )
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating text response: {e}")
            return "Maaf, terjadi kesalahan saat memproses permintaan Anda. Silakan coba lagi."
    
    async def generate_image_description(self, image_path: str, prompt: str = None) -> str:
        """Analyze image and generate description"""
        try:
            # Read image file
            async with aiofiles.open(image_path, 'rb') as file:
                image_data = await file.read()
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Prepare prompt
            if not prompt:
                prompt = "Deskripsikan gambar ini secara detail dalam bahasa Indonesia."
            
            # Generate response
            response = await asyncio.to_thread(
                self.vision_model.generate_content,
                [prompt, image],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=1024,
                )
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return "Maaf, gagal menganalisis gambar. Silakan coba lagi."
    
    async def generate_image_from_text(self, prompt: str, style: str = "realistic") -> Optional[str]:
        """Generate image from text prompt using Gemini"""
        try:
            # Note: Gemini 2.5 doesn't directly generate images
            # This is a placeholder for future image generation capability
            # You might want to integrate with other services like DALL-E, Midjourney, etc.
            
            # For now, return a message explaining the limitation
            return None
            
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return None
    
    async def summarize_conversation(self, messages: List[Dict[str, Any]]) -> str:
        """Summarize conversation for memory optimization"""
        try:
            # Prepare conversation text
            conversation_text = ""
            for msg in messages:
                role = "User" if msg["role"] == "user" else "Assistant"
                if "parts" in msg and msg["parts"]:
                    content = msg["parts"][0].get("text", "")
                    conversation_text += f"{role}: {content}\n"
            
            prompt = f"""
            Buatlah ringkasan singkat dari percakapan berikut dalam bahasa Indonesia:
            
            {conversation_text}
            
            Ringkasan harus mencakup poin-poin penting dan konteks yang relevan untuk percakapan selanjutnya.
            Maksimal 200 kata.
            """
            
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=512,
                )
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error summarizing conversation: {e}")
            return "Ringkasan percakapan tidak tersedia."
    
    def get_system_prompt(self) -> str:
        """Get default system prompt for the assistant"""
        return """
        Anda adalah asisten AI yang cerdas dan membantu bernama AsistenAI. 
        Anda dibuat untuk membantu pengguna dengan berbagai pertanyaan dan tugas.
        
        Karakteristik Anda:
        - Ramah dan sopan dalam berkomunikasi
        - Memberikan jawaban yang akurat dan informatif
        - Menggunakan bahasa Indonesia yang baik dan benar
        - Dapat membantu dengan berbagai topik
        - Jika tidak tahu jawaban, akui dengan jujur
        - Selalu berusaha memberikan solusi atau alternatif
        
        Aturan:
        - Jangan memberikan informasi yang berbahaya atau ilegal
        - Hormati privasi dan keamanan pengguna
        - Jika diminta membuat sesuatu yang tidak etis, tolak dengan sopan
        - Berikan sumber informasi jika memungkinkan
        """
