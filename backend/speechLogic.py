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

# --- Load .env ---
load_dotenv()

# --- Setup Gemini as Requirements Gathering Assistant ---
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel(
    'gemini-2.5-flash',
    system_instruction="""You are a professional software requirements analyst.

YOUR JOB: Gather complete specifications before generating ANY code.

WORKFLOW:
1. When user says they want to build something, ask SHORT clarifying questions ONE AT A TIME
2. Gather these key details:
   - Project type (web app, mobile app, desktop app, website, etc.)
   - Purpose and main functionality
   - Target users/audience
   - Key features (list 3-5 main features)
   - Tech stack preferences (framework, language, database)
   - Design preferences (style, colors, layout)
   - Any special requirements
   
3. SMART DEFAULTS: If user says "I don't know", "skip", "default", or gives unclear answer:
   - Fill in a reasonable default
   - Announce it: "Okay, I'll assume [default choice]"
   - Continue to next question
   
4. After gathering ALL information, create a summary in this EXACT format:
   PROJECT SUMMARY:
   - Type: [project type]
   - Purpose: [brief description]
   - Target Users: [audience]
   - Key Features: [list features]
   - Tech Stack: [technologies]
   - Design: [design preferences]
   
   Then ask: "Does this look correct? Say 'yes' to proceed with code generation or 'no' to make changes."

5. ONLY generate code after user confirms with "yes"

RULES:
- Keep ALL responses SHORT (1-3 sentences max)
- Ask ONE question at a time
- Be conversational and friendly
- Use smart defaults when user is unsure
- Never generate code until user confirms the summary
- If user wants changes, ask what to modify"""
)

# Initialize chat and state
chat = model.start_chat(history=[])
conversation_state = {
    "gathering_requirements": False,
    "requirements_complete": False,
    "waiting_for_confirmation": False,
    "project_summary": None,
    "ready_to_generate": False
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