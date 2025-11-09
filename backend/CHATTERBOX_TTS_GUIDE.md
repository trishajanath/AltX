# AltX Chatterbox TTS Integration Guide

## Overview
AltX now supports advanced text-to-speech capabilities using Chatterbox TTS, including voice cloning and multilingual support with built-in Perth watermarking.

## Features
- ✅ High-quality English TTS
- ✅ Multilingual support (23+ languages)
- ✅ Voice cloning from reference audio
- ✅ Built-in Perth watermarking for responsible AI
- ✅ Fallback to Google Cloud TTS
- ✅ RESTful API endpoints
- ✅ Async processing

## Installation

### 1. Core Dependencies
```bash
pip install torch torchaudio
pip install librosa soundfile
```

### 2. Chatterbox TTS (if available)
```bash
pip install chatterbox-tts
```

### 3. Perth Watermarking (optional)
```bash
pip install perth
```

## API Endpoints

### 1. Enhanced TTS with Chatterbox
```http
POST /api/synthesize-chatterbox
Content-Type: application/json

{
    "text": "Hello from AltX! This is enhanced TTS.",
    "language": "en",
    "voice_prompt_path": "/path/to/reference.wav"  // optional for voice cloning
}
```

**Response:** Audio file (WAV format) with headers:
- `X-Watermark-Score`: Watermark detection confidence
- `X-TTS-Engine`: "Chatterbox"
- `X-Language`: Language used

### 2. Voice Cloning
```http
POST /api/voice-clone
Content-Type: multipart/form-data

text: "Text to synthesize with cloned voice"
reference_audio: [WAV file upload]
```

**Response:** Cloned voice audio file

### 3. Multilingual Demo
```http
GET /api/multilingual-demo
```

Generates demo files in multiple languages and returns paths/status.

### 4. Supported Languages
```http
GET /api/supported-languages
```

Returns available engines and supported language codes.

## Code Examples

### Basic Usage
```python
import asyncio
from chatterbox_tts import tts_manager

async def generate_speech():
    # Initialize
    await tts_manager.initialize_models()
    
    # Generate English speech
    audio_path = await tts_manager.generate_speech(
        text="Ezreal and Jinx teamed up for an epic pentakill!",
        language="en"
    )
    
    print(f"Generated: {audio_path}")

asyncio.run(generate_speech())
```

### Voice Cloning
```python
async def clone_voice():
    cloned_audio = await tts_manager.clone_voice(
        text="This will sound like the reference voice",
        reference_audio_path="reference_voice.wav"
    )
    print(f"Cloned voice: {cloned_audio}")
```

### Multilingual TTS
```python
async def multilingual_example():
    # French
    french_audio = await tts_manager.generate_speech(
        text="Bonjour, comment ça va?",
        language="fr"
    )
    
    # Chinese
    chinese_audio = await tts_manager.generate_speech(
        text="你好，今天天气真不错。",
        language="zh"
    )
```

### Watermark Detection
```python
from chatterbox_tts import detect_watermark

# Check if audio has Perth watermark
score = detect_watermark("generated_audio.wav")
print(f"Watermark confidence: {score}")  # 0.0 = no watermark, 1.0 = watermarked
```

## Frontend Integration

### JavaScript/React Example
```javascript
// Enhanced TTS request
const generateSpeech = async (text, language = 'en') => {
    const response = await fetch('/api/synthesize-chatterbox', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            text: text,
            language: language
        })
    });
    
    if (response.ok) {
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        
        // Play the audio
        const audio = new Audio(audioUrl);
        audio.play();
        
        // Check watermark
        const watermarkScore = response.headers.get('X-Watermark-Score');
        console.log('Watermark detected:', watermarkScore);
    }
};

// Voice cloning
const cloneVoice = async (text, referenceAudioFile) => {
    const formData = new FormData();
    formData.append('text', text);
    formData.append('reference_audio', referenceAudioFile);
    
    const response = await fetch('/api/voice-clone', {
        method: 'POST',
        body: formData
    });
    
    if (response.ok) {
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        audio.play();
    }
};
```

## Supported Languages

### Chatterbox Multilingual Model
- English (en)
- Spanish (es)
- French (fr)
- German (de)
- Italian (it)
- Portuguese (pt)
- Russian (ru)
- Japanese (ja)
- Korean (ko)
- Chinese (zh)
- Arabic (ar)
- Hindi (hi)
- Thai (th)
- Vietnamese (vi)
- Indonesian (id)
- Malaysian (ms)
- Turkish (tr)
- Polish (pl)
- Dutch (nl)
- Swedish (sv)
- Danish (da)
- Norwegian (no)
- Finnish (fi)

## Error Handling

The system includes comprehensive fallbacks:

1. **Chatterbox TTS unavailable** → Falls back to Google Cloud TTS
2. **Google Cloud TTS unavailable** → Returns error with installation instructions
3. **Model loading fails** → Graceful degradation with error messages
4. **Invalid audio format** → Format conversion attempts
5. **Language not supported** → Falls back to English

## Performance Considerations

- **Model Loading**: Models are loaded lazily on first use
- **Caching**: Generated audio files are cached temporarily
- **Cleanup**: Old files are automatically cleaned up
- **Memory Management**: Models use optimal device selection (CUDA/CPU)

## Testing

Run the test script to verify installation:

```bash
cd backend
python test_chatterbox_tts.py
```

This will test:
- Model initialization
- Basic TTS generation
- Multilingual support
- Voice cloning capabilities
- API endpoint availability
- Watermark detection

## Responsible AI

All audio generated by Chatterbox includes Perth watermarking:
- Imperceptible to humans
- Survives MP3 compression and editing
- Nearly 100% detection accuracy
- Enables tracking of AI-generated content

## Troubleshooting

### Common Issues

1. **"Module not found: chatterbox"**
   ```bash
   pip install chatterbox-tts
   ```

2. **CUDA out of memory**
   - Use CPU device: `ChatterboxTTSManager(device="cpu")`
   - Reduce batch size or text length

3. **Poor audio quality**
   - Check input text formatting
   - Ensure reference audio is high quality (for cloning)
   - Verify language code is correct

4. **Watermark not detected**
   - Install Perth: `pip install perth`
   - Ensure audio hasn't been heavily processed

### Support
For issues with Chatterbox TTS, refer to:
- Chatterbox documentation
- Perth watermarking documentation
- AltX voice chat API logs

---

🎉 **Your AltX application now has advanced voice capabilities!**