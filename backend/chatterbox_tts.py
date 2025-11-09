"""
Chatterbox TTS Integration for AltX Voice Chat
Enhanced text-to-speech with voice cloning capabilities
"""
import os
import tempfile
import asyncio
from pathlib import Path
from typing import Optional, Union
import torch
import torchaudio as ta
from fastapi import HTTPException
import logging

# Configure logging  
logger = logging.getLogger(__name__)

class ChatterboxTTSManager:
    """
    Manager class for Chatterbox TTS with fallback options
    Handles both monolingual and multilingual TTS models
    """
    
    def __init__(self, device: str = "auto"):
        """
        Initialize TTS manager
        
        Args:
            device: Device to run models on ("cuda", "cpu", or "auto")
        """
        self.device = self._get_device(device)
        self.english_model = None
        self.multilingual_model = None
        self.is_initialized = False
        self.sample_rate = 16000  # Default sample rate
        
        # Audio output directory
        self.audio_dir = Path("generated_audio")
        self.audio_dir.mkdir(exist_ok=True)
        
    def _get_device(self, device: str) -> str:
        """Determine the best device to use"""
        if device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device
    
    async def initialize_models(self):
        """Initialize TTS models asynchronously"""
        try:
            # Try to import Chatterbox TTS
            from chatterbox.tts import ChatterboxTTS
            from chatterbox.mtl_tts import ChatterboxMultilingualTTS
            
            logger.info(f"🚀 Initializing Chatterbox TTS models on {self.device}")
            
            # Initialize English model
            try:
                self.english_model = ChatterboxTTS.from_pretrained(device=self.device)
                self.sample_rate = self.english_model.sr
                logger.info("✅ English TTS model loaded successfully")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load English model: {e}")
            
            # Initialize multilingual model
            try:
                self.multilingual_model = ChatterboxMultilingualTTS.from_pretrained(device=self.device)
                logger.info("✅ Multilingual TTS model loaded successfully")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load multilingual model: {e}")
            
            self.is_initialized = True
            logger.info("🎉 Chatterbox TTS initialization complete")
            
        except ImportError as e:
            logger.error(f"❌ Chatterbox TTS not available: {e}")
            logger.info("💡 Install with: pip install chatterbox-tts")
            self.is_initialized = False
            
    async def generate_speech(
        self, 
        text: str, 
        language: str = "en",
        voice_prompt_path: Optional[str] = None,
        output_filename: Optional[str] = None
    ) -> str:
        """
        Generate speech from text using Chatterbox TTS
        
        Args:
            text: Text to synthesize
            language: Language code ("en", "fr", "zh", etc.)
            voice_prompt_path: Optional path to voice cloning sample
            output_filename: Optional custom output filename
            
        Returns:
            Path to generated audio file
        """
        if not self.is_initialized:
            await self.initialize_models()
            
        if not self.is_initialized:
            raise HTTPException(
                status_code=503, 
                detail="TTS service not available. Please install chatterbox-tts."
            )
        
        try:
            # Generate unique filename if not provided
            if not output_filename:
                timestamp = int(asyncio.get_event_loop().time() * 1000)
                output_filename = f"tts_output_{timestamp}.wav"
            
            output_path = self.audio_dir / output_filename
            
            # Choose model based on language
            if language == "en" and self.english_model:
                # Use English model for better quality
                logger.info(f"🎤 Generating English speech: '{text[:50]}...'")
                
                if voice_prompt_path and Path(voice_prompt_path).exists():
                    # Voice cloning with audio prompt
                    wav = self.english_model.generate(text, audio_prompt_path=voice_prompt_path)
                    logger.info("🎭 Generated speech with voice cloning")
                else:
                    # Standard synthesis
                    wav = self.english_model.generate(text)
                    logger.info("🔊 Generated standard English speech")
                
                # Save audio file
                ta.save(str(output_path), wav, self.sample_rate)
                
            elif self.multilingual_model:
                # Use multilingual model
                logger.info(f"🌍 Generating {language} speech: '{text[:50]}...'")
                
                # Map language codes
                lang_map = {
                    "en": "en",
                    "es": "es", 
                    "fr": "fr",
                    "de": "de",
                    "it": "it",
                    "pt": "pt",
                    "ru": "ru",
                    "ja": "ja",
                    "ko": "ko",
                    "zh": "zh",
                    "ar": "ar",
                    "hi": "hi"
                }
                
                lang_id = lang_map.get(language, "en")
                wav = self.multilingual_model.generate(text, language_id=lang_id)
                
                # Save audio file
                ta.save(str(output_path), wav, self.multilingual_model.sr)
                logger.info(f"🎵 Generated {language} speech successfully")
                
            else:
                raise HTTPException(
                    status_code=503,
                    detail="No suitable TTS model available for the requested language"
                )
            
            logger.info(f"💾 Audio saved: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"❌ TTS generation failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate speech: {str(e)}"
            )
    
    async def generate_multilingual_demo(self) -> dict:
        """Generate demo audio files in multiple languages"""
        if not self.is_initialized:
            await self.initialize_models()
            
        demo_texts = {
            "en": "Welcome to AltX! This is our advanced AI assistant that can help you build amazing applications.",
            "es": "¡Bienvenido a AltX! Este es nuestro asistente de IA avanzado que puede ayudarte a construir aplicaciones increíbles.",
            "fr": "Bienvenue sur AltX! Ceci est notre assistant IA avancé qui peut vous aider à créer des applications extraordinaires.",
            "de": "Willkommen bei AltX! Dies ist unser fortschrittlicher KI-Assistent, der Ihnen beim Erstellen erstaunlicher Anwendungen helfen kann.",
            "zh": "欢迎使用AltX！这是我们先进的AI助手，可以帮助您构建令人惊叹的应用程序。",
            "ja": "AltXへようこそ！これは素晴らしいアプリケーションの構築をお手伝いする高度なAIアシスタントです。"
        }
        
        results = {}
        
        for lang, text in demo_texts.items():
            try:
                audio_path = await self.generate_speech(
                    text=text,
                    language=lang,
                    output_filename=f"demo_{lang}.wav"
                )
                results[lang] = {
                    "success": True,
                    "audio_path": audio_path,
                    "text": text
                }
                logger.info(f"✅ Generated demo for {lang}")
                
            except Exception as e:
                results[lang] = {
                    "success": False,
                    "error": str(e),
                    "text": text
                }
                logger.error(f"❌ Failed to generate demo for {lang}: {e}")
        
        return results
    
    async def clone_voice(self, text: str, reference_audio_path: str) -> str:
        """
        Generate speech with voice cloning from reference audio
        
        Args:
            text: Text to synthesize
            reference_audio_path: Path to reference audio for voice cloning
            
        Returns:
            Path to generated audio file
        """
        if not Path(reference_audio_path).exists():
            raise HTTPException(
                status_code=404,
                detail=f"Reference audio file not found: {reference_audio_path}"
            )
        
        return await self.generate_speech(
            text=text,
            language="en",  # Voice cloning currently works best with English model
            voice_prompt_path=reference_audio_path,
            output_filename=f"voice_clone_{int(asyncio.get_event_loop().time() * 1000)}.wav"
        )
    
    def get_supported_languages(self) -> list:
        """Get list of supported languages"""
        if self.multilingual_model:
            return [
                "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh", 
                "ar", "hi", "th", "vi", "id", "ms", "tr", "pl", "nl", "sv", 
                "da", "no", "fi"
            ]
        elif self.english_model:
            return ["en"]
        else:
            return []
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """Clean up old generated audio files"""
        import time
        current_time = time.time()
        
        for audio_file in self.audio_dir.glob("*.wav"):
            file_age = current_time - audio_file.stat().st_mtime
            if file_age > (max_age_hours * 3600):
                try:
                    audio_file.unlink()
                    logger.info(f"🗑️ Cleaned up old file: {audio_file}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to delete {audio_file}: {e}")

# Global TTS manager instance
tts_manager = ChatterboxTTSManager()

# Watermark detection utility
def detect_watermark(audio_path: str) -> float:
    """
    Detect Perth watermark in audio file
    
    Args:
        audio_path: Path to audio file to check
        
    Returns:
        Watermark confidence (0.0 = no watermark, 1.0 = watermarked)
    """
    try:
        import perth
        import librosa
        
        # Load the audio
        watermarked_audio, sr = librosa.load(audio_path, sr=None)
        
        # Initialize watermarker
        watermarker = perth.PerthImplicitWatermarker()
        
        # Extract watermark
        watermark = watermarker.get_watermark(watermarked_audio, sample_rate=sr)
        
        logger.info(f"🔍 Watermark detection for {audio_path}: {watermark}")
        return float(watermark)
        
    except ImportError:
        logger.warning("⚠️ Perth watermark detection not available")
        return 0.0
    except Exception as e:
        logger.error(f"❌ Watermark detection failed: {e}")
        return 0.0

# Example usage function
async def example_usage():
    """Example of how to use the Chatterbox TTS system"""
    
    # Initialize TTS manager
    await tts_manager.initialize_models()
    
    # Generate English speech
    english_audio = await tts_manager.generate_speech(
        text="Ezreal and Jinx teamed up with Ahri, Yasuo, and Teemo to take down the enemy's Nexus in an epic late-game pentakill.",
        language="en"
    )
    print(f"English audio generated: {english_audio}")
    
    # Generate multilingual speech
    if "fr" in tts_manager.get_supported_languages():
        french_audio = await tts_manager.generate_speech(
            text="Bonjour, comment ça va? Ceci est le modèle de synthèse vocale multilingue Chatterbox.",
            language="fr"
        )
        print(f"French audio generated: {french_audio}")
    
    # Generate Chinese speech  
    if "zh" in tts_manager.get_supported_languages():
        chinese_audio = await tts_manager.generate_speech(
            text="你好，今天天气真不错，希望你有一个愉快的周末。",
            language="zh"
        )
        print(f"Chinese audio generated: {chinese_audio}")
    
    # Detect watermarks
    watermark_confidence = detect_watermark(english_audio)
    print(f"Watermark detected: {watermark_confidence}")

if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())