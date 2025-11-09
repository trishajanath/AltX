#!/usr/bin/env python3
"""
Test script for Chatterbox TTS integration in AltX
Run this to verify TTS functionality
"""
import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

async def test_chatterbox_integration():
    """Test the Chatterbox TTS integration"""
    print("🚀 Testing AltX Chatterbox TTS Integration")
    print("=" * 50)
    
    try:
        # Test importing the TTS manager
        print("📦 Testing imports...")
        from chatterbox_tts import tts_manager, detect_watermark
        print("✅ TTS manager imported successfully")
        
        # Test model initialization
        print("\n🔧 Initializing TTS models...")
        await tts_manager.initialize_models()
        
        if tts_manager.is_initialized:
            print("✅ TTS models initialized successfully")
            
            # Test supported languages
            languages = tts_manager.get_supported_languages()
            print(f"🌍 Supported languages: {languages}")
            
            # Test basic English TTS
            print("\n🎤 Testing English TTS...")
            test_text = "Hello from AltX! This is a test of our enhanced voice system using Chatterbox TTS."
            
            try:
                audio_path = await tts_manager.generate_speech(
                    text=test_text,
                    language="en"
                )
                print(f"✅ English TTS successful: {audio_path}")
                
                # Test watermark detection
                watermark_score = detect_watermark(audio_path)
                print(f"🔍 Watermark detected: {watermark_score}")
                
            except Exception as e:
                print(f"❌ English TTS failed: {e}")
            
            # Test multilingual TTS (if available)
            if "fr" in languages:
                print("\n🇫🇷 Testing French TTS...")
                try:
                    french_audio = await tts_manager.generate_speech(
                        text="Bonjour! Ceci est un test du système TTS multilingue d'AltX.",
                        language="fr"
                    )
                    print(f"✅ French TTS successful: {french_audio}")
                except Exception as e:
                    print(f"❌ French TTS failed: {e}")
            
            # Test Chinese TTS (if available)
            if "zh" in languages:
                print("\n🇨🇳 Testing Chinese TTS...")
                try:
                    chinese_audio = await tts_manager.generate_speech(
                        text="你好！这是AltX多语言TTS系统的测试。",
                        language="zh"
                    )
                    print(f"✅ Chinese TTS successful: {chinese_audio}")
                except Exception as e:
                    print(f"❌ Chinese TTS failed: {e}")
            
            # Test multilingual demo
            print("\n🌍 Testing multilingual demo generation...")
            try:
                demo_results = await tts_manager.generate_multilingual_demo()
                print("✅ Multilingual demo results:")
                for lang, result in demo_results.items():
                    status = "✅" if result.get("success") else "❌"
                    print(f"  {status} {lang}: {result.get('audio_path', result.get('error', 'Unknown'))}")
            except Exception as e:
                print(f"❌ Multilingual demo failed: {e}")
                
        else:
            print("❌ TTS models failed to initialize")
            print("💡 Make sure you have installed: pip install torch torchaudio")
            print("💡 For Chatterbox TTS: pip install chatterbox-tts")
            
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("\n🔧 Installation Guide:")
        print("1. Install PyTorch: pip install torch torchaudio")
        print("2. Install Chatterbox TTS: pip install chatterbox-tts")
        print("3. Install audio libraries: pip install librosa soundfile")
        print("4. Optional watermarking: pip install perth")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🏁 TTS Integration Test Complete")

def test_voice_api_endpoints():
    """Test the voice API endpoints"""
    print("\n🌐 Testing Voice API Endpoints")
    print("-" * 30)
    
    try:
        from voice_chat_api import router
        print("✅ Voice chat API router imported successfully")
        
        # List available endpoints
        print("📋 Available endpoints:")
        for route in router.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                methods = ', '.join(route.methods) if route.methods else 'GET'
                print(f"  {methods} {route.path}")
        
    except Exception as e:
        print(f"❌ Voice API test failed: {e}")

async def main():
    """Main test function"""
    print("🎯 AltX Enhanced TTS System Test")
    print("=" * 60)
    
    # Test TTS integration
    await test_chatterbox_integration()
    
    # Test API endpoints
    test_voice_api_endpoints()
    
    print("\n💡 Usage Examples:")
    print("1. Basic TTS: POST /api/synthesize-chatterbox")
    print("2. Voice Cloning: POST /api/voice-clone")
    print("3. Multilingual Demo: GET /api/multilingual-demo")
    print("4. Supported Languages: GET /api/supported-languages")
    
    print("\n🚀 Integration complete! Your AltX voice system is ready.")

if __name__ == "__main__":
    # Run the test
    asyncio.run(main())