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
  const [projectHistory, setProjectHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [historyError, setHistoryError] = useState(null);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const chatContainerRef = useRef(null);
  const speechSynthRef = useRef(null);
  const currentAudioRef = useRef(null);

  // Initialize with greeting
  useEffect(() => {
    const greeting = {
      type: 'ai',
      content: "Hey there! 👋 I'm your coding buddy and I'm super excited to help you build something awesome! What cool idea do you have in mind?",
      timestamp: new Date()
    };
    setConversation([greeting]);
    
    // Speak the greeting only once
    const timer = setTimeout(() => {
      if (!isMuted) {
        speakText(greeting.content);
      }
    }, 500); // Small delay to ensure component is ready
    
    return () => clearTimeout(timer);
  }, []); // Empty dependency array to run only once

  // Auto-scroll to latest message
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [conversation]);

  // Cleanup effect: Stop all audio when component unmounts (navigation away)
  useEffect(() => {
    return () => {
      // Stop any playing audio
      stopSpeaking();
      
      // Stop recording if active
      if (mediaRecorderRef.current && isRecording) {
        mediaRecorderRef.current.stop();
      }
      
      // Clean up any media streams
      if (mediaRecorderRef.current && mediaRecorderRef.current.stream) {
        mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      }
    };
  }, []); // Empty dependency array means this runs only on unmount

  // Handle page visibility changes (tab switching, minimizing)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden && isPlaying) {
        // Page is hidden (user switched tabs/minimized), stop audio
        stopSpeaking();
        setAudioStoppedMessage('🔇 Audio stopped (tab switched)');
        setTimeout(() => setAudioStoppedMessage(''), 3000);
      }
    };

    const handleBeforeUnload = () => {
      // Page is being unloaded (navigation/close), stop all audio
      stopSpeaking();
      if (mediaRecorderRef.current && isRecording) {
        mediaRecorderRef.current.stop();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('beforeunload', handleBeforeUnload);
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [isPlaying, isRecording]);

  // Fetch project history
  const fetchProjectHistory = async () => {
    try {
      console.log('🔄 Fetching project history...');
      setIsLoadingHistory(true);
      setHistoryError(null);
      
      const response = await fetch('http://localhost:8000/api/project-history');
      
      console.log('📡 Response status:', response.status);
      console.log('📡 Response headers:', Object.fromEntries(response.headers.entries()));
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('📊 Project history data:', data);
      
      if (data.success) {
        setProjectHistory(data.projects || []);
        setHistoryError(null);
        console.log('✅ Successfully loaded', data.projects?.length || 0, 'projects');
      } else {
        console.error('❌ Failed to fetch project history:', data.error);
        setHistoryError(data.error || 'Failed to load projects');
        setProjectHistory([]);
      }
    } catch (error) {
      console.error('❌ Error fetching project history:', error);
      setHistoryError(error.message || 'Network error while loading projects');
      setProjectHistory([]);
    } finally {
      setIsLoadingHistory(false);
      console.log('🏁 Finished loading project history');
    }
  };

  // Load project history on component mount
  useEffect(() => {
    fetchProjectHistory();
  }, []);

  // Speech-to-Text setup
  const startRecording = async () => {
    try {
      // First, get all available audio devices
      const devices = await navigator.mediaDevices.enumerateDevices();
      const audioInputs = devices.filter(device => device.kind === 'audioinput');
      
      console.log('Available audio inputs:', audioInputs);
      
      // Use selected device or find the best microphone
      let deviceId = selectedDeviceId;
      
      if (!deviceId) {
        // Look for microphone devices (avoid system audio mixers)
        const micDevice = audioInputs.find(device => 
          device.label.toLowerCase().includes('mic') || 
          device.label.toLowerCase().includes('microphone') ||
          (!device.label.toLowerCase().includes('stereo') && 
           !device.label.toLowerCase().includes('speaker') &&
           !device.label.toLowerCase().includes('mix') &&
           !device.label.toLowerCase().includes('what u hear') &&
           !device.label.toLowerCase().includes('what you hear'))
        );
        
        if (micDevice) {
          deviceId = micDevice.deviceId;
          console.log('Using microphone device:', micDevice.label);
          addMessage('system', `🎤 Using: ${micDevice.label}`);
        } else {
          console.log('Using default audio input');
          addMessage('system', '⚠️ Could not find microphone - using default input. Please select your microphone below.');
        }
      } else {
        const selectedDevice = audioInputs.find(d => d.deviceId === deviceId);
        console.log('Using selected device:', selectedDevice?.label);
        addMessage('system', `🎤 Using: ${selectedDevice?.label || 'Selected device'}`);
      }

      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: { 
          deviceId: deviceId ? { exact: deviceId } : undefined,
          sampleRate: 48000, // Changed to 48000 to match WebM format
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          // Explicitly request microphone capture
          mediaSource: 'microphone'
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
      // Step 1: Transcribe audio using our voice chat API
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');
      
      const transcribeResponse = await fetch('/api/process-speech', {
        method: 'POST',
        body: formData
      });
      
      const transcribeResult = await transcribeResponse.json();
      
      if (transcribeResult.transcript) {
        // Add user message to conversation
        const userMessage = {
          type: 'user',
          content: transcribeResult.transcript,
          timestamp: new Date()
        };
        setConversation(prev => [...prev, userMessage]);
        
        // Step 2: Process with AI chat
        const chatResponse = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            message: transcribeResult.transcript,
            conversation_history: conversation 
          })
        });
        
        if (!chatResponse.ok) {
          throw new Error('Chat API failed');
        }
        
        const chatResult = await chatResponse.json();
        
        // Add AI response to conversation
        const aiMessage = {
          type: 'ai',
          content: chatResult.response,
          timestamp: new Date()
        };
        setConversation(prev => [...prev, aiMessage]);
        
        // Check if this is a project summary
        if (chatResult.response.includes('PROJECT SUMMARY:')) {
          setProjectSummary(chatResult.response);
        }
        
        // Check if user confirmed and ready to generate
        if (chatResult.should_generate) {
          await handleProjectGeneration(chatResult.project_spec);
        }
        
        // Speak the response if not muted
        if (!isMuted) {
          await speakText(chatResult.response);
        }
      } else if (transcribeResult.error) {
        // Show detailed error message from backend
        const errorMessage = {
          type: 'system',
          content: `🎤 ${transcribeResult.error}`,
          timestamp: new Date()
        };
        setConversation(prev => [...prev, errorMessage]);
        
        // Show suggestions if available
        if (transcribeResult.suggestions) {
          const suggestionText = "💡 Suggestions:\n" + transcribeResult.suggestions.map(s => `• ${s}`).join('\n');
          const suggestionMessage = {
            type: 'system',
            content: suggestionText,
            timestamp: new Date()
          };
          setConversation(prev => [...prev, suggestionMessage]);
        }
      } else {
        // Transcription failed
        const errorMessage = {
          type: 'system',
          content: "I couldn't understand that. Could you please try again or use text input?",
          timestamp: new Date()
        };
        setConversation(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error('Voice processing error:', error);
      const errorMessage = {
        type: 'ai',
        content: "Sorry, I'm having trouble processing your request. Please try again.",
        timestamp: new Date()
      };
      setConversation(prev => [...prev, errorMessage]);
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

  // Text-to-Speech using server-side TTS first, fallback to browser
  const speakText = async (text) => {
    if (isMuted || !text || isPlaying) return; // Don't play if already playing
    
    // Stop any current audio
    stopSpeaking();
    
    try {
      // Try server-side TTS first using our voice chat API
      const response = await fetch('/api/synthesize-speech', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      
      if (response.ok) {
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        
        // Store reference to current audio
        currentAudioRef.current = audio;
        
        setIsPlaying(true);
        audio.onended = () => {
          setIsPlaying(false);
          currentAudioRef.current = null;
          URL.revokeObjectURL(audioUrl); // Clean up URL
        };
        audio.onerror = () => {
          setIsPlaying(false);
          currentAudioRef.current = null;
          URL.revokeObjectURL(audioUrl); // Clean up URL
        };
        
        await audio.play();
      } else {
        // Fallback to browser speech synthesis
        useBrowserTTS(text);
      }
    } catch (error) {
      console.error('TTS error, using browser fallback:', error);
      useBrowserTTS(text);
    }
  };

  const useBrowserTTS = (text) => {
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
    speechSynthesis.speak(utterance);
  };

  const stopSpeaking = () => {
    try {
      // Stop browser speech synthesis
      speechSynthesis.cancel();
    } catch (error) {
      console.warn('Error stopping speech synthesis:', error);
    }
    
    try {
      // Stop current audio if playing
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current.currentTime = 0;
        currentAudioRef.current = null;
      }
    } catch (error) {
      console.warn('Error stopping current audio:', error);
    }
    
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
      // Generate a meaningful project name from the description and type
      const generateProjectName = (description, type) => {
        const timestamp = Date.now().toString().slice(-6); // Last 6 digits for uniqueness
        
        if (!description || description === 'AI-generated application') {
          return `app-${timestamp}`;
        }
        
        // Extract key words from description
        const cleanDesc = description.toLowerCase()
          .replace(/[^\w\s]/g, '')
          .split(' ')
          .filter(word => word.length > 2 && !['the', 'and', 'for', 'with', 'app', 'application'].includes(word))
          .slice(0, 2)
          .join('-');
        
        const typePrefix = (type || 'app').toLowerCase().split(' ')[0];
        
        return cleanDesc ? `${typePrefix}-${cleanDesc}-${timestamp}` : `${typePrefix}-app-${timestamp}`;
      };

      const projectName = generateProjectName(projectSpec.description, projectSpec.type);

      const response = await fetch('/api/build-with-ai', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          project_name: projectName,
          idea: projectSpec.description,
          tech_stack: projectSpec.tech_stack || [],
          project_type: projectSpec.type || 'web app',
          features: projectSpec.features || [],
          requirements: projectSpec
        })
      });
      
      if (!response.ok) {
        throw new Error('Project generation failed');
      }
      
      const result = await response.json();
      
      if (result.success) {
        addMessage('system', `✅ Project "${projectName}" generated successfully!`);
        
        // Refresh project history to include the new project
        fetchProjectHistory();
        
        // Redirect to Monaco editor
        setTimeout(() => {
          if (onProjectGenerated) {
            onProjectGenerated(projectName);
          } else {
            window.location.href = `/project/${projectName}`;
          }
        }, 2000);
      } else {
        addMessage('system', `❌ Project generation failed: ${result.error || 'Unknown error'}`);
      }
      
    } catch (error) {
      console.error('Project generation error:', error);
      addMessage('system', '❌ Failed to generate project. Please try again.');
    }
  };

  // Manual text input for fallback
  const [textInput, setTextInput] = useState('');
  const [audioDevices, setAudioDevices] = useState([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState('');
  const [audioStoppedMessage, setAudioStoppedMessage] = useState('');
  
  // Load available audio devices
  useEffect(() => {
    const loadAudioDevices = async () => {
      try {
        // Request permission first
        await navigator.mediaDevices.getUserMedia({ audio: true });
        
        const devices = await navigator.mediaDevices.enumerateDevices();
        const audioInputs = devices.filter(device => device.kind === 'audioinput');
        setAudioDevices(audioInputs);
        
        console.log('Audio devices loaded:', audioInputs);
      } catch (error) {
        console.error('Error loading audio devices:', error);
      }
    };
    
    loadAudioDevices();
  }, []);
  
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
                  {audioStoppedMessage && audioStoppedMessage}
                  {!isRecording && !isPlaying && !audioStoppedMessage && '💬 Ready to chat'}
                </span>
              </div>

              {/* Microphone Selector */}
              {audioDevices.length > 1 && (
                <div style={{ marginBottom: '1rem' }}>
                  <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.5rem' }}>
                    🎤 Select Microphone:
                  </label>
                  <select
                    value={selectedDeviceId}
                    onChange={(e) => setSelectedDeviceId(e.target.value)}
                    style={{
                      width: '100%',
                      background: 'rgba(255, 255, 255, 0.08)',
                      border: '1px solid rgba(255, 255, 255, 0.15)',
                      borderRadius: '0.5rem',
                      color: 'var(--text-primary)',
                      fontSize: '0.85rem',
                      padding: '0.5rem',
                    }}
                  >
                    <option value="">Default Microphone</option>
                    {audioDevices.map(device => (
                      <option key={device.deviceId} value={device.deviceId}>
                        {device.label || `Microphone ${device.deviceId.slice(0, 8)}...`}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Project History Section */}
              <div style={{ marginBottom: '1.5rem' }}>
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'space-between', 
                  marginBottom: '0.75rem' 
                }}>
                  <label style={{ 
                    fontSize: '0.85rem', 
                    color: 'var(--text-secondary)', 
                    fontWeight: '600' 
                  }}>
                    📂 Your Projects
                  </label>
                  <button
                    onClick={() => setShowHistory(!showHistory)}
                    style={{
                      background: 'rgba(255, 255, 255, 0.08)',
                      border: '1px solid rgba(255, 255, 255, 0.15)',
                      borderRadius: '0.375rem',
                      color: 'var(--text-secondary)',
                      fontSize: '0.75rem',
                      padding: '0.25rem 0.5rem',
                      cursor: 'pointer',
                    }}
                  >
                    {showHistory ? 'Hide' : `Show (${projectHistory.length})`}
                  </button>
                </div>
                
                {showHistory && (
                  <div style={{
                    background: 'rgba(255, 255, 255, 0.04)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    borderRadius: '0.5rem',
                    maxHeight: '200px',
                    overflowY: 'auto',
                  }}>
                    {isLoadingHistory ? (
                      <div style={{ 
                        padding: '1rem', 
                        textAlign: 'center', 
                        color: 'var(--text-secondary)',
                        fontSize: '0.85rem'
                      }}>
                        <Loader size={16} className="animate-spin" style={{ marginRight: '0.5rem' }} />
                        Loading projects...
                      </div>
                    ) : historyError ? (
                      <div style={{ 
                        padding: '1rem', 
                        textAlign: 'center', 
                        color: '#ef4444',
                        fontSize: '0.85rem'
                      }}>
                        ❌ {historyError}
                        <br />
                        <button 
                          onClick={fetchProjectHistory}
                          style={{
                            marginTop: '0.5rem',
                            background: 'rgba(59, 130, 246, 0.2)',
                            border: '1px solid rgba(59, 130, 246, 0.3)',
                            borderRadius: '0.25rem',
                            color: '#60a5fa',
                            fontSize: '0.7rem',
                            padding: '0.25rem 0.5rem',
                            cursor: 'pointer',
                          }}
                        >
                          🔄 Retry
                        </button>
                      </div>
                    ) : projectHistory.length === 0 ? (
                      <div style={{ 
                        padding: '1rem', 
                        textAlign: 'center', 
                        color: 'var(--text-secondary)',
                        fontSize: '0.85rem'
                      }}>
                        No projects yet. Build your first app! 🚀
                      </div>
                    ) : (
                      <div style={{ padding: '0.5rem' }}>
                        {projectHistory.slice(0, 5).map((project, index) => (
                          <div
                            key={project.slug}
                            style={{
                              padding: '0.75rem',
                              borderRadius: '0.375rem',
                              marginBottom: '0.5rem',
                              background: 'rgba(255, 255, 255, 0.02)',
                              border: '1px solid rgba(255, 255, 255, 0.05)',
                              cursor: 'pointer',
                              transition: 'all 0.2s ease',
                            }}
                            onMouseEnter={(e) => {
                              e.target.style.background = 'rgba(255, 255, 255, 0.08)';
                              e.target.style.borderColor = 'rgba(255, 255, 255, 0.15)';
                            }}
                            onMouseLeave={(e) => {
                              e.target.style.background = 'rgba(255, 255, 255, 0.02)';
                              e.target.style.borderColor = 'rgba(255, 255, 255, 0.05)';
                            }}
                          >
                            <div style={{ 
                              fontSize: '0.8rem', 
                              fontWeight: '600', 
                              color: 'var(--text-primary)',
                              marginBottom: '0.25rem'
                            }}>
                              {project.name}
                            </div>
                            <div style={{ 
                              fontSize: '0.7rem', 
                              color: 'var(--text-secondary)',
                              marginBottom: '0.5rem'
                            }}>
                              {project.tech_stack.join(', ') || 'Web App'} • {project.created_date_formatted}
                            </div>
                            <div style={{ display: 'flex', gap: '0.5rem' }}>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  window.open(project.preview_url, '_blank');
                                }}
                                style={{
                                  background: 'rgba(59, 130, 246, 0.2)',
                                  border: '1px solid rgba(59, 130, 246, 0.3)',
                                  borderRadius: '0.25rem',
                                  color: '#60a5fa',
                                  fontSize: '0.7rem',
                                  padding: '0.25rem 0.5rem',
                                  cursor: 'pointer',
                                }}
                              >
                                👁️ Preview
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  window.location.href = project.editor_url;
                                }}
                                style={{
                                  background: 'rgba(168, 85, 247, 0.2)',
                                  border: '1px solid rgba(168, 85, 247, 0.3)',
                                  borderRadius: '0.25rem',
                                  color: '#c084fc',
                                  fontSize: '0.7rem',
                                  padding: '0.25rem 0.5rem',
                                  cursor: 'pointer',
                                }}
                              >
                                ✏️ Edit
                              </button>
                            </div>
                          </div>
                        ))}
                        
                        {projectHistory.length > 5 && (
                          <div style={{ 
                            textAlign: 'center', 
                            padding: '0.5rem',
                            fontSize: '0.75rem',
                            color: 'var(--text-secondary)'
                          }}>
                            +{projectHistory.length - 5} more projects
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
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
                  <br />
                  �🇸 Optimized for English language
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