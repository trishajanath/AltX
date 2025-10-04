import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Volume2, VolumeX, MessageCircle, Loader, Play, Square, Settings, BrainCircuit } from 'lucide-react';
import PageWrapper from './PageWrapper';
import usePreventZoom from './usePreventZoom';

const VoiceChatInterface = ({ onProjectGenerated }) => {
  usePreventZoom();
  const [isRecording, setIsRecording] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [conversation, setConversation] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentTranscript, setCurrentTranscript] = useState('');
  const [projectSummary, setProjectSummary] = useState(null);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const chatContainerRef = useRef(null);
  const speechSynthRef = useRef(null);

  // Initialize with greeting
  useEffect(() => {
    const greeting = {
      type: 'ai',
      content: "Hi! I'm your AI assistant. I'll help you build your app by gathering requirements first. What would you like to build today?",
      timestamp: new Date()
    };
    setConversation([greeting]);
    
    // Speak the greeting
    if (!isMuted) {
      speakText(greeting.content);
    }
  }, []);

  // Auto-scroll to latest message
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [conversation]);

  // Speech-to-Text setup
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: { 
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true
        } 
      });
      
      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      audioChunksRef.current = [];
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await processAudioInput(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorderRef.current.start(100); // Collect data every 100ms
      setIsRecording(true);
      
    } catch (error) {
      console.error('Error accessing microphone:', error);
      addMessage('system', 'Error: Could not access microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // Process audio input and send to backend
  const processAudioInput = async (audioBlob) => {
    setIsLoading(true);
    
    try {
      // Convert to format expected by backend
      const formData = new FormData();
      formData.append('audio', audioBlob, 'audio.webm');
      
      // Send to speech processing endpoint
      const response = await fetch('/api/process-speech', {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        throw new Error('Speech processing failed');
      }
      
      const result = await response.json();
      
      if (result.transcript) {
        // Add user message
        addMessage('user', result.transcript);
        
        // Send to AI for response
        await sendToAI(result.transcript);
      } else if (result.error) {
        // Show detailed error message from backend
        addMessage('system', `🎤 ${result.error}`);
        
        // Show suggestions if available
        if (result.suggestions) {
          const suggestionText = "💡 Suggestions:\n" + result.suggestions.map(s => `• ${s}`).join('\n');
          addMessage('system', suggestionText);
        }
        
        // Show fallback message if available
        if (result.fallback_message) {
          addMessage('system', `ℹ️ ${result.fallback_message}`);
        }
      } else {
        addMessage('system', 'Could not understand speech. Please try again or use text input.');
      }
      
    } catch (error) {
      console.error('Speech processing error:', error);
      addMessage('system', '🎤 Speech processing failed. Please use the text input below instead.');
    } finally {
      setIsLoading(false);
    }
  };

  // Send message to AI assistant
  const sendToAI = async (message) => {
    setIsLoading(true);
    
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: message,
          conversation_history: conversation.filter(msg => msg.type !== 'system')
        })
      });
      
      if (!response.ok) {
        throw new Error('AI chat failed');
      }
      
      const result = await response.json();
      
      // Add AI response
      addMessage('ai', result.response);
      
      // Check if this is a project summary
      if (result.response.includes('PROJECT SUMMARY:')) {
        setProjectSummary(result.response);
      }
      
      // Check if user confirmed and ready to generate
      if (result.should_generate) {
        handleProjectGeneration(result.project_spec);
      }
      
      // Speak the response if not muted
      if (!isMuted) {
        speakText(result.response);
      }
      
    } catch (error) {
      console.error('AI chat error:', error);
      addMessage('system', 'AI assistant error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Text-to-Speech
  const speakText = (text) => {
    if (isMuted || !text) return;
    
    // Cancel any ongoing speech
    if (speechSynthRef.current) {
      speechSynthesis.cancel();
    }
    
    // Clean text for speech (remove markdown, special chars)
    const cleanText = text
      .replace(/[#*_`]/g, '')
      .replace(/PROJECT SUMMARY:/g, 'Project Summary:')
      .replace(/- /g, '. ');
    
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 0.9;
    utterance.pitch = 1;
    utterance.volume = 0.8;
    
    // Find a good voice
    const voices = speechSynthesis.getVoices();
    const preferredVoice = voices.find(voice => 
      voice.name.includes('Google') || 
      voice.name.includes('Microsoft') ||
      voice.lang.includes('en-US')
    );
    if (preferredVoice) {
      utterance.voice = preferredVoice;
    }
    
    utterance.onstart = () => setIsPlaying(true);
    utterance.onend = () => setIsPlaying(false);
    utterance.onerror = () => setIsPlaying(false);
    
    speechSynthRef.current = utterance;
    speechSynthesis.speak(utterance);
  };

  const stopSpeaking = () => {
    speechSynthesis.cancel();
    setIsPlaying(false);
  };

  // Add message to conversation
  const addMessage = (type, content) => {
    const message = {
      type,
      content,
      timestamp: new Date()
    };
    setConversation(prev => [...prev, message]);
  };

  // Handle project generation
  const handleProjectGeneration = async (projectSpec) => {
    addMessage('system', '🚀 Starting project generation...');
    
    try {
      const response = await fetch('/api/build-with-ai', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          idea: projectSpec.description,
          requirements: projectSpec
        })
      });
      
      if (!response.ok) {
        throw new Error('Project generation failed');
      }
      
      const result = await response.json();
      
      if (result.success) {
        addMessage('system', `✅ Project "${result.project_name}" generated successfully!`);
        
        // Redirect to Monaco editor
        setTimeout(() => {
          if (onProjectGenerated) {
            onProjectGenerated(result.project_name);
          } else {
            window.location.href = `/project/${result.project_name}`;
          }
        }, 2000);
      } else {
        addMessage('system', '❌ Project generation failed. Please try again.');
      }
      
    } catch (error) {
      console.error('Project generation error:', error);
      addMessage('system', '❌ Failed to generate project. Please try again.');
    }
  };

  // Manual text input for fallback
  const [textInput, setTextInput] = useState('');
  
  const sendTextMessage = () => {
    if (textInput.trim()) {
      addMessage('user', textInput);
      sendToAI(textInput);
      setTextInput('');
    }
  };

  return (
    <PageWrapper>
      <style>{`
        :root {
          --bg-black: #0a0a0a;
          --card-bg: rgba(255, 255, 255, 0.04);
          --card-border: rgba(255, 255, 255, 0.08);
          --text-primary: #ffffff;
          --text-secondary: #a1a1a1;
          --accent: #4ade80;
        }
        .voice-chat-page {
          background: var(--bg-black);
          color: var(--text-primary);
          min-height: 100vh;
          font-family: "Inter", sans-serif;
        }
        .layout-container {
          max-width: 900px;
          margin: 0 auto;
          padding: 4rem 2rem;
        }
        .hero-section { text-align: center; margin-bottom: 4rem; }
        .hero-title { font-size: 3rem; font-weight: 700; margin: 0; }
        .hero-subtitle {
          font-size: 1.2rem;
          color: var(--text-secondary);
          margin-bottom: 2rem;
          line-height: 1.6;
        }

        .features-info {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 1rem;
          margin-bottom: 2rem;
          padding: 1.5rem;
          background: rgba(255, 255, 255, 0.05);
          border-radius: 1rem;
          border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .feature-item {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          font-size: 0.95rem;
          color: var(--text-primary);
        }

        .feature-icon {
          font-size: 1.2rem;
          opacity: 0.8;
        }

        .main-chat-card {
          background: var(--card-bg);
          border: 1px solid var(--card-border);
          border-radius: 1.5rem;
          padding: 0;
          margin-bottom: 2rem;
          box-shadow: 0 8px 30px rgba(0,0,0,0.2);
          transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
          overflow: hidden;
          height: 500px;
          display: flex;
          flex-direction: column;
        }
        .main-chat-card:hover {
          transform: translateY(-5px);
          box-shadow: 0 8px 32px 0 rgba(255, 255, 255, 0.1);
          border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .chat-header {
          padding: 1.5rem 2rem;
          border-bottom: 1px solid var(--card-border);
          display: flex;
          align-items: center;
          justify-content: space-between;
        }

        .chat-header-left {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .chat-controls {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .control-btn {
          background: rgba(255, 255, 255, 0.1);
          border: 1px solid rgba(255, 255, 255, 0.15);
          border-radius: 0.5rem;
          padding: 0.5rem;
          color: var(--text-primary);
          cursor: pointer;
          transition: all 0.2s ease;
        }
        .control-btn:hover {
          background: rgba(255, 255, 255, 0.15);
          border-color: rgba(255, 255, 255, 0.25);
        }
        .control-btn.active {
          background: rgba(74, 222, 128, 0.2);
          border-color: var(--accent);
          color: var(--accent);
        }
        .control-btn.recording {
          background: rgba(239, 68, 68, 0.2);
          border-color: #ef4444;
          color: #ef4444;
          animation: pulse 1s infinite;
        }

        .chat-container {
          flex: 1;
          overflow-y: auto;
          padding: 1.5rem 2rem;
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .message {
          display: flex;
          margin-bottom: 1rem;
        }
        .message.user {
          justify-content: flex-end;
        }
        .message.ai {
          justify-content: flex-start;
        }
        .message.system {
          justify-content: center;
        }

        .message-bubble {
          max-width: 70%;
          padding: 1rem 1.5rem;
          border-radius: 1rem;
          font-size: 0.95rem;
          line-height: 1.5;
        }
        .message-bubble.user {
          background: var(--accent);
          color: #000;
        }
        .message-bubble.ai {
          background: rgba(255, 255, 255, 0.08);
          color: var(--text-primary);
          border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .message-bubble.system {
          background: rgba(255, 255, 255, 0.04);
          color: var(--text-secondary);
          font-size: 0.85rem;
          text-align: center;
        }

        .message-time {
          font-size: 0.75rem;
          opacity: 0.6;
          margin-top: 0.5rem;
        }

        .loading-message {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 1rem 1.5rem;
          background: rgba(255, 255, 255, 0.08);
          border-radius: 1rem;
          color: var(--text-secondary);
          font-size: 0.9rem;
        }

        .chat-input-area {
          padding: 1.5rem 2rem;
          border-top: 1px solid var(--card-border);
          background: rgba(255, 255, 255, 0.02);
        }

        .input-container {
          display: flex;
          align-items: center;
          gap: 1rem;
        }

        .voice-btn {
          background: var(--accent);
          border: none;
          color: #000;
          padding: 0.75rem;
          border-radius: 50%;
          cursor: pointer;
          transition: all 0.3s ease;
          font-weight: 600;
          font-size: 1rem;
          width: 48px;
          height: 48px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .voice-btn:hover:not(:disabled) { 
          opacity: 0.9; 
          transform: translateY(-2px); 
        }
        .voice-btn:disabled { 
          opacity: 0.6; 
          cursor: not-allowed; 
        }
        .voice-btn.recording {
          background: #ef4444;
          color: #fff;
          animation: pulse 1s infinite;
        }

        .text-input {
          flex: 1;
          background: rgba(255, 255, 255, 0.08);
          border: 1px solid rgba(255, 255, 255, 0.15);
          border-radius: 1rem;
          color: var(--text-primary);
          font-size: 1rem;
          padding: 0.75rem 1.25rem;
          transition: all 0.2s ease;
        }
        .text-input:focus { 
          outline: none;
          border-color: var(--accent);
          box-shadow: 0 0 0 3px rgba(74, 222, 128, 0.1);
        }
        .text-input::placeholder {
          color: var(--text-secondary);
          opacity: 0.7;
        }

        .send-btn {
          background: rgba(255, 255, 255, 0.1);
          border: 1px solid rgba(255, 255, 255, 0.15);
          color: var(--text-primary);
          padding: 0.75rem 1.25rem;
          border-radius: 1rem;
          cursor: pointer;
          font-weight: 600;
          transition: all 0.2s ease;
        }
        .send-btn:hover:not(:disabled) {
          background: rgba(255, 255, 255, 0.15);
          border-color: rgba(255, 255, 255, 0.25);
        }
        .send-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .status-bar {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-top: 1rem;
          font-size: 0.85rem;
          color: var(--text-secondary);
        }

        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
      
      <div className="voice-chat-page">
        <div className="layout-container">
          {/* Hero Section */}
          <div className="hero-section">
            <h1 className="hero-title">
              🎤 Voice Chat Builder
            </h1>
            <p className="hero-subtitle">
              Build full-stack applications through natural conversation with AI
            </p>
            
            {/* Features Info */}
            <div className="features-info">
              <div className="feature-item">
                <span className="feature-icon">🗣️</span>
                <span>Voice Recognition</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon">🤖</span>
                <span>AI Assistant</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon">⚡</span>
                <span>Real-time Generation</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon">🚀</span>
                <span>Auto Deploy</span>
              </div>
            </div>
          </div>

          {/* Main Chat Interface */}
          <div className="main-chat-card">
            {/* Chat Header */}
            <div className="chat-header">
              <div className="chat-header-left">
                <BrainCircuit size={24} style={{ color: 'var(--accent)' }} />
                <div>
                  <div style={{ fontWeight: '600', fontSize: '1.1rem' }}>AI Assistant</div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    Voice-powered project generation
                  </div>
                </div>
              </div>
              
              <div className="chat-controls">
                <button
                  onClick={() => setIsMuted(!isMuted)}
                  className={`control-btn ${isMuted ? 'active' : ''}`}
                  title={isMuted ? 'Enable audio' : 'Mute audio'}
                >
                  {isMuted ? <VolumeX size={16} /> : <Volume2 size={16} />}
                </button>
                
                {isPlaying && (
                  <button
                    onClick={stopSpeaking}
                    className="control-btn active"
                    title="Stop speaking"
                  >
                    <Square size={16} />
                  </button>
                )}
              </div>
            </div>

            {/* Chat Container */}
            <div ref={chatContainerRef} className="chat-container">
              {conversation.map((message, index) => (
                <div key={index} className={`message ${message.type}`}>
                  <div className={`message-bubble ${message.type}`}>
                    <div className="whitespace-pre-wrap">{message.content}</div>
                    <div className="message-time">
                      {message.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}
              
              {isLoading && (
                <div className="loading-message">
                  <Loader size={16} className="animate-spin" />
                  <span>AI is thinking...</span>
                </div>
              )}
            </div>

            {/* Chat Input Area */}
            <div className="chat-input-area">
              <div className="input-container">
                <button
                  onClick={isRecording ? stopRecording : startRecording}
                  disabled={isLoading}
                  className={`voice-btn ${isRecording ? 'recording' : ''}`}
                  title={isRecording ? 'Stop recording' : 'Start voice recording'}
                >
                  {isRecording ? <Square size={20} /> : <Mic size={20} />}
                </button>
                
                <input
                  type="text"
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && sendTextMessage()}
                  placeholder="Describe your app idea or ask questions..."
                  className="text-input"
                  disabled={isLoading}
                />
                
                <button
                  onClick={sendTextMessage}
                  disabled={!textInput.trim() || isLoading}
                  className="send-btn"
                >
                  Send
                </button>
              </div>
              
              <div className="status-bar">
                <span>
                  {isRecording && '🔴 Recording...'}
                  {isPlaying && '🔊 AI Speaking...'}
                  {!isRecording && !isPlaying && '💬 Ready for conversation'}
                </span>
                <span>
                  Voice & text input • Real-time AI responses
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </PageWrapper>
  );
};

export default VoiceChatInterface;