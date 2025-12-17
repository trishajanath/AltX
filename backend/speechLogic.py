import os
from dotenv import load_dotenv
import wave
import pyaudio
import subprocess
import google.generativeai as genai
from google.cloud import speech, texttospeech
import re
import json
from datetime import datetime
from pure_ai_generator import PureAIGenerator
from s3_storage import upload_project_to_s3
import asyncio
from pathlib import Path

# --- Load .env ---
load_dotenv()

# --- Setup Gemini as Requirements Gathering Assistant ---
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel(
    'gemini-2.5-flash',
    system_instruction="""You are a casual, friendly AI buddy who loves helping people build cool web apps through voice chat!

CONVERSATION STYLE:
- Talk like a friend, not a formal assistant
- Keep responses super short (1-2 sentences max)
- Use casual language: "Cool!", "Awesome!", "Nice idea!", "Got it!"
- Ask ONE simple question at a time
- Don't overthink it - if the user gives you enough to start, just go with it

CONVERSATION FLOW:
1. When someone wants to build something, get excited and ask what they have in mind
2. Chat naturally about their idea - don't interrogate them with formal questions
3. If they seem ready or say things like "let's build it", "start building", "make it now" - just go ahead and build!
4. When you have a decent idea OR user wants to start, create a quick summary:

   PROJECT SUMMARY
   ===============
   - Type: [app type]
   - Purpose: [brief description]  
   - Key Features: [main features]
   - Tech Stack: React + FastAPI
   
   Then say: "Sound good? Say 'yes' to build it or 'no' to change something!"

5. Build immediately if user confirms OR if they explicitly request it during conversation

EARLY BUILD TRIGGERS:
- "let's build this", "start building", "make it now", "build it", "create it"
- "I'm ready", "that's enough", "go ahead", "sounds good, build it"

RULES:
- Be enthusiastic and casual
- Don't over-complicate things
- Build with partial info if user wants to start
- Use smart defaults for missing details"""
)

# Initialize chat, AI generator, and state
chat = model.start_chat(history=[])
ai_generator = PureAIGenerator(
    s3_uploader=upload_project_to_s3,
    user_id='anonymous'  # speechLogic doesn't have user auth yet
)
conversation_state = {
    "gathering_requirements": False,
    "requirements_complete": False,
    "waiting_for_confirmation": False,
    "project_summary": None,
    "ready_to_generate": False,
    "project_name": None,
    "project_idea": None
}

# --- Record audio ---
def record_audio(filename="input.wav", record_seconds=5):
    chunk = 1024
    sample_format = pyaudio.paInt16
    channels = 1
    rate = 16000
    p = pyaudio.PyAudio()

    print("\n🎤 Recording... Speak now!")
    stream = p.open(format=sample_format, channels=channels,
                    rate=rate, input=True,
                    frames_per_buffer=chunk)
    frames = []
    for _ in range(0, int(rate / chunk * record_seconds)):
        frames.append(stream.read(chunk))
    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(filename, "wb")
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(sample_format))
    wf.setframerate(rate)
    wf.writeframes(b"".join(frames))
    wf.close()

# --- Speech-to-Text ---
def transcribe_audio(filename="input.wav"):
    client_speech = speech.SpeechClient()
    with open(filename, "rb") as f:
        audio = speech.RecognitionAudio(content=f.read())

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
    )

    response = client_speech.recognize(config=config, audio=audio)
    if response.results:
        transcript = response.results[0].alternatives[0].transcript
        print(f"📝 You said: {transcript}")
        return transcript
    return ""

# --- Get text input as fallback ---
def get_text_input():
    """Allow user to type if voice wasn't clear"""
    print("\n⌨️  If I didn't understand you correctly, type your answer here")
    print("   (or press Enter to use voice transcription): ", end="")
    typed_input = input().strip()
    if typed_input:
        print(f"📝 You typed: {typed_input}")
        return typed_input
    return None

# --- Detect project intent ---
def is_build_request(text):
    """Check if user wants to build something"""
    keywords = [
        "build", "create", "make", "develop", "design", "app", "website",
        "application", "program", "system", "platform", "tool", "want to build"
    ]
    return any(keyword in text.lower() for keyword in keywords)

# --- Detect confirmation ---
def is_confirmation(text):
    """Check if user is confirming or rejecting"""
    text_lower = text.lower().strip()
    confirmations = ["yes", "yeah", "yep", "correct", "looks good", "perfect", "proceed", "go ahead"]
    rejections = ["no", "nope", "not quite", "change", "modify", "wrong"]
    
    if any(word in text_lower for word in confirmations):
        return "yes"
    elif any(word in text_lower for word in rejections):
        return "no"
    return None

# --- Detect early build requests ---
def is_early_build_request(text):
    """Check if user wants to start building immediately"""
    early_build_keywords = [
        "let's build", "start building", "make it now", "build it", "create it",
        "i'm ready", "that's enough", "go ahead", "sounds good, build it",
        "build this", "let's go", "start now", "make this", "ready to build"
    ]
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in early_build_keywords)

# --- Extract summary from response ---
def extract_summary(text):
    """Extract project summary from assistant's response"""
    if "PROJECT SUMMARY:" in text:
        # Extract everything from PROJECT SUMMARY onwards
        summary_start = text.find("PROJECT SUMMARY:")
        summary = text[summary_start:].strip()
        return summary
    return None

# --- Extract code from markdown ---
def extract_code_from_response(text):
    """Extract all code blocks from response"""
    pattern = r'```(\w+)?\n(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)
    
    code_blocks = []
    for match in matches:
        language = match[0] or "python"
        code = match[1].strip()
        code_blocks.append((code, language))
    
    return code_blocks

# --- Save code to file ---
def save_code(code, language, filename=None):
    """Save generated code to a file"""
    extensions = {
        "python": "py", "javascript": "js", "typescript": "ts",
        "html": "html", "css": "css", "jsx": "jsx", "tsx": "tsx"
    }
    
    ext = extensions.get(language.lower(), "txt")
    
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"generated_{language}_{timestamp}.{ext}"
    
    with open(filename, "w") as f:
        f.write(code)
    
    print(f"💾 Code saved to: {filename}")
    return filename

# --- Print code ---
def print_code(code, language, filename):
    """Print code with formatting"""
    print("\n" + "="*70)
    print(f"💻 GENERATED CODE ({language.upper()}) - {filename}")
    print("="*70)
    print(code)
    print("="*70 + "\n")

# --- Get AI response ---
def get_ai_reply(user_text):
    try:
        response = chat.send_message(user_text)
        ai_text = response.text
        print(f"\n🤖 Assistant: {ai_text}\n")
        return ai_text
    except Exception as e:
        print(f"❌ Error: {e}")
        return "I'm sorry, I encountered an error. Can you repeat that?"

# --- API Functions for Monaco Server Integration ---

def transcribe_audio_data(audio_data):
    """Transcribe audio data from bytes"""
    try:
        client_speech = speech.SpeechClient()
        audio = speech.RecognitionAudio(content=audio_data)

        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,  # Changed for web audio
            sample_rate_hertz=48000,  # Common web audio rate
            language_code="en-US",
        )

        response = client_speech.recognize(config=config, audio=audio)
        if response.results:
            transcript = response.results[0].alternatives[0].transcript
            print(f"📝 Transcribed: {transcript}")
            return transcript
        return ""
    except Exception as e:
        print(f"Transcription error: {e}")
        return ""

def text_to_speech(text):
    """Convert text to speech and return audio data"""
    try:
        if len(text) > 500:
            text = text[:500]
        
        tts_client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US", 
            name="en-US-Neural2-C",
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.05
        )

        response = tts_client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        return response.audio_content
    except Exception as e:
        print(f"TTS error: {e}")
        return None

async def process_speech_request(text):
    """Main function to process speech requests from Monaco server"""
    global conversation_state, chat, ai_generator
    
    result = {
        "response": "",
        "conversation_state": conversation_state.copy(),
        "code_generated": False,
        "files_created": [],
        "project_path": None
    }
    
    try:
        print(f"🎯 Processing speech: {text}")
        
        # 1. User initiates a build request
        if is_build_request(text) and not conversation_state["gathering_requirements"]:
            conversation_state["gathering_requirements"] = True
            conversation_state["waiting_for_confirmation"] = False
            conversation_state["ready_to_generate"] = False
            
            ai_response = get_ai_reply(text)
            result["response"] = ai_response
            result["conversation_state"] = conversation_state.copy()
        
        # 2. Handle early build requests during conversation
        elif conversation_state["gathering_requirements"] and is_early_build_request(text):
            # User wants to start building now - create a quick summary and proceed
            print("🚀 Early build request detected!")
            
            # Get AI to create a summary with current conversation context
            summary_prompt = f"Based on our conversation, create a quick PROJECT SUMMARY for this app idea and say you'll start building: {text}"
            ai_response = get_ai_reply(summary_prompt)
            
            # Try to extract summary from the response
            summary = extract_summary(ai_response)
            if summary:
                conversation_state["project_summary"] = summary
                conversation_state["waiting_for_confirmation"] = True
                conversation_state["requirements_complete"] = True
                print(f"📋 Quick summary created: {summary[:100]}...")
            else:
                # If no formal summary, create a basic one
                basic_summary = f"PROJECT SUMMARY\n===============\n- Type: Web Application\n- Purpose: {text}\n- Key Features: User-friendly interface, responsive design\n- Tech Stack: React + FastAPI"
                conversation_state["project_summary"] = basic_summary
                conversation_state["waiting_for_confirmation"] = True
                conversation_state["requirements_complete"] = True
                ai_response += f"\n\n{basic_summary}\n\nSound good? Say 'yes' to build it!"
            
            result["response"] = ai_response
            result["conversation_state"] = conversation_state.copy()
        
        # 3. Handle confirmation
        elif conversation_state["waiting_for_confirmation"]:
            confirmation = is_confirmation(text)

            if confirmation == "yes":
                conversation_state["ready_to_generate"] = True
                conversation_state["waiting_for_confirmation"] = False

                # Extract project details from the summary
                summary = conversation_state.get("project_summary", "")
                project_name = extract_project_name_from_summary(summary)
                conversation_state["project_name"] = project_name
                
                # Extract project idea from summary
                project_idea = "web application"
                for line in summary.split('\n'):
                    if 'Type:' in line:
                        project_idea = line.split('Type:')[-1].strip()
                    elif 'Purpose:' in line:
                        purpose = line.split('Purpose:')[-1].strip()
                        project_idea = f"{project_idea} - {purpose}"

                conversation_state["project_idea"] = project_idea

                try:
                    print(f"🚀 Starting code generation for: {project_name}")
                    print(f"💡 Project idea: {project_idea}")

                    # Create project directory
                    project_path = Path(f"generated_projects/{project_name.lower().replace(' ', '-')}")
                    
                    # Use Pure AI Generator to create the project
                    files_created = await ai_generator.generate_project_structure(
                        project_path=project_path,
                        idea=project_idea,
                        project_name=project_name
                    )

                    print(f"✅ Successfully generated {len(files_created)} files!")
                    print("📂 Files created:")
                    for file in files_created:
                        print(f"  - {file}")

                    success_msg = f"🎉 Your {project_name} application has been successfully generated! I created {len(files_created)} files including React frontend, FastAPI backend, and all necessary configuration."
                    print(success_msg)

                    result["code_generated"] = True
                    result["files_created"] = [str(f) for f in files_created]
                    result["project_path"] = str(project_path)
                    result["response"] = success_msg

                except Exception as e:
                    error_msg = f"❌ Error generating code: {e}"
                    print(error_msg)
                    result["response"] = f"I encountered an error while generating your application: {str(e)}. Let me try again or you can provide more details."
                
                # Reset state for the next conversation
                conversation_state = {
                    "gathering_requirements": False,
                    "requirements_complete": False,
                    "waiting_for_confirmation": False,
                    "project_summary": None,
                    "ready_to_generate": False,
                    "project_name": None,
                    "project_idea": None
                }
                
                # Update the result with the reset state before returning
                result["conversation_state"] = conversation_state.copy()

            elif confirmation == "no":
                # User wants to make changes
                conversation_state["waiting_for_confirmation"] = False
                conversation_state["gathering_requirements"] = True
                ai_response = get_ai_reply(text + " - What would you like to change?")
                result["response"] = ai_response
                result["conversation_state"] = conversation_state.copy()
            else:
                # Unclear response, ask for clarification
                result["response"] = "I didn't catch that. Please say 'yes' to proceed with code generation or 'no' to make changes."
                result["conversation_state"] = conversation_state.copy()
        
        # 4. Gathering requirements
        elif conversation_state["gathering_requirements"]:
            ai_response = get_ai_reply(text)
            
            # Check if summary was provided
            summary = extract_summary(ai_response)
            if summary:
                conversation_state["project_summary"] = summary
                conversation_state["waiting_for_confirmation"] = True
                conversation_state["requirements_complete"] = True
                print(f"📋 Summary extracted: {summary[:100]}...")
            
            result["response"] = ai_response
            result["conversation_state"] = conversation_state.copy()
        
        # 5. General conversation
        else:
            ai_response = get_ai_reply(text)
            result["response"] = ai_response
            result["conversation_state"] = conversation_state.copy()

        return result

    except Exception as e:
        print(f"❌ Error in process_speech_request: {e}")
        return {
            "response": f"I encountered an error processing your request: {str(e)}. Please try again.",
            "conversation_state": conversation_state.copy(),
            "code_generated": False,
            "files_created": [],
            "project_path": None
        }

def extract_project_name_from_summary(summary):
    """Extract project name from summary"""
    lines = summary.split('\n')
    for line in lines:
        if 'Type:' in line:
            project_type = line.split('Type:')[-1].strip()
            return f"{project_type.title()} App"
        elif 'Purpose:' in line:
            purpose = line.split('Purpose:')[-1].strip()
            # Extract key words for project name
            words = purpose.split()[:3]  # First 3 words
            return ' '.join(words).title()
    
    return "My App"

# --- Text-to-Speech ---
def speak_text(text, filename="output.mp3"):
    # Truncate if too long
    if len(text) > 500:
        text = text[:500]
    
    tts_client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", 
        name="en-US-Neural2-C",
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=1.05
    )

    try:
        response = tts_client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        with open(filename, "wb") as out:
            out.write(response.audio_content)
        subprocess.run(["afplay", filename], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"❌ TTS Error: {e}")

# --- Main loop ---
if __name__ == "__main__":
    print("=" * 70)
    print("🎙️  VOICE APP BUILDER ASSISTANT")
    print("=" * 70)
    print("I'll help you build your app by gathering requirements first!")
    print("\nHow it works:")
    print("  1. Tell me what you want to build")
    print("  2. I'll ask questions to understand your needs")
    print("  3. I'll summarize and confirm with you")
    print("  4. Then I'll generate the complete code")
    print("\nPress Ctrl+C to exit")
    print("=" * 70)
    
    greeting = "Hi! What would you like to build today?"
    print(f"\n🤖 Assistant: {greeting}\n")
    speak_text(greeting)
    
    try:
        while True:
            # Record user input
            record_audio()
            text = transcribe_audio()
            
            # Allow text input as fallback
            if not text:
                print("⚠️  No speech detected.")
            
            typed_text = get_text_input()
            if typed_text:
                text = typed_text
            
            if not text:
                print("⚠️  No input received. Please try again.\n")
                continue
            
            # Check for exit
            if any(word in text.lower() for word in ["goodbye", "bye", "exit", "quit", "stop"]):
                farewell = "Goodbye! Come back when you're ready to build!"
                print(f"🤖 Assistant: {farewell}\n")
                speak_text(farewell)
                break
            
            # State machine logic
            
            # 1. User initiates a build request
            if is_build_request(text) and not conversation_state["gathering_requirements"]:
                conversation_state["gathering_requirements"] = True
                response = get_ai_reply(text)
                speak_text(response)
            
            # 2. Waiting for confirmation after summary
            elif conversation_state["waiting_for_confirmation"]:
                confirmation = is_confirmation(text)
                
                if confirmation == "yes":
                    conversation_state["ready_to_generate"] = True
                    conversation_state["waiting_for_confirmation"] = False
                    
                    # Generate code
                    generate_prompt = f"""Now generate the complete, production-ready code based on this summary:

{conversation_state['project_summary']}

Provide all necessary files with proper structure."""
                    
                    response = get_ai_reply(generate_prompt)
                    
                    # Extract code
                    code_blocks = extract_code_from_response(response)
                    
                    if code_blocks:
                        print("\n" + "="*70)
                        print("✨ CODE GENERATION COMPLETE!")
                        print("="*70)
                        
                        for code, language in code_blocks:
                            filename = save_code(code, language)
                            print_code(code, language, filename)
                        
                        summary_msg = f"Done! I've generated {len(code_blocks)} file{'s' if len(code_blocks) > 1 else ''} for your project. Check your console for all the code."
                        speak_text(summary_msg)
                    else:
                        speak_text(response)
                    
                    # Reset state
                    conversation_state = {
                        "gathering_requirements": False,
                        "requirements_complete": False,
                        "waiting_for_confirmation": False,
                        "project_summary": None,
                        "ready_to_generate": False
                    }
                
                elif confirmation == "no":
                    response = get_ai_reply(text + " - What would you like to change?")
                    speak_text(response)
                    conversation_state["waiting_for_confirmation"] = False
                    conversation_state["gathering_requirements"] = True
                else:
                    clarify = "I didn't catch that. Please say 'yes' to proceed or 'no' to make changes."
                    print(f"🤖 Assistant: {clarify}\n")
                    speak_text(clarify)
            
            # 3. Gathering requirements
            elif conversation_state["gathering_requirements"]:
                response = get_ai_reply(text)
                
                # Check if summary was provided
                summary = extract_summary(response)
                if summary:
                    conversation_state["project_summary"] = summary
                    conversation_state["waiting_for_confirmation"] = True
                    conversation_state["requirements_complete"] = True
                
                speak_text(response)
            
            # 4. General conversation
            else:
                response = get_ai_reply(text)
                speak_text(response)
            
    except KeyboardInterrupt:
        print("\n\n👋 Session ended. Happy building!")