"""
Voice Chat API endpoints for the frontend integration
"""
import os
import json
import tempfile
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, Response
import google.generativeai as genai
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Try to import Google Cloud services
try:
    from google.cloud import speech, texttospeech
    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_AVAILABLE = False
    print("⚠️  Google Cloud services not available - using fallback")

router = APIRouter(prefix="/api", tags=["voice-chat"])

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    conversation_history: List[Dict[str, Any]] = []

class ProjectSpec(BaseModel):
    description: str
    type: str
    features: List[str]
    tech_stack: Dict[str, str]
    target_audience: str

# Initialize Gemini for conversation
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def _ensure_english_response(ai_response: str, user_message: str) -> str:
    """Ensure AI response is in English, not Hindi or other languages"""
    
    # Check for common Hindi/Devanagari characters or Hindi words
    hindi_indicators = ['आप', 'में', 'है', 'को', 'का', 'की', 'से', 'पर', 'ऐप', 'बना', 'क्या', 'कैसे']
    
    # Check if response contains Hindi indicators
    has_hindi = any(indicator in ai_response for indicator in hindi_indicators)
    
    if has_hindi:
        # Force English response
        return "I'm here to help you build your app! Could you tell me more about what you'd like to create? For example, is it a web app, mobile app, or something else?"
    
    return ai_response

def _validate_english_transcript(transcript: str) -> str:
    """Validate and fix transcript to ensure it's English"""
    
    # Check for Hindi/Devanagari characters
    hindi_chars = ['आ', 'इ', 'ई', 'उ', 'ऊ', 'ए', 'ऐ', 'ओ', 'औ', 'क', 'ग', 'च', 'ज', 'ट', 'ड', 'त', 'द', 'न', 'प', 'ब', 'म', 'य', 'र', 'ल', 'व', 'श', 'स', 'ह']
    hindi_words = ['आप', 'में', 'है', 'को', 'का', 'की', 'से', 'पर', 'ऐप', 'बना', 'क्या', 'कैसे', 'हां', 'नहीं']
    
    # Check if transcript contains significant Hindi content
    has_hindi_chars = any(char in transcript for char in hindi_chars)
    has_hindi_words = any(word in transcript for word in hindi_words)
    
    if has_hindi_chars or has_hindi_words:
        # If it's clearly Hindi, return a default English message
        print(f"⚠️ Detected Hindi in transcript: {transcript}")
        return "I want to build an app"
    
    return transcript

conversation_model = genai.GenerativeModel(
    'gemini-2.5-flash',
    system_instruction="""You are a professional software requirements analyst and conversational AI assistant.

CRITICAL LANGUAGE RULE: Always respond in ENGLISH unless the user is clearly speaking another language consistently throughout the conversation. If there's any doubt about the language, default to English. Never switch to Hindi or other languages unless explicitly requested.

YOUR JOB: Gather complete app specifications through natural conversation, then generate projects.

CONVERSATION FLOW:
1. Greet users warmly and ask what they want to build
2. Ask ONE short question at a time to gather:
   - Project type (web app, mobile app, etc.)
   - Main purpose and functionality  
   - Target users/audience
   - Key features (3-5 main ones)
   - Tech stack preferences
   - Design preferences (colors, theme, style - VERY IMPORTANT!)
   - Special requirements

CRITICAL: Always ask about design preferences! Ask questions like:
"What should it look like? Any specific colors, themes, or style preferences?"

3. SMART DEFAULTS: If user says "I don't know", "default", or gives vague answers:
   - Suggest reasonable defaults
   - Say: "I'll assume [default]. We can change this later."
   - Continue to next question

4. Keep responses CONVERSATIONAL and BRIEF (2-3 sentences max)

5. After gathering info, create a summary like:
   "PROJECT SUMMARY:
   📱 Type: [type]
   🎯 Purpose: [purpose] 
   👥 Users: [audience]
   ⭐ Features: [list including design features]
   💻 Tech: [stack]
   🎨 Style: [design colors, theme, visual preferences]
   
   Does this look good? Say 'yes' to generate your app!"
   
MUST include design preferences in BOTH Features and Style sections!

6. If user confirms (says yes/looks good/generate/build), respond:
   "Perfect! Generating your project now..." and set should_generate=true

IMPORTANT RULES:
- Be friendly and enthusiastic
- Ask only ONE question per response
- Keep it conversational, not formal
- Don't overwhelm with too many options
- Make sensible assumptions when user is unsure
- After 5-7 questions, summarize and ask for confirmation"""
)

@router.post("/process-speech")
async def process_speech(audio: UploadFile = File(...)):
    """Process uploaded audio and return transcription"""
    
    if not GOOGLE_CLOUD_AVAILABLE:
        return JSONResponse(
            status_code=200,
            content={
                "error": "Google Cloud Speech not configured. Please use text input instead.", 
                "transcript": None,
                "fallback_message": "Voice recognition unavailable - please type your message"
            }
        )
    
    try:
        # Check if audio file is valid
        content = await audio.read()
        if len(content) < 1000:  # Less than 1KB probably empty
            return {
                "transcript": None, 
                "error": "Audio too short or empty. Please record a longer message."
            }
        
        # Save uploaded audio to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Check if Google Cloud credentials are available
        try:
            client = speech.SpeechClient()
        except Exception as cred_error:
            os.unlink(temp_file_path)
            return JSONResponse(
                status_code=200,
                content={
                    "error": f"Google Cloud authentication error. Please use text input instead.", 
                    "transcript": None,
                    "fallback_message": "Voice recognition needs setup - please type your message"
                }
            )
        
        # Transcribe using Google Cloud Speech with multiple encoding attempts
        with open(temp_file_path, "rb") as audio_file:
            audio_content = audio_file.read()
        
        audio_data = speech.RecognitionAudio(content=audio_content)
        
        # Try different configurations - start with most likely to work
        configs_to_try = [
            # WebM Opus - English primary with limited alternatives (NO Hindi to prevent confusion)
            speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                sample_rate_hertz=48000,
                language_code="en-US",  # Primary language - English ONLY
                alternative_language_codes=["en-GB", "en-AU", "en-CA"],  # Only English variants
                enable_automatic_punctuation=True,
                model="latest_long",
                use_enhanced=True,
                enable_spoken_punctuation=True,
                enable_spoken_emojis=True
            ),
            # WebM Opus with broader language support (fallback only)
            speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                sample_rate_hertz=48000,
                language_code="en-US",
                alternative_language_codes=["es-ES", "fr-FR", "de-DE", "it-IT", "pt-BR", "zh-CN"],  # Removed Hindi
                enable_automatic_punctuation=True
            ),
            # WebM Opus with auto sample rate detection
            speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                language_code="en-US",
                enable_automatic_punctuation=True
            ),
            # OGG Opus fallback - 48kHz
            speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
                sample_rate_hertz=48000,
                language_code="en-US",
                enable_automatic_punctuation=True
            )
        ]
        
        response = None
        successful_config = None
        
        for i, config in enumerate(configs_to_try):
            try:
                print(f"🎤 Trying config {i+1}: {config.encoding.name}, sample_rate: {getattr(config, 'sample_rate_hertz', 'auto')}")
                response = client.recognize(config=config, audio=audio_data)
                if response.results and response.results[0].alternatives:
                    successful_config = config
                    print(f"✅ Success with config {i+1}: {config.encoding.name}")
                    break
                else:
                    print(f"⚠️  Config {i+1} returned empty results")
            except Exception as encoding_error:
                print(f"❌ Config {i+1} failed: {encoding_error}")
                continue
        
        # Clean up temp file
        os.unlink(temp_file_path)
        
        if response and response.results:
            transcript = response.results[0].alternatives[0].transcript.strip()
            if transcript:
                # Validate that transcript is primarily English
                validated_transcript = _validate_english_transcript(transcript)
                return {"transcript": validated_transcript}
        
        return {
            "transcript": None, 
            "error": "Could not understand speech. Please try speaking more clearly or use text input.",
            "suggestions": [
                "Speak closer to the microphone",
                "Ensure you're in a quiet environment", 
                "Try speaking more slowly and clearly",
                "Use the text input as a backup"
            ]
        }
            
    except Exception as e:
        # Clean up temp file if it exists
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        
        print(f"Speech processing error: {e}")
        return JSONResponse(
            status_code=200,  # Don't return 500, return 200 with error message
            content={
                "error": f"Speech recognition temporarily unavailable. Please use text input instead.", 
                "transcript": None,
                "technical_error": str(e),
                "fallback_message": "You can type your message below instead of using voice"
            }
        )

@router.post("/chat")
async def chat_with_ai(chat_data: ChatMessage):
    """Handle conversation with AI assistant"""
    
    try:
        # Build conversation context
        conversation_context = ""
        for msg in chat_data.conversation_history[-10:]:  # Last 10 messages for context
            if msg['type'] == 'user':
                conversation_context += f"User: {msg['content']}\n"
            elif msg['type'] == 'ai':
                conversation_context += f"Assistant: {msg['content']}\n"
        
        # Add current message
        conversation_context += f"User: {chat_data.message}\n"
        
        # Generate response with safety handling
        prompt = f"""Conversation so far:
{conversation_context}

CRITICAL INSTRUCTIONS: 
- ALWAYS respond in English unless the user has explicitly requested another language
- If the transcribed text seems like broken English or poor translation, treat it as English and respond in clear English
- Never respond in Hindi, Urdu, or any Indian language unless explicitly requested
- Keep responses friendly, professional, and focused on gathering app requirements
- Use simple, clear English

Response:"""
        
        response = conversation_model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.8,
                "max_output_tokens": 500
            },
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
        )
        
        # Handle blocked responses
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if hasattr(candidate, 'finish_reason') and candidate.finish_reason != 1:  # 1 = STOP (normal completion)
                ai_response = "I'm here to help you build your app! Could you tell me more about what you'd like to create? For example, is it a web app, mobile app, or something else?"
            else:
                ai_response = response.text if response.text else "I'm ready to help you build your app! What would you like to create?"
        else:
            ai_response = "I'm your AI assistant and I'm ready to help you build amazing projects! What kind of app would you like to create today!"
        
        # Force English response if AI responded in wrong language
        ai_response = _ensure_english_response(ai_response, chat_data.message)
        
        # Check if this is a project confirmation
        should_generate = False
        project_spec = None
        
        # Simple confirmation detection
        user_msg_lower = chat_data.message.lower()
        confirmation_words = ['yes', 'looks good', 'generate', 'build', 'create', 'perfect', 'correct', 'right']
        
        if any(word in user_msg_lower for word in confirmation_words) and "PROJECT SUMMARY:" in conversation_context:
            should_generate = True
            
            # Extract project info from conversation properly
            project_description = ""
            project_type = "web app"
            features = []
            tech_stack = ["React", "FastAPI"]
            
            # Parse the PROJECT SUMMARY from conversation
            try:
                summary_start = conversation_context.find("PROJECT SUMMARY:")
                if summary_start != -1:
                    summary_section = conversation_context[summary_start:summary_start + 1000]
                    
                    # Extract type
                    if "Type:" in summary_section:
                        type_line = summary_section.split("Type:")[1].split("\n")[0].strip()
                        project_type = type_line.replace("📱", "").replace("💻", "").strip()
                    
                    # Extract purpose/description
                    if "Purpose:" in summary_section:
                        purpose_line = summary_section.split("Purpose:")[1].split("\n")[0].strip()
                        project_description = purpose_line.replace("🎯", "").strip()
                    
                    # Extract features from summary
                    if "Features:" in summary_section:
                        features_line = summary_section.split("Features:")[1].split("\n")[0].strip()
                        features = [f.strip() for f in features_line.replace("⭐", "").split(",") if f.strip()]
                    
                    # Also extract design preferences from style section
                    if "Style:" in summary_section:
                        style_line = summary_section.split("Style:")[1].split("\n")[0].strip()
                        style_features = style_line.replace("🎨", "").strip()
                        if style_features:
                            features.append(f"Design: {style_features}")
                    
                    # Extract tech stack
                    if "Tech:" in summary_section:
                        tech_line = summary_section.split("Tech:")[1].split("\n")[0].strip()
                        tech_parts = tech_line.replace("💻", "").split(",")
                        if len(tech_parts) >= 2:
                            tech_stack = [t.strip() for t in tech_parts if t.strip()]
                
                # ENHANCED: Also extract design requirements from entire conversation
                design_keywords = [
                    "black background", "white text", "white font", "white color", 
                    "dark theme", "dark mode", "light theme", "modern design",
                    "minimalist", "colorful", "gradient", "responsive"
                ]
                
                conversation_lower = conversation_context.lower()
                detected_design_features = []
                
                for keyword in design_keywords:
                    if keyword in conversation_lower:
                        detected_design_features.append(keyword)
                
                # Add detected design features to features list
                if detected_design_features:
                    design_feature = f"Design preferences: {', '.join(detected_design_features)}"
                    if design_feature not in features:
                        features.append(design_feature)
                
                print(f"DEBUG: Extracted features: {features}")
                print(f"DEBUG: Detected design features: {detected_design_features}")
                
            except Exception as e:
                print(f"Error parsing project summary: {e}")
            
            project_spec = {
                "description": project_description or "AI-generated application",
                "type": project_type,
                "features": features,
                "tech_stack": tech_stack,
                "conversation_history": chat_data.conversation_history
            }
            
            print(f"DEBUG: Final project_spec being sent: {project_spec}")
        
        return {
            "response": ai_response,
            "should_generate": should_generate,
            "project_spec": project_spec
        }
        
    except Exception as e:
        print(f"Chat AI error: {e}")
        # Return a fallback response instead of throwing an error
        return {
            "response": "I'm here to help you build your app! Could you tell me what kind of project you'd like to create? For example, a website, mobile app, or desktop application?",
            "should_generate": False,
            "project_spec": None
        }

class TextToSpeechRequest(BaseModel):
    text: str

@router.post("/synthesize-speech")
async def synthesize_speech(request: TextToSpeechRequest):
    """Convert text to speech and return audio file"""
    text = request.text
    
    if not GOOGLE_CLOUD_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={"error": "Text-to-speech not available"}
        )
    
    try:
        client = texttospeech.TextToSpeechClient()
        
        # Truncate long text
        if len(text) > 500:
            text = text[:500] + "..."
        
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Neural2-C",
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0
        )
        
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # Save to temp file and return path or base64
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            temp_file.write(response.audio_content)
            temp_file_path = temp_file.name
        
        # Return the file path or base64 encoded audio
        import base64
        with open(temp_file_path, "rb") as audio_file:
            audio_content = audio_file.read()
        
        os.unlink(temp_file_path)
        
        # Return as audio blob
        return Response(
            content=audio_content,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=speech.mp3"}
        )
        
    except Exception as e:
        print(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=f"Text-to-speech failed: {str(e)}")

# Health check endpoint
@router.get("/voice-chat/status")
async def get_voice_chat_status():
    """Get status of voice chat services"""
    
    status = {
        "google_cloud_available": GOOGLE_CLOUD_AVAILABLE,
        "services": {
            "speech_to_text": GOOGLE_CLOUD_AVAILABLE,
            "text_to_speech": GOOGLE_CLOUD_AVAILABLE,
            "ai_chat": bool(os.getenv("GOOGLE_API_KEY"))
        }
    }
    
    return status