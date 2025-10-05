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
          --accent-purple: #a855f7;
          --accent-blue: #3b82f6;
        }

        .voice-chat-page {
          background: transparent;
          color: var(--text-primary);
          min-height: 100vh;
          font-family: "Inter", sans-serif;
          position: relative;
        }

        /* Aura Designer inspired layout */
        .designer-layout {
          height: 100vh;
          display: grid;
          grid-template-columns: 1fr;
          gap: 1rem;
          padding: 1rem;
        }

        @media (min-width: 768px) {
          .designer-layout {
            grid-template-columns: 2fr 1fr;
          }
        }

        @media (min-width: 1024px) {
          .designer-layout {
            grid-template-columns: 7fr 3fr;
          }
        }

        .main-canvas-area {
          background: rgba(17, 24, 39, 0.5);
          border-radius: 1rem;
          display: flex;
          flex-direction: column;
          overflow: hidden;
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .canvas-header {
          padding: 1rem;
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
          display: flex;
          align-items: center;
          justify-content: space-between;
        }

        .project-title {
          font-weight: 700;
          font-size: 1.125rem;
          background: linear-gradient(135deg, #3b82f6, #a855f7);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .canvas-content {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 2rem;
          position: relative;
        }

        .conversation-display {
          width: 100%;
          max-width: 600px;
          background: rgba(255, 255, 255, 0.02);
          border-radius: 1rem;
          border: 1px solid rgba(255, 255, 255, 0.08);
          overflow: hidden;
          display: flex;
          flex-direction: column;
          height: 500px;
        }

        .conversation-header {
          padding: 1rem 1.5rem;
          border-bottom: 1px solid rgba(255, 255, 255, 0.08);
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .ai-avatar {
          width: 2rem;
          height: 2rem;
          border-radius: 50%;
          background: linear-gradient(135deg, #3b82f6, #a855f7);
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 700;
          font-size: 0.875rem;
          color: white;
        }

        .conversation-messages {
          flex: 1;
          overflow-y: auto;
          padding: 1rem;
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .message {
          display: flex;
          gap: 0.75rem;
          align-items: flex-start;
        }

        .message.user {
          justify-content: flex-end;
        }

        .message.user .message-bubble {
          background: linear-gradient(135deg, #a855f7, #3b82f6);
          color: white;
          border-radius: 1rem 1rem 0.25rem 1rem;
        }

        .message.ai .message-bubble {
          background: rgba(255, 255, 255, 0.08);
          color: var(--text-primary);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 1rem 1rem 1rem 0.25rem;
        }

        .message.system .message-bubble {
          background: rgba(255, 255, 255, 0.04);
          color: var(--text-secondary);
          font-size: 0.875rem;
          text-align: center;
          border-radius: 1rem;
          margin: 0 auto;
        }

        .message-bubble {
          padding: 0.75rem 1rem;
          max-width: 300px;
          font-size: 0.9rem;
          line-height: 1.5;
          white-space: pre-wrap;
        }

        .message-time {
          font-size: 0.75rem;
          opacity: 0.6;
          margin-top: 0.25rem;
        }

        .conversation-sidebar {
          background: rgba(17, 24, 39, 0.5);
          border-radius: 1rem;
          display: flex;
          flex-direction: column;
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .sidebar-header {
          padding: 1rem 1.5rem;
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .sidebar-title {
          font-weight: 600;
          font-size: 1rem;
          color: var(--text-primary);
        }

        .sidebar-content {
          flex: 1;
          padding: 1rem;
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .voice-orb-container {
          display: flex;
          justify-content: center;
          margin: 2rem 0;
        }

        .voice-orb {
          position: relative;
          width: 120px;
          height: 120px;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .voice-orb:hover {
          transform: scale(1.05);
        }

        .orb-outer {
          position: absolute;
          inset: 0;
          border-radius: 50%;
          background: conic-gradient(from 180deg at 50% 50%, #3b82f6 0%, #a855f7 25%, #ef4444 50%, #f59e0b 75%, #3b82f6 100%);
          animation: spin 10s linear infinite;
          filter: blur(8px);
        }

        .orb-inner {
          position: absolute;
          inset: 4px;
          background: #030712;
          border-radius: 50%;
          z-index: 10;
          display: flex;
          align-items: center;
          justify-content: center;
          border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .orb-inner svg {
          width: 2rem;
          height: 2rem;
          color: var(--text-secondary);
          transition: color 0.3s ease;
        }

        .voice-orb.recording .orb-outer {
          animation: pulse 1.5s infinite, spin 10s linear infinite;
        }

        .voice-orb.recording .orb-inner svg {
          color: #ef4444;
        }

        .input-section {
          margin-top: auto;
        }

        .text-input-container {
          position: relative;
          margin-bottom: 1rem;
        }

        .text-input {
          width: 100%;
          background: rgba(255, 255, 255, 0.08);
          border: 1px solid rgba(255, 255, 255, 0.15);
          border-radius: 2rem;
          color: var(--text-primary);
          font-size: 0.9rem;
          padding: 0.75rem 3rem 0.75rem 1rem;
          transition: all 0.2s ease;
        }

        .text-input:focus {
          outline: none;
          border-color: var(--accent-purple);
          box-shadow: 0 0 0 3px rgba(168, 85, 247, 0.1);
        }

        .text-input::placeholder {
          color: var(--text-secondary);
          opacity: 0.7;
        }

        .send-button {
          position: absolute;
          right: 0.25rem;
          top: 50%;
          transform: translateY(-50%);
          width: 2rem;
          height: 2rem;
          border-radius: 50%;
          background: linear-gradient(135deg, #3b82f6, #a855f7);
          border: none;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .send-button:hover:not(:disabled) {
          transform: translateY(-50%) scale(1.1);
        }

        .send-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .send-button svg {
          width: 0.875rem;
          height: 0.875rem;
          color: white;
        }

        .status-indicators {
          display: flex;
          align-items: center;
          justify-content: space-between;
          font-size: 0.8rem;
          color: var(--text-secondary);
        }

        .control-buttons {
          display: flex;
          gap: 0.5rem;
        }

        .control-btn {
          background: rgba(255, 255, 255, 0.08);
          border: 1px solid rgba(255, 255, 255, 0.15);
          border-radius: 0.5rem;
          padding: 0.5rem;
          color: var(--text-secondary);
          cursor: pointer;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .control-btn:hover {
          background: rgba(255, 255, 255, 0.12);
          color: var(--text-primary);
        }

        .control-btn.active {
          background: rgba(168, 85, 247, 0.2);
          border-color: var(--accent-purple);
          color: var(--accent-purple);
        }

        .loading-indicator {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.75rem 1rem;
          background: rgba(255, 255, 255, 0.05);
          border-radius: 1rem;
          color: var(--text-secondary);
          font-size: 0.875rem;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        @keyframes pulse {
          0%, 100% { opacity: 0.8; transform: scale(1); }
          50% { opacity: 1; transform: scale(1.05); }
        }

        .fade-in {
          animation: fadeIn 0.5s ease-in-out forwards;
        }

        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
      
      <div className="voice-chat-page">
        <main className="designer-layout fade-in">
          {/* Main Canvas Area - Left Side */}
          <div className="main-canvas-area">
            <div className="canvas-header">
              <div className="project-title">🎤 AI Voice Builder</div>
              <div className="control-buttons">
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

            <div className="canvas-content">
              <div className="conversation-display">
                <div className="conversation-header">
                  <div className="ai-avatar">A</div>
                  <div>
                    <div style={{ fontWeight: '600', fontSize: '0.95rem' }}>AI Assistant</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      Voice-powered project generation
                    </div>
                  </div>
                </div>

                <div ref={chatContainerRef} className="conversation-messages">
                  {conversation.map((message, index) => (
                    <div key={index} className={`message ${message.type}`}>
                      {message.type === 'ai' && (
                        <div className="ai-avatar">A</div>
                      )}
                      <div className={`message-bubble ${message.type}`}>
                        <div className="whitespace-pre-wrap">{message.content}</div>
                        <div className="message-time">
                          {message.timestamp.toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  ))}
                  
                  {isLoading && (
                    <div className="loading-indicator">
                      <Loader size={16} className="animate-spin" />
                      <span>AI is thinking...</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Conversation Sidebar - Right Side */}
          <div className="conversation-sidebar">
            <div className="sidebar-header">
              <div className="sidebar-title">Voice Interface</div>
            </div>

            <div className="sidebar-content">
              {/* Voice Orb */}
              <div className="voice-orb-container">
                <div 
                  className={`voice-orb ${isRecording ? 'recording' : ''}`}
                  onClick={isRecording ? stopRecording : startRecording}
                >
                  <div className="orb-outer"></div>
                  <div className="orb-inner">
                    {isRecording ? <Square size={32} /> : <Mic size={32} />}
                  </div>
                </div>
              </div>

              {/* Status */}
              <div className="status-indicators">
                <span>
                  {isRecording && '🔴 Recording...'}
                  {isPlaying && '🔊 AI Speaking...'}
                  {!isRecording && !isPlaying && '💬 Ready to chat'}
                </span>
              </div>

              {/* Text Input Section */}
              <div className="input-section">
                <div className="text-input-container">
                  <input
                    type="text"
                    value={textInput}
                    onChange={(e) => setTextInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendTextMessage()}
                    placeholder="Describe your app idea..."
                    className="text-input"
                    disabled={isLoading}
                  />
                  <button
                    onClick={sendTextMessage}
                    disabled={!textInput.trim() || isLoading}
                    className="send-button"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
                    </svg>
                  </button>
                </div>

                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textAlign: 'center', marginTop: '0.5rem' }}>
                  Click the orb to speak • Type as backup
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </PageWrapper>
  );
};

export default VoiceChatInterface;