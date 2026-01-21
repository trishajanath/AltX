"""
Voice Chat API endpoints for the frontend integration
"""
import os
import json
import tempfile
import asyncio
import time
import base64
import io
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse, Response
import google.generativeai as genai
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Try to import PDF processing
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("⚠️  PyPDF2 not available - PDF text extraction disabled")

# Try to import image processing
try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    print("⚠️  Pillow not available - image processing disabled")

# Try to import Google Cloud services
try:
    from google.cloud import speech, texttospeech
    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_AVAILABLE = False
    print("⚠️  Google Cloud services not available - using fallback")

# Import Chatterbox TTS integration
try:
    from chatterbox_tts import tts_manager, detect_watermark
    CHATTERBOX_AVAILABLE = True
    print("✅ Chatterbox TTS integration available")
except ImportError:
    CHATTERBOX_AVAILABLE = False
    print("⚠️  Chatterbox TTS not available - install with: pip install chatterbox-tts")

router = APIRouter(prefix="/api", tags=["voice-chat"])

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    conversation_history: List[Dict[str, Any]] = []

class ChatMessageWithDocs(BaseModel):
    """Chat message that may include extracted documentation context"""
    message: str
    conversation_history: List[Dict[str, Any]] = []
    documentation_context: Optional[str] = None  # Extracted text from uploaded files

class ProjectSpec(BaseModel):
    description: str
    type: str
    features: List[str]
    tech_stack: Dict[str, str]
    target_audience: str

# Helper functions for file processing
def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text content from a PDF file."""
    if not PDF_AVAILABLE:
        return "[PDF processing not available - please describe your requirements in text]"
    
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text_content = []
        
        for page_num, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            if page_text:
                text_content.append(f"--- Page {page_num + 1} ---\n{page_text}")
        
        extracted_text = "\n\n".join(text_content)
        
        # Limit text length to prevent token overflow
        max_chars = 15000
        if len(extracted_text) > max_chars:
            extracted_text = extracted_text[:max_chars] + f"\n\n[... Document truncated. Showing first {max_chars} characters of {len(extracted_text)} total ...]"
        
        return extracted_text if extracted_text else "[PDF contained no extractable text]"
    except Exception as e:
        print(f"❌ PDF extraction error: {e}")
        return f"[Error extracting PDF content: {str(e)}]"

def describe_image_with_gemini(image_content: bytes, mime_type: str) -> str:
    """Use Gemini to describe/analyze an uploaded image for context."""
    try:
        # Use Gemini vision model to describe the image
        vision_model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Create image part for Gemini
        image_part = {
            "mime_type": mime_type,
            "data": base64.b64encode(image_content).decode('utf-8')
        }
        
        prompt = """Analyze this image and extract any useful information for building a software application. 
Look for:
1. UI/UX design mockups or wireframes
2. Text content, labels, or descriptions
3. Color schemes, themes, or branding
4. Layout structure and components
5. Any specifications or requirements shown

Provide a detailed description that would help an AI generate code for a similar application."""

        response = vision_model.generate_content([prompt, image_part])
        
        if response.text:
            return f"[Image Analysis]\n{response.text}"
        else:
            return "[Could not analyze image content]"
    except Exception as e:
        print(f"❌ Image analysis error: {e}")
        return f"[Error analyzing image: {str(e)}]"

async def process_uploaded_files(files: List[UploadFile]) -> str:
    """Process uploaded files and extract documentation context."""
    if not files:
        return ""
    
    documentation_parts = []
    
    for file in files:
        try:
            content = await file.read()
            filename = file.filename or "unnamed_file"
            content_type = file.content_type or ""
            
            print(f"📄 Processing uploaded file: {filename} ({content_type}, {len(content)} bytes)")
            
            if content_type == "application/pdf" or filename.lower().endswith('.pdf'):
                # Extract text from PDF
                extracted = extract_text_from_pdf(content)
                documentation_parts.append(f"\n📄 **Document: {filename}**\n{extracted}")
                
            elif content_type.startswith("image/"):
                # Analyze image with Gemini vision
                extracted = describe_image_with_gemini(content, content_type)
                documentation_parts.append(f"\n🖼️ **Image: {filename}**\n{extracted}")
                
            else:
                # Try to read as text
                try:
                    text_content = content.decode('utf-8')
                    if len(text_content) > 10000:
                        text_content = text_content[:10000] + "\n[... content truncated ...]"
                    documentation_parts.append(f"\n📝 **File: {filename}**\n{text_content}")
                except:
                    documentation_parts.append(f"\n📎 **File: {filename}** [Binary file - content not extractable]")
                    
        except Exception as e:
            print(f"❌ Error processing file {file.filename}: {e}")
            documentation_parts.append(f"\n❌ **File: {file.filename}** [Error: {str(e)}]")
    
    if documentation_parts:
        return "\n\n=== USER PROVIDED DOCUMENTATION ===\n" + "\n".join(documentation_parts) + "\n=== END DOCUMENTATION ===\n"
    
    return ""

# Store documentation context for project generation (keyed by session/user)
_documentation_context_store: Dict[str, str] = {}

def store_documentation_context(session_id: str, context: str):
    """Store documentation context for later use in project generation."""
    if context:
        _documentation_context_store[session_id] = context
        print(f"📚 Stored documentation context for session {session_id} ({len(context)} chars)")

def get_documentation_context(session_id: str) -> Optional[str]:
    """Retrieve stored documentation context."""
    return _documentation_context_store.get(session_id)

def clear_documentation_context(session_id: str):
    """Clear documentation context after project generation."""
    if session_id in _documentation_context_store:
        del _documentation_context_store[session_id]
        print(f"🧹 Cleared documentation context for session {session_id}")

# Initialize Gemini for conversation
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("❌ WARNING: GOOGLE_API_KEY environment variable not set!")
    print("   Voice chat will not work without a valid API key.")
else:
    print(f"✅ Gemini API key configured (length: {len(GOOGLE_API_KEY)})")
    
genai.configure(api_key=GOOGLE_API_KEY)

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

🚨 CRITICAL: DO NOT ASK REDUNDANT QUESTIONS! 
If the user already provided information in their message, DO NOT ask about it again.
Extract all information from what they've already said before asking new questions.

INFORMATION TO GATHER (only ask if NOT already provided):
- Project type (web app, mobile app, etc.)
- Main purpose/functionality (what it does)
- Key features (3-5 main ones)
- Tech stack preferences (default: React + FastAPI)
- Design preferences (colors, theme, style)

CONVERSATION FLOW:
1. When user gives initial description, EXTRACT ALL INFO from it first!
   Example: "e-commerce for groceries, black background, white text, product search, cart, login"
   → You already have: purpose (grocery e-commerce), features (search, cart, login), design (black bg, white text)
   → Only ask about what's MISSING (maybe just tech stack)

2. Ask ONE short question at a time ONLY for missing information

3. SMART DEFAULTS: If user says "I don't know", "default", "nope", or similar:
   - Use sensible defaults, don't ask again
   - Tech stack default: React + FastAPI
   - Say: "I'll use React for frontend and FastAPI for backend - our recommended stack!"

4. After 2-4 exchanges (or when you have all info), create PROJECT SUMMARY:

   "PROJECT SUMMARY:
   
   Application Type: [type]
   Purpose: [purpose from their description]
   Key Features: [all features they mentioned + design features]
   Technology Stack: [stack]
   Design Style: [colors and theme they specified]
   
   Please confirm these specifications are correct. Reply 'yes' to proceed with generation."

5. If user confirms (yes/looks good/generate), respond:
   "Perfect! Generating your project now..." and set should_generate=true

🚨 NEVER DO THIS:
- Ask "What's the main purpose?" if they already described it
- Ask "What features?" if they listed features already  
- Ask about colors if they already said "black background, white text"
- Keep asking the same question differently
- Ask more than 4-5 total questions

MUST include ALL user-specified design preferences (colors, theme) in the summary!"""
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
        
        # Check audio size - WebM audio is roughly 10KB/second at typical bitrates
        # 60 seconds * 10KB = ~600KB, but we'll be conservative and check duration
        audio_size_kb = len(audio_content) / 1024
        estimated_duration_seconds = audio_size_kb / 8  # Conservative estimate: ~8KB/second for WebM Opus
        
        if estimated_duration_seconds > 55:  # Give 5 second buffer before 60s limit
            os.unlink(temp_file_path)
            return JSONResponse(
                status_code=200,
                content={
                    "error": f"Audio recording too long (~{int(estimated_duration_seconds)} seconds). Google Speech API limit is 60 seconds for real-time processing.",
                    "transcript": None,
                    "suggestions": [
                        "Try recording a shorter message (under 50 seconds)",
                        "Break your message into smaller parts",
                        "Use text input for longer messages"
                    ]
                }
            )
        
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
        audio_too_long_error = False
        
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
                error_str = str(encoding_error)
                print(f"❌ Config {i+1} failed: {error_str}")
                # Check if this is the "audio too long" error
                if "Sync input too long" in error_str or "LongRunningRecognize" in error_str:
                    audio_too_long_error = True
                    break  # No point trying other configs for length issues
                continue
        
        # Clean up temp file
        os.unlink(temp_file_path)
        
        # Handle audio too long error specifically
        if audio_too_long_error:
            return JSONResponse(
                status_code=200,
                content={
                    "error": "Audio recording exceeds 60 second limit. Please record a shorter message.",
                    "transcript": None,
                    "suggestions": [
                        "Keep your recording under 50 seconds",
                        "Break longer messages into multiple recordings",
                        "Use text input for detailed descriptions"
                    ]
                }
            )
        
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

@router.post("/chat-with-files")
async def chat_with_ai_and_files(
    message: str = Form(default=""),
    conversation_history: str = Form(default="[]"),
    files: Optional[List[UploadFile]] = File(default=None)
):
    """Handle conversation with AI assistant, including file uploads for documentation.
    
    This endpoint accepts multipart form data with optional file attachments.
    Files (images, PDFs) will be processed and their content used as context
    for the AI to generate better applications.
    """
    print(f"📨 Received chat-with-files request: message='{message[:100]}...', files={files}")
    try:
        # Handle missing or empty message
        if not message or message.strip() == "":
            return {
                "response": "I didn't receive your message. Could you please try again?",
                "should_generate": False,
                "project_spec": None,
                "has_documentation": False
            }
        
        # Ensure files is a list
        if files is None:
            files = []
            
        # Parse conversation history from JSON string
        try:
            history = json.loads(conversation_history)
        except json.JSONDecodeError:
            history = []
        
        # Process any uploaded files
        documentation_context = ""
        if files and len(files) > 0:
            # Filter out empty file uploads
            actual_files = [f for f in files if f and f.filename and f.size and f.size > 0]
            if actual_files:
                print(f"📎 Processing {len(actual_files)} uploaded files for chat context")
                try:
                    documentation_context = await process_uploaded_files(actual_files)
                except Exception as file_err:
                    print(f"⚠️ Error processing files: {file_err}")
                    documentation_context = ""
                
                # Store context for project generation
                # Use a simple session ID based on conversation length for now
                session_id = f"chat_{len(history)}_{hash(message)}"
                store_documentation_context(session_id, documentation_context)
        
        # Build conversation context
        conversation_context = ""
        for msg in history[-10:]:  # Last 10 messages for context
            if msg.get('type') == 'user':
                conversation_context += f"User: {msg.get('content', '')}\n"
            elif msg.get('type') == 'ai':
                conversation_context += f"Assistant: {msg.get('content', '')}\n"
        
        # Add documentation context if available
        if documentation_context:
            conversation_context = documentation_context + "\n\n" + conversation_context
            print(f"📚 Added {len(documentation_context)} chars of documentation context")
        
        # Add current message
        conversation_context += f"User: {message}\n"
        
        # Check if we have enough info for a summary
        conv_lower = conversation_context.lower()
        
        # Check for project type/purpose
        has_project_type = any(keyword in conv_lower for keyword in [
            'grocery', 'e-commerce', 'ecommerce', 'shopping', 'store', 'app', 'website', 
            'mobile', 'web app', 'application', 'dashboard', 'portfolio', 'blog',
            'tracker', 'management', 'booking', 'delivery', 'social'
        ])
        
        # Check for tech stack (or user said they don't care / confirmed default)
        has_tech_stack = any(keyword in conv_lower for keyword in [
            'react', 'fastapi', 'javascript', 'python', 'node', 'vue', 'angular',
            'recommended stack', "i'll use react"
        ]) or ('yup' in message.lower() or 'yes' in message.lower() or 'yeah' in message.lower())
        
        # Check for design preferences  
        has_design_prefs = any(keyword in conv_lower for keyword in [
            'black', 'white', 'dark', 'light', 'color', 'theme', 'style', 'design',
            'modern', 'minimal', 'clean', 'professional', 'background'
        ])
        
        # Check for features
        has_features = any(keyword in conv_lower for keyword in [
            'cart', 'login', 'signup', 'search', 'product', 'checkout', 'review',
            'payment', 'profile', 'list', 'filter', 'category', 'order'
        ])
        
        # User said they have no more requirements
        user_done = any(word in message.lower() for word in ['nope', 'no more', 'that\'s it', 'nothing else', 'that is it'])
        
        # Create summary if we have core info and user indicated they're done
        should_create_summary = has_project_type and has_features and has_design_prefs and (user_done or has_tech_stack)
        
        print(f"DEBUG Summary Check: type={has_project_type}, features={has_features}, design={has_design_prefs}, tech={has_tech_stack}, done={user_done}")
        print(f"DEBUG Should create summary: {should_create_summary}")
        print(f"DEBUG Has documentation: {len(documentation_context) > 0}")
        
        # Build enhanced prompt with documentation awareness
        doc_instruction = ""
        if documentation_context:
            doc_instruction = """

IMPORTANT: The user has provided documentation (PDFs, images, or text files) as reference material.
Use this documentation to:
1. Understand the specific features, UI designs, or requirements they want
2. Extract any color schemes, branding, or design patterns from images
3. Reference specific pages or sections from PDFs when discussing features
4. Incorporate exact terminology and requirements from the documentation

When you create the PROJECT SUMMARY, include features and designs based on the provided documentation.
"""
        
        summary_instruction = """
        
🚨 CRITICAL: You have ALL the information needed. Create a PROJECT SUMMARY NOW!

Based on the conversation, the user has provided:
- Project type/purpose
- Features they want
- Design preferences (colors/theme)
- Tech stack (or confirmed default)

DO NOT ask any more questions. Create a summary in this EXACT format:

"PROJECT SUMMARY:

Application Type: [extract from conversation - e.g., "Web Application"]
Purpose: [extract main purpose - e.g., "E-commerce grocery store for busy professionals"] 
Key Features: [list ALL features mentioned: product search, listings, shopping cart, login, sign up, customer reviews, etc.]
Technology Stack: React (frontend), FastAPI (backend)
Design Style: [EXACT design they specified - e.g., "Black background with white text, modern design"]

Please confirm these specifications are correct. Reply 'yes' to proceed with generation."

IMPORTANT: Include their EXACT color preferences (black background, white text) in the Design Style!
""" if should_create_summary else ""
        
        prompt = f"""Conversation so far:
{conversation_context}

CRITICAL INSTRUCTIONS: 
- ALWAYS respond in English unless the user has explicitly requested another language
- If the transcribed text seems like broken English or poor translation, treat it as English and respond in clear English
- Never respond in Hindi, Urdu, or any Indian language unless explicitly requested
- Keep responses friendly, professional, and focused on gathering app requirements
- Use simple, clear English{doc_instruction}{summary_instruction}

Response:"""
        
        response = conversation_model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.8,
                "max_output_tokens": 2048
            },
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
        )
        
        # Extract AI response
        ai_response = ""
        if response.candidates and len(response.candidates) > 0:
            try:
                ai_response = response.text if response.text else "I'm ready to help you build your app! What would you like to create?"
            except Exception as e:
                print(f"⚠️ Error accessing response.text: {e}")
                ai_response = "I'm ready to help you build your app! What would you like to create?"
        else:
            ai_response = "I'm your AI assistant and I'm ready to help you build amazing projects! What kind of app would you like to create today!"
        
        # Force English response
        ai_response = _ensure_english_response(ai_response, message)
        
        # Check if this is a project confirmation
        should_generate = False
        project_spec = None
        
        user_msg_lower = message.lower()
        confirmation_words = ['yes', 'looks good', 'generate', 'build it', 'create it', 'perfect', 'correct', 'sounds good']
        has_project_summary = "PROJECT SUMMARY:" in conversation_context
        is_confirmation = any(word in user_msg_lower for word in confirmation_words)
        
        if is_confirmation and has_project_summary:
            should_generate = True
            
            project_description = ""
            project_type = "web app"
            features = []
            tech_stack = ["React", "FastAPI"]
            
            # Parse the PROJECT SUMMARY
            try:
                summary_start = conversation_context.find("PROJECT SUMMARY:")
                if summary_start != -1:
                    summary_section = conversation_context[summary_start:summary_start + 1000]
                    
                    if "Type:" in summary_section:
                        type_line = summary_section.split("Type:")[1].split("\n")[0].strip()
                        project_type = type_line.replace("📱", "").replace("💻", "").strip()
                    
                    if "Purpose:" in summary_section:
                        purpose_line = summary_section.split("Purpose:")[1].split("\n")[0].strip()
                        project_description = purpose_line.replace("🎯", "").strip()
                    
                    if "Features:" in summary_section:
                        features_line = summary_section.split("Features:")[1].split("\n")[0].strip()
                        features = [f.strip() for f in features_line.replace("⭐", "").split(",") if f.strip()]
                    
                    if "Style:" in summary_section:
                        style_line = summary_section.split("Style:")[1].split("\n")[0].strip()
                        style_features = style_line.replace("🎨", "").strip()
                        if style_features:
                            features.append(f"Design: {style_features}")
                    
                    if "Tech:" in summary_section:
                        tech_line = summary_section.split("Tech:")[1].split("\n")[0].strip()
                        tech_parts = tech_line.replace("💻", "").split(",")
                        if len(tech_parts) >= 2:
                            tech_stack = [t.strip() for t in tech_parts if t.strip()]
            except Exception as e:
                print(f"Error parsing project summary: {e}")
            
            project_spec = {
                "description": project_description or "AI-generated application",
                "type": project_type,
                "features": features,
                "tech_stack": tech_stack,
                "conversation_history": history,
                "documentation_context": documentation_context if documentation_context else None
            }
            
            print(f"DEBUG: Final project_spec with docs: {bool(documentation_context)}")
        
        return {
            "response": ai_response,
            "should_generate": should_generate,
            "project_spec": project_spec,
            "has_documentation": len(documentation_context) > 0
        }
        
    except Exception as e:
        print(f"❌ Chat with files error: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return {
            "response": "I'm having a technical issue. Could you try again?",
            "should_generate": False,
            "project_spec": None
        }

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
        
        # Check if we have enough info for a summary
        conv_lower = conversation_context.lower()
        msg_lower = chat_data.message.lower()
        
        # Check for project type/purpose
        has_project_type = any(keyword in conv_lower for keyword in [
            'grocery', 'e-commerce', 'ecommerce', 'shopping', 'store', 'app', 'website', 
            'mobile', 'web app', 'application', 'dashboard', 'portfolio', 'blog',
            'tracker', 'management', 'booking', 'delivery', 'social'
        ])
        
        # Check for tech stack (or user confirmed default)
        has_tech_stack = any(keyword in conv_lower for keyword in [
            'react', 'fastapi', 'javascript', 'python', 'node', 'vue', 'angular',
            'recommended stack', "i'll use react"
        ]) or ('yup' in msg_lower or 'yes' in msg_lower or 'yeah' in msg_lower)
        
        # Check for design preferences  
        has_design_prefs = any(keyword in conv_lower for keyword in [
            'black', 'white', 'dark', 'light', 'color', 'theme', 'style', 'design',
            'modern', 'minimal', 'clean', 'professional', 'background'
        ])
        
        # Check for features
        has_features = any(keyword in conv_lower for keyword in [
            'cart', 'login', 'signup', 'search', 'product', 'checkout', 'review',
            'payment', 'profile', 'list', 'filter', 'category', 'order'
        ])
        
        # User said they have no more requirements
        user_done = any(word in msg_lower for word in ['nope', 'no more', 'that\'s it', 'nothing else', 'that is it'])
        
        should_create_summary = has_project_type and has_features and has_design_prefs and (user_done or has_tech_stack)
        
        print(f"DEBUG Summary Check: type={has_project_type}, features={has_features}, design={has_design_prefs}, tech={has_tech_stack}, done={user_done}")
        print(f"DEBUG Should create summary: {should_create_summary}")
        
        # Generate response with safety handling
        summary_instruction = """
        
🚨 CRITICAL: You have ALL the information needed. Create a PROJECT SUMMARY NOW!

Based on the conversation, the user has provided:
- Project type/purpose
- Features they want
- Design preferences (colors/theme)
- Tech stack (or confirmed default)

DO NOT ask any more questions. Create a summary in this EXACT format:

"PROJECT SUMMARY:

Application Type: [extract from conversation - e.g., "Web Application"]
Purpose: [extract main purpose - e.g., "E-commerce grocery store for busy professionals"] 
Key Features: [list ALL features mentioned: product search, listings, shopping cart, login, sign up, customer reviews, etc.]
Technology Stack: React (frontend), FastAPI (backend)
Design Style: [EXACT design they specified - e.g., "Black background with white text, modern design"]

Please confirm these specifications are correct. Reply 'yes' to proceed with generation."

IMPORTANT: Include their EXACT color preferences (black background, white text) in the Design Style!
""" if should_create_summary else ""
        
        prompt = f"""Conversation so far:
{conversation_context}

CRITICAL INSTRUCTIONS: 
- ALWAYS respond in English unless the user has explicitly requested another language
- If the transcribed text seems like broken English or poor translation, treat it as English and respond in clear English
- Never respond in Hindi, Urdu, or any Indian language unless explicitly requested
- Keep responses friendly, professional, and focused on gathering app requirements
- Use simple, clear English{summary_instruction}

Response:"""
        
        response = conversation_model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.8,
                "max_output_tokens": 2048  # Increased from 500 to allow complete responses
            },
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
        )
        
        # Handle blocked responses with debugging
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            finish_reason = getattr(candidate, 'finish_reason', None)
            print(f"DEBUG: AI response finish_reason: {finish_reason}")
            
            if finish_reason is not None and finish_reason != 1:  # 1 = STOP (normal completion)
                if finish_reason == 2:  # MAX_TOKENS - response was truncated
                    print(f"⚠️ AI response hit max tokens limit, using partial response")
                    # Use partial text if available
                    try:
                        partial_text = response.text if hasattr(response, 'text') else None
                        if partial_text:
                            print(f"DEBUG: Using truncated response: {partial_text[:100]}")
                            ai_response = partial_text
                        else:
                            ai_response = "Got it! What else would you like to add to your project?"
                    except Exception as e:
                        print(f"DEBUG: Could not access response text: {e}")
                        ai_response = "Got it! What else would you like to add to your project?"
                else:
                    # Other blocking reasons (safety, etc.)
                    print(f"⚠️ AI response blocked/incomplete, finish_reason: {finish_reason}")
                # Check if there's any partial text
                try:
                    partial_text = response.text if hasattr(response, 'text') else None
                    if partial_text:
                        print(f"DEBUG: Partial text available: {partial_text[:100]}")
                        ai_response = partial_text
                    else:
                        ai_response = "Got it! What else would you like to add to your project?"
                except Exception as e:
                    print(f"DEBUG: Could not access response text: {e}")
                    ai_response = "Got it! What else would you like to add to your project?"
            else:
                # Normal completion
                try:
                    ai_response = response.text if response.text else "I'm ready to help you build your app! What would you like to create?"
                    print(f"✅ AI response text: {ai_response[:100]}")
                except Exception as e:
                    print(f"⚠️ Error accessing response.text: {e}")
                    ai_response = "I'm ready to help you build your app! What would you like to create?"
        else:
            print("DEBUG: No candidates in AI response")
            ai_response = "I'm your AI assistant and I'm ready to help you build amazing projects! What kind of app would you like to create today!"
        
        # Force English response if AI responded in wrong language
        ai_response = _ensure_english_response(ai_response, chat_data.message)
        
        # Check if this is a project confirmation
        should_generate = False
        project_spec = None
        
        # Simple confirmation detection - only for project generation
        user_msg_lower = chat_data.message.lower()
        confirmation_words = ['yes', 'looks good', 'generate', 'build it', 'create it', 'perfect', 'correct', 'sounds good']
        
        # Only trigger generation if there's a PROJECT SUMMARY and a clear confirmation
        has_project_summary = "PROJECT SUMMARY:" in conversation_context
        is_confirmation = any(word in user_msg_lower for word in confirmation_words)
        
        print(f"DEBUG: User message: '{chat_data.message}'")
        print(f"DEBUG: Has project summary: {has_project_summary}")
        print(f"DEBUG: Is confirmation: {is_confirmation}")
        
        if is_confirmation and has_project_summary:
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
        print(f"❌ Chat AI error: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        
        # Check for specific error types and provide better feedback
        error_str = str(e).lower()
        
        if "api key" in error_str or "authentication" in error_str:
            response_text = "I'm having trouble connecting to my AI service. Please check that your API key is properly configured."
        elif "rate limit" in error_str or "quota" in error_str:
            response_text = "I'm getting too many requests right now. Please wait a moment and try again."
        elif "network" in error_str or "connection" in error_str:
            response_text = "I'm having network issues. Please check your internet connection and try again."
        else:
            # Generic fallback with more helpful message
            response_text = "I'm having a technical issue understanding that. Could you try rephrasing or saying it again?"
        
        print(f"🔄 Returning error response: {response_text}")
        
        return {
            "response": response_text,
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
            content={"error": "Text-to-speech not available - Google Cloud SDK not installed"}
        )
    
    try:
        # Check if Google Cloud credentials are configured
        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            print("⚠️  GOOGLE_APPLICATION_CREDENTIALS not set, TTS unavailable")
            return JSONResponse(
                status_code=503,
                content={"error": "Text-to-speech credentials not configured"}
            )
        
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
            speaking_rate=1.3
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
        
        # Return as audio blob (CORS handled by middleware)
        response = Response(
            content=audio_content,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=speech.mp3"
            }
        )
        return response
        
    except Exception as e:
        print(f"❌ TTS error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Text-to-speech failed: {str(e)}")

# Enhanced TTS with Chatterbox integration
class ChatterboxTTSRequest(BaseModel):
    text: str
    language: str = "en"
    voice_prompt_path: Optional[str] = None

@router.post("/synthesize-chatterbox")
async def synthesize_chatterbox_speech(request: ChatterboxTTSRequest):
    """Convert text to speech using Chatterbox TTS with advanced features"""
    
    if not CHATTERBOX_AVAILABLE:
        # Fallback to Google Cloud TTS if available
        if GOOGLE_CLOUD_AVAILABLE:
            fallback_request = TextToSpeechRequest(text=request.text)
            return await synthesize_speech(fallback_request)
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Advanced TTS not available", 
                    "message": "Please install chatterbox-tts for enhanced voice synthesis",
                    "fallback": "Using basic TTS"
                }
            )
    
    try:
        # Initialize TTS manager if needed
        if not tts_manager.is_initialized:
            await tts_manager.initialize_models()
        
        # Generate speech with Chatterbox
        audio_path = await tts_manager.generate_speech(
            text=request.text,
            language=request.language,
            voice_prompt_path=request.voice_prompt_path
        )
        
        # Read the generated audio file
        audio_file_path = Path(audio_path)
        if not audio_file_path.exists():
            raise HTTPException(status_code=500, detail="Generated audio file not found")
        
        # Return audio file
        with open(audio_file_path, "rb") as audio_file:
            audio_content = audio_file.read()
        
        # Detect watermark
        watermark_score = detect_watermark(str(audio_file_path))
        
        return Response(
            content=audio_content,
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"inline; filename=chatterbox_tts_{int(time.time() * 1000)}.wav",
                "X-Watermark-Score": str(watermark_score),
                "X-TTS-Engine": "Chatterbox",
                "X-Language": request.language
            }
        )
        
    except Exception as e:
        print(f"Chatterbox TTS error: {e}")
        
        # Try fallback to Google Cloud TTS
        if GOOGLE_CLOUD_AVAILABLE and request.language == "en":
            try:
                fallback_request = TextToSpeechRequest(text=request.text)
                return await synthesize_speech(fallback_request)
            except:
                pass
        
        raise HTTPException(
            status_code=500, 
            detail=f"Enhanced TTS failed: {str(e)}"
        )

@router.post("/voice-clone")
async def clone_voice(
    text: str,
    reference_audio: UploadFile = File(...)
):
    """Generate speech with voice cloning from uploaded reference audio"""
    
    if not CHATTERBOX_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={
                "error": "Voice cloning not available",
                "message": "Please install chatterbox-tts for voice cloning features"
            }
        )
    
    try:
        # Save uploaded reference audio
        reference_content = await reference_audio.read()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_ref:
            temp_ref.write(reference_content)
            temp_ref_path = temp_ref.name
        
        # Initialize TTS manager if needed
        if not tts_manager.is_initialized:
            await tts_manager.initialize_models()
        
        # Generate cloned speech
        cloned_audio_path = await tts_manager.clone_voice(
            text=text,
            reference_audio_path=temp_ref_path
        )
        
        # Clean up reference file
        os.unlink(temp_ref_path)
        
        # Return cloned audio
        with open(cloned_audio_path, "rb") as audio_file:
            audio_content = audio_file.read()
        
        return Response(
            content=audio_content,
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"inline; filename=voice_clone_{int(time.time() * 1000)}.wav",
                "X-TTS-Engine": "Chatterbox-Clone",
                "X-Clone-Quality": "High"
            }
        )
        
    except Exception as e:
        # Clean up temp file if it exists
        if 'temp_ref_path' in locals() and os.path.exists(temp_ref_path):
            os.unlink(temp_ref_path)
        
        print(f"Voice cloning error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Voice cloning failed: {str(e)}"
        )

@router.get("/multilingual-demo")
async def generate_multilingual_demo():
    """Generate demo audio files in multiple languages"""
    
    if not CHATTERBOX_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={
                "error": "Multilingual TTS not available",
                "message": "Please install chatterbox-tts for multilingual features"
            }
        )
    
    try:
        # Initialize TTS manager if needed
        if not tts_manager.is_initialized:
            await tts_manager.initialize_models()
        
        # Generate demo files
        demo_results = await tts_manager.generate_multilingual_demo()
        
        # Return results with download links
        return {
            "success": True,
            "message": "Multilingual demo generated successfully",
            "languages": demo_results,
            "supported_languages": tts_manager.get_supported_languages()
        }
        
    except Exception as e:
        print(f"Multilingual demo error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Demo generation failed: {str(e)}"
        )

@router.get("/supported-languages")
async def get_supported_languages():
    """Get list of supported TTS languages"""
    
    languages = {
        "google_cloud": ["en-US", "en-GB", "es-ES", "fr-FR", "de-DE"] if GOOGLE_CLOUD_AVAILABLE else [],
        "chatterbox": []
    }
    
    if CHATTERBOX_AVAILABLE:
        try:
            if not tts_manager.is_initialized:
                await tts_manager.initialize_models()
            languages["chatterbox"] = tts_manager.get_supported_languages()
        except:
            pass
    
    return {
        "available_engines": {
            "google_cloud": GOOGLE_CLOUD_AVAILABLE,
            "chatterbox": CHATTERBOX_AVAILABLE
        },
        "supported_languages": languages,
        "recommended_engine": "chatterbox" if CHATTERBOX_AVAILABLE else "google_cloud"
    }

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