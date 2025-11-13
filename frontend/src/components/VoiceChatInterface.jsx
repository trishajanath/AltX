import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Scan, Database, UploadCloud, Volume2, VolumeX, MessageCircle, Loader, Play, Square, Settings, BrainCircuit, ArrowRight, X } from 'lucide-react';
import PageWrapper from './PageWrapper';
import usePreventZoom from './usePreventZoom';
import {
  Menubar,
  MenubarContent,
  MenubarItem,
  MenubarMenu,
  MenubarSeparator,
  MenubarShortcut,
  MenubarTrigger,
} from "./ui/buttonswitch";
import './voice.css';
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
  
  // Format time ago function
  const formatTimeAgo = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor((now - date) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${diffInHours} hours ago`;
    
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays === 1) return 'Yesterday';
    if (diffInDays < 7) return `${diffInDays} days ago`;
    
    return date.toLocaleDateString();
  };
  
  // Real-time conversation states
  const [isRealTimeMode, setIsRealTimeMode] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [realTimeTranscript, setRealTimeTranscript] = useState('');
  const [voiceActivityTimer, setVoiceActivityTimer] = useState(null);
  const [silenceTimer, setSilenceTimer] = useState(null);
  const [speechAPIFailures, setSpeechAPIFailures] = useState(0);
  
  // NEW: State for dynamic mode switching
  const [currentMode, setCurrentMode] = useState('voice'); // 'voice', 'scan_website', 'scan_repo', 'deploy'
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const chatContainerRef = useRef(null);
  const speechSynthRef = useRef(null);
  const currentAudioRef = useRef(null);
  const recognitionRef = useRef(null);
  const realTimeStreamRef = useRef(null);
  const audioContextRef = useRef(null);
  const processorRef = useRef(null);
  const speechFailuresRef = useRef(0);
  const lastErrorTimeRef = useRef(0);
  const errorProcessingRef = useRef(false);
  const recognitionInstanceIdRef = useRef(0);
  const lastMessageContentRef = useRef('');

  // Initialize with AI welcome message
  useEffect(() => {
    // Start with AI welcome message
    setConversation([{
      type: 'ai',
      content: 'Hi! What would you like to build today?',
      timestamp: new Date()
    }]);
  }, []); // Empty dependency array to run only once

  // Suggestion chips for initial conversation
  const suggestionChips = [
    { icon: '🌐', text: 'Create a portfolio website', prompt: 'I want to create a modern portfolio website to showcase my work' },
    { icon: '🛒', text: 'Build an e-commerce site', prompt: 'Help me build an e-commerce website with a shopping cart' },
    { icon: '📱', text: 'Make a landing page', prompt: 'Create a professional landing page for my product' },
    { icon: '✨', text: 'Design a blog platform', prompt: 'I need a blog platform with post management' }
  ];

  const handleSuggestionClick = (prompt) => {
    // Add user message to conversation
    const userMessage = {
      type: 'user',
      content: prompt,
      timestamp: new Date()
    };
    
    setConversation(prev => [...prev, userMessage]);
    
    // Send to AI
    handleUserInput(prompt);
  };

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
        setAudioStoppedMessage('Audio stopped (tab switched)');
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

  // Real-time speech recognition setup with improved error handling
  useEffect(() => {
    if (!isRealTimeMode) {
      // Clean up if switching out of real-time mode
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch (error) {
          console.log('Error stopping recognition:', error);
        }
        recognitionRef.current = null;
      }
      return;
    }

    // Check for speech recognition support
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      console.warn('Speech recognition not supported');
      addMessage('system', 'Real-time speech recognition not supported in this browser. Using recording mode instead.');
      setIsRealTimeMode(false);
      return;
    }

    // Clean up existing recognition instance with more thorough cleanup
    if (recognitionRef.current) {
      try {
        recognitionRef.current.onend = null;
        recognitionRef.current.onerror = null;
        recognitionRef.current.onresult = null;
        recognitionRef.current.onstart = null;
        recognitionRef.current.stop();
        recognitionRef.current = null;
      } catch (error) {
        console.log('Error stopping existing recognition:', error);
      }
    }

    // Create unique instance ID
    recognitionInstanceIdRef.current = Date.now();
    const instanceId = recognitionInstanceIdRef.current;
    console.log('Creating speech recognition instance:', instanceId);

    let restartTimeout;
    let silenceTimeout;
    let currentTranscript = '';
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognitionRef.current = new SpeechRecognition();
    
    // Configure recognition
    recognitionRef.current.continuous = true;
    recognitionRef.current.interimResults = true;
    recognitionRef.current.lang = 'en-US';
    recognitionRef.current.maxAlternatives = 1;
    
    recognitionRef.current.onstart = () => {
      console.log('Speech recognition started');
      setIsListening(true);
      currentTranscript = '';
    };
    
    recognitionRef.current.onresult = (event) => {
      let interimTranscript = '';
      let finalTranscript = '';
      
      // Clear any existing silence timeout
      if (silenceTimeout) {
        clearTimeout(silenceTimeout);
        silenceTimeout = null;
      }
      
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript;
          currentTranscript += transcript + ' ';
        } else {
          interimTranscript += transcript;
        }
      }
      
      // Update real-time display
      setRealTimeTranscript(interimTranscript || currentTranscript);
      
      // Set timeout to detect end of speech (2 seconds of silence)
      silenceTimeout = setTimeout(() => {
        if (currentTranscript.trim()) {
          console.log('Processing after silence:', currentTranscript.trim());
          handleRealTimeTranscript(currentTranscript.trim());
          currentTranscript = '';
          setRealTimeTranscript('');
        }
      }, 2000);
      
      // Also process if we get a final result with significant content
      if (finalTranscript.trim() && finalTranscript.trim().split(' ').length >= 3) {
        // Wait a bit more to see if more speech is coming
        setTimeout(() => {
          if (currentTranscript.trim()) {
            console.log('Processing complete phrase:', currentTranscript.trim());
            handleRealTimeTranscript(currentTranscript.trim());
            currentTranscript = '';
            setRealTimeTranscript('');
          }
        }, 1000);
      }
    };
    
    recognitionRef.current.onerror = (event) => {
      console.error(`Speech recognition error (instance ${instanceId}):`, event.error);
      
      // Check if this is from an old instance
      if (instanceId !== recognitionInstanceIdRef.current) {
        console.log('Ignoring error from old instance:', instanceId);
        return;
      }
      
      // Handle specific error types
      if (event.error === 'network') {
        console.log('Network error - switching to manual mode');
        
        // Debounce: ignore if we just processed an error recently
        const now = Date.now();
        if (now - lastErrorTimeRef.current < 2000 || errorProcessingRef.current) {
          console.log('Ignoring duplicate network error (debounced)');
          return;
        }
        
        errorProcessingRef.current = true;
        lastErrorTimeRef.current = now;
        
        setSpeechAPIFailures(prevFailures => {
          const newFailures = prevFailures + 1;
          speechFailuresRef.current = newFailures;
          console.log('Speech API failures:', newFailures);
          
          if (newFailures === 1) {
            addMessage('system', '⚠️ Web Speech API network error. Retrying once...');
          } else if (newFailures === 2) {
            addMessage('system', '⚠️ Web Speech API still failing. Final retry...');
          } else if (newFailures >= 3) {
            addMessage('system', '🚫 Web Speech API unavailable (Google service issue). Please use manual recording - click the orb when ready to speak.');
            setIsListening(false);
          }
          
          // Reset processing flag after a short delay
          setTimeout(() => {
            errorProcessingRef.current = false;
          }, 500);
          
          return newFailures;
        });
      } else if (event.error === 'no-speech') {
        console.log('No speech detected');
        // This is normal, don't show error
      } else if (event.error === 'audio-capture') {
        addMessage('system', 'Microphone access error. Please check permissions and microphone selection.');
      } else if (event.error === 'not-allowed') {
        addMessage('system', 'Microphone access denied. Please allow microphone access and try again.');
        setIsRealTimeMode(false);
        return;
      } else {
        addMessage('system', `Speech recognition error: ${event.error}`);
      }
    };
    
    recognitionRef.current.onend = () => {
      console.log(`Speech recognition ended (instance ${instanceId})`);
      
      // Check if this is from an old instance
      if (instanceId !== recognitionInstanceIdRef.current) {
        console.log('Ignoring end event from old instance:', instanceId);
        return;
      }
      
      setIsListening(false);
      
      // Process any remaining transcript
      if (currentTranscript.trim()) {
        console.log('Processing remaining transcript on end:', currentTranscript.trim());
        handleRealTimeTranscript(currentTranscript.trim());
        currentTranscript = '';
      }
      setRealTimeTranscript('');
      
      // Restart after a short delay if still in real-time mode and haven't had too many failures
      if (isRealTimeMode && !isLoading) {
        restartTimeout = setTimeout(() => {
          // Check current failure count and instance at restart time
          if (recognitionRef.current && isRealTimeMode && speechFailuresRef.current < 3 && instanceId === recognitionInstanceIdRef.current) {
            try {
              recognitionRef.current.start();
            } catch (error) {
              console.log('Restart error:', error);
              // If restart fails, suggest manual mode
              addMessage('system', '💡 Speech recognition having issues. Use manual recording by clicking the orb, or try refreshing the page.');
            }
          }
        }, 2000); // Longer delay to avoid rapid failures
      }
    };
    
    // Start recognition with error handling
    try {
      recognitionRef.current.start();
    } catch (error) {
      console.error('Failed to start recognition:', error);
      addMessage('system', 'Failed to start speech recognition. Please try again.');
      setIsRealTimeMode(false);
    }
    
    return () => {
      if (restartTimeout) clearTimeout(restartTimeout);
      if (silenceTimeout) clearTimeout(silenceTimeout);
      
      if (recognitionRef.current) {
        recognitionRef.current.stop();
        recognitionRef.current = null;
      }
      setIsListening(false);
      setRealTimeTranscript('');
    };
  }, [isRealTimeMode, isLoading]);

  // Function to manually start listening (for reset button)
  const startListening = () => {
    if (!isRealTimeMode) return;
    
    try {
      // Create a new instance ID to prevent old instances from interfering
      recognitionInstanceIdRef.current = Date.now();
      console.log('Manual restart with new instance ID:', recognitionInstanceIdRef.current);
      
      // Stop any existing recognition first
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch (error) {
          console.log('Error stopping for restart:', error);
        }
      }
      
      // Small delay before restarting
      setTimeout(() => {
        if (recognitionRef.current && isRealTimeMode) {
          try {
            recognitionRef.current.start();
            console.log('Manual restart of speech recognition successful');
          } catch (error) {
            console.log('Manual restart error:', error);
            addMessage('system', '💡 Could not restart speech recognition. Try switching modes or refreshing.');
          }
        }
      }, 1000);
    } catch (error) {
      console.log('Error in startListening:', error);
    }
  };

  // Handle real-time transcript processing with proper debouncing
  const handleRealTimeTranscript = async (transcript) => {
    // Ignore very short phrases or repeated content
    if (!transcript || transcript.length < 3) return;
    
    // Check if we're already processing
    if (isLoading) {
      console.log('Already processing, ignoring:', transcript);
      return;
    }
    
    // Clear any existing timers
    if (voiceActivityTimer) {
      clearTimeout(voiceActivityTimer);
      setVoiceActivityTimer(null);
    }
    if (silenceTimer) {
      clearTimeout(silenceTimer);
      setSilenceTimer(null);
    }

    // Add user message immediately for better UX
    const userMessage = {
      type: 'user',
      content: transcript,
      timestamp: new Date()
    };
    setConversation(prev => [...prev, userMessage]);

    // Process immediately since we already detected the end of speech
    console.log('Processing transcript immediately:', transcript);
    await processRealTimeMessage(transcript);
  };

  // Process real-time message with AI
  const processRealTimeMessage = async (message) => {
    setIsLoading(true);
    
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message,
          conversation_history: conversation.filter(msg => msg.type !== 'system')
        })
      });
      
      if (!response.ok) {
        throw new Error('AI chat failed');
      }
      
      const result = await response.json();
      
      // Add AI response
      const aiMessage = {
        type: 'ai',
        content: result.response,
        timestamp: new Date()
      };
      setConversation(prev => [...prev, aiMessage]);
      
      // Handle project generation
      if (result.should_generate) {
        await handleProjectGeneration(result.project_spec);
      }
      
      // Speak response
      if (!isMuted) {
        await speakTextWithSettings(result.response);
      }
      
    } catch (error) {
      console.error('Real-time processing error:', error);
      addMessage('system', 'Error processing your message. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Toggle between real-time and recording modes
  const toggleRealTimeMode = () => {
    if (isRecording) {
      stopRecording();
    }
    
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    
    setIsRealTimeMode(!isRealTimeMode);
    
    // Add system message to inform user
    const mode = !isRealTimeMode ? 'real-time conversation' : 'recording';
    addMessage('system', `Switched to ${mode} mode`);
  };

  // Fetch project history
  const fetchProjectHistory = async () => {
    try {
      console.log('Fetching project history...');
      setIsLoadingHistory(true);
      setHistoryError(null);
      
      const response = await fetch('http://localhost:8000/api/project-history');
      
      console.log('Response status:', response.status);
      console.log('Response headers:', Object.fromEntries(response.headers.entries()));
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('Project history data:', data);
      
      if (data.success) {
        setProjectHistory(data.projects || []);
        setHistoryError(null);
        console.log('Success: Successfully loaded', data.projects?.length || 0, 'projects');
      } else {
        console.error('Error: Failed to fetch project history:', data.error);
        setHistoryError(data.error || 'Failed to load projects');
        setProjectHistory([]);
      }
    } catch (error) {
      console.error('Error fetching project history:', error);
      setHistoryError(error.message || 'Network error while loading projects');
      setProjectHistory([]);
    } finally {
      setIsLoadingHistory(false);
      console.log('Finished loading project history');
    }
  };

  // Load project history on component mount
  useEffect(() => {
    fetchProjectHistory();
  }, []);

  // Handle edit project - navigate to Monaco editor
  const handleEditProject = (project) => {
    const editorUrl = `/project/${project.slug}`;
    window.location.href = editorUrl;
  };

  // Handle preview project - open in new tab
  const handlePreviewProject = (project) => {
    const previewUrl = project.preview_url || `http://localhost:8000/api/sandbox-preview/${project.slug}`;
    window.open(previewUrl, '_blank', 'noopener,noreferrer');
  };

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
          addMessage('system', `Using: ${micDevice.label}`);
        } else {
          console.log('Using default audio input');
          addMessage('system', 'Warning: Could not find microphone - using default input. Please select your microphone below.');
        }
      } else {
        const selectedDevice = audioInputs.find(d => d.deviceId === deviceId);
        console.log('Using selected device:', selectedDevice?.label);
        addMessage('system', `Using: ${selectedDevice?.label || 'Selected device'}`);
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
          await speakTextWithSettings(chatResult.response);
        }
      } else if (transcribeResult.error) {
        // Show detailed error message from backend
        const errorMessage = {
          type: 'system',
          content: `Mic: ${transcribeResult.error}`,
          timestamp: new Date()
        };
        setConversation(prev => [...prev, errorMessage]);
        
        // Show suggestions if available
        if (transcribeResult.suggestions) {
          const suggestionText = "Suggestions:\n" + transcribeResult.suggestions.map(s => `• ${s}`).join('\n');
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
        speakTextWithSettings(result.response);
      }
      
    } catch (error) {
      console.error('AI chat error:', error);
      addMessage('system', 'AI assistant error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Text-to-Speech using server-side TTS first, fallback to browser
  const speakText = async (text, language = 'en') => {
    if (isMuted || !text || isPlaying) return; // Don't play if already playing
    
    // Stop any current audio
    stopSpeaking();
    
    try {
      // Try enhanced Chatterbox TTS first
      console.log('Attempting Chatterbox TTS...');
      const chatterboxResponse = await fetch('/api/synthesize-chatterbox', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          text,
          language
        })
      });
      
      if (chatterboxResponse.ok) {
        console.log('Using Chatterbox TTS');
        const audioBlob = await chatterboxResponse.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        
        // Store reference to current audio
        currentAudioRef.current = audio;
        
        // Check for watermark info
        const watermarkScore = chatterboxResponse.headers.get('X-Watermark-Score');
        const ttsEngine = chatterboxResponse.headers.get('X-TTS-Engine');
        
        if (watermarkScore) {
          console.log(`Watermark detected: ${watermarkScore} (Engine: ${ttsEngine})`);
        }
        
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
        return; // Success, exit early
      }
      
      // Fallback to Google Cloud TTS
      console.log('Warning: Chatterbox TTS unavailable, trying Google Cloud TTS...');
      console.log('Using language:', language);
      const response = await fetch('/api/synthesize-speech', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          text,
          language: language || 'en-US'
        })
      });
      
      if (response.ok) {
        console.log('Success: Using Google Cloud TTS');
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
        // Final fallback to browser speech synthesis
        console.log('Warning: Server TTS unavailable, using browser TTS...');
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

  // Add message to conversation with deduplication
  const addMessage = (type, content) => {
    // Prevent duplicate messages within 2 seconds
    const messageKey = `${type}:${content}`;
    if (lastMessageContentRef.current === messageKey) {
      console.log('Preventing duplicate message:', content);
      return;
    }
    
    lastMessageContentRef.current = messageKey;
    
    // Clear the deduplication after 2 seconds
    setTimeout(() => {
      if (lastMessageContentRef.current === messageKey) {
        lastMessageContentRef.current = '';
      }
    }, 2000);
    
    const message = {
      type,
      content,
      timestamp: new Date()
    };
    setConversation(prev => [...prev, message]);
  };

  // Handle project generation
  const handleProjectGeneration = async (projectSpec) => {
    addMessage('system', 'Starting project generation...');
    
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
        addMessage('system', `Success: Project "${projectName}" generated successfully!`);
        
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
        addMessage('system', `Error: Project generation failed: ${result.error || 'Unknown error'}`);
      }
      
    } catch (error) {
      console.error('Project generation error:', error);
      addMessage('system', 'Error: Failed to generate project. Please try again.');
    }
  };

  // Manual text input for fallback
  const [textInput, setTextInput] = useState('');
  const [audioDevices, setAudioDevices] = useState([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState('');
  const [audioStoppedMessage, setAudioStoppedMessage] = useState('');
  
  // Enhanced TTS state
  const [ttsLanguage, setTtsLanguage] = useState('en-US');
  const [ttsEngine, setTtsEngine] = useState('google'); // Default to google since chatterbox is unavailable
  const [supportedLanguages, setSupportedLanguages] = useState([]);
  const [showTTSSettings, setShowTTSSettings] = useState(false);
  const [voiceCloneFile, setVoiceCloneFile] = useState(null);
  const [isVoiceCloning, setIsVoiceCloning] = useState(false);
  const voiceCloneInputRef = useRef(null);
  
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

  // Load supported TTS languages
  useEffect(() => {
    const loadSupportedLanguages = async () => {
      try {
        const response = await fetch('/api/supported-languages');
        if (response.ok) {
          const data = await response.json();
          console.log('Success: Supported TTS languages loaded:', data);
          
          // Check if Chatterbox is available
          const isChatterboxAvailable = data.available_engines?.chatterbox || false;
          const isGoogleAvailable = data.available_engines?.google_cloud || false;
          
          // Set appropriate engine based on availability
          if (!isChatterboxAvailable && isGoogleAvailable) {
            setTtsEngine('google');
            // Only show message once per session
            if (sessionStorage.getItem('tts-engine-notice') !== 'shown') {
              addMessage('system', 'Warning: Chatterbox TTS unavailable. Using Google Cloud TTS.');
              sessionStorage.setItem('tts-engine-notice', 'shown');
            }
          }
          
          // Use Google Cloud languages as they are available
          const googleLanguages = data.supported_languages?.google_cloud || [];
          const chatterboxLanguages = data.supported_languages?.chatterbox || [];
          
          // Convert to proper format
          const allLanguages = [
            ...googleLanguages.map(code => ({
              code: code,
              name: getLanguageName(code),
              engine: 'google'
            })),
            ...chatterboxLanguages.map(code => ({
              code: code,
              name: getLanguageName(code),
              engine: 'chatterbox'
            }))
          ];
          
          const finalLanguages = allLanguages.length > 0 ? allLanguages : [
            { code: 'en-US', name: 'English (US)', engine: 'google' },
            { code: 'en-GB', name: 'English (UK)', engine: 'google' },
            { code: 'es-ES', name: 'Spanish (Spain)', engine: 'google' },
            { code: 'fr-FR', name: 'French (France)', engine: 'google' },
            { code: 'de-DE', name: 'German (Germany)', engine: 'google' }
          ];
          
          setSupportedLanguages(finalLanguages);
          
          // Set default language to first available language
          if (finalLanguages.length > 0 && ttsLanguage === 'en-US') {
            setTtsLanguage(finalLanguages[0].code);
          }
        }
      } catch (error) {
        console.error('Warning: Failed to load supported languages:', error);
        // Fallback to common languages
        setSupportedLanguages([
          { code: 'en-US', name: 'English (US)', engine: 'google' },
          { code: 'en-GB', name: 'English (UK)', engine: 'google' },
          { code: 'es-ES', name: 'Spanish (Spain)', engine: 'google' },
          { code: 'fr-FR', name: 'French (France)', engine: 'google' },
          { code: 'de-DE', name: 'German (Germany)', engine: 'google' }
        ]);
        setTtsEngine('google'); // Default to Google if loading fails
      }
    };
    
    // Helper function to get language names
    const getLanguageName = (code) => {
      const languageNames = {
        'en-US': 'English (US)',
        'en-GB': 'English (UK)', 
        'es-ES': 'Spanish (Spain)',
        'fr-FR': 'French (France)',
        'de-DE': 'German (Germany)',
        'en': 'English',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'zh': 'Chinese',
        'ja': 'Japanese'
      };
      return languageNames[code] || code;
    };
    
    loadSupportedLanguages();
  }, []);

  // Handle voice cloning
  const handleVoiceClone = async (text) => {
    if (!voiceCloneFile) {
      addMessage('system', 'Warning: Please select a reference audio file for voice cloning.');
      return;
    }

    setIsVoiceCloning(true);
    
    try {
      const formData = new FormData();
      formData.append('text', text);
      formData.append('reference_audio', voiceCloneFile);
      
      const response = await fetch('/api/voice-clone', {
        method: 'POST',
        body: formData
      });
      
      if (response.ok) {
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        
        currentAudioRef.current = audio;
        setIsPlaying(true);
        
        audio.onended = () => {
          setIsPlaying(false);
          currentAudioRef.current = null;
          URL.revokeObjectURL(audioUrl);
        };
        
        audio.onerror = () => {
          setIsPlaying(false);
          currentAudioRef.current = null;
          URL.revokeObjectURL(audioUrl);
          addMessage('system', 'Error: Voice cloning playback failed.');
        };
        
        await audio.play();
        addMessage('system', 'Voice cloning successful! Playing cloned voice...');
        
      } else {
        addMessage('system', 'Error: Voice cloning failed. Please try again.');
      }
    } catch (error) {
      console.error('Voice cloning error:', error);
      addMessage('system', 'Error: Voice cloning error. Please try again.');
    } finally {
      setIsVoiceCloning(false);
    }
  };

  // Enhanced TTS with language and engine selection
  const speakTextWithSettings = async (text) => {
    if (voiceCloneFile && ttsEngine === 'chatterbox') {
      await handleVoiceClone(text);
    } else {
      await speakText(text, ttsLanguage);
    }
  };

  const testTTSSettings = async () => {
    const engineName = ttsEngine === 'chatterbox' ? 'Chatterbox TTS' : 'Google Cloud TTS';
    const languageName = supportedLanguages.find(lang => lang.code === ttsLanguage)?.name || ttsLanguage;
    
    let testText = `Hello! I'm testing the ${engineName} engine with ${languageName} voice.`;
    
    if (voiceCloneFile && ttsEngine === 'chatterbox') {
      testText += ` This should sound like the uploaded voice sample.`;
    } else {
      testText += ` Listen to how this voice sounds different from others.`;
    }
    
    addMessage('system', `Testing: ${engineName} - ${languageName}${voiceCloneFile ? ' (Voice Cloned)' : ''}`);
    console.log('Testing TTS:', { engine: ttsEngine, language: ttsLanguage, hasVoiceClone: !!voiceCloneFile });
    
    await speakTextWithSettings(testText);
  };
  
  const sendTextMessage = () => {
    if (!textInput.trim() || isLoading) return;
    
    addMessage('user', textInput);

    // Handle AI based on the current mode
    switch (currentMode) {
      case 'voice':
        sendToAI(textInput);
        break;
      case 'scan_website':
        sendToAI(`Scanning website: ${textInput}`);
        break;
      case 'scan_repo':
        sendToAI(`Scanning repository: ${textInput}`);
        break;
      case 'deploy':
        sendToAI(`Starting deployment for: ${textInput}`);
        break;
      default:
        sendToAI(textInput);
    }
    
    setTextInput('');
  };

  // Helper to get placeholder text for the current mode
  const getPlaceholder = () => {
    switch (currentMode) {
      case 'voice':
        return 'Ask Xverta to create a landing page...';
      case 'scan_website':
        return 'Enter a website URL to scan...';
      case 'scan_repo':
        return 'Enter a GitHub repository URL to scan...';
      case 'deploy':
        return 'Enter a project name to deploy...';
      default:
        return 'Ask me anything...';
    }
  };

  // Test microphone function
  const testMicrophone = async () => {
    try {
      addMessage('system', 'Testing microphone... Say something!');
      
      // Test basic microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: { 
          deviceId: selectedDeviceId ? { exact: selectedDeviceId } : undefined,
          sampleRate: 48000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } 
      });
      
      // Test speech recognition
      if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const testRecognition = new SpeechRecognition();
        
        testRecognition.continuous = false;
        testRecognition.interimResults = false;
        testRecognition.lang = 'en-US';
        
        testRecognition.onresult = (event) => {
          const transcript = event.results[0][0].transcript;
          addMessage('system', `Microphone test successful! I heard: "${transcript}"`);
          stream.getTracks().forEach(track => track.stop());
        };
        
        testRecognition.onerror = (event) => {
          if (event.error === 'network') {
            addMessage('system', `Web Speech API network error. This is a Chrome/Google service issue. Solution: Use manual recording (click orb) or try Firefox browser.`);
          } else {
            addMessage('system', `Speech recognition test failed: ${event.error}`);
          }
          stream.getTracks().forEach(track => track.stop());
        };
        
        testRecognition.onend = () => {
          stream.getTracks().forEach(track => track.stop());
        };
        
        testRecognition.start();
        
        // Auto-stop after 10 seconds
        setTimeout(() => {
          testRecognition.stop();
          if (stream) {
            stream.getTracks().forEach(track => track.stop());
          }
        }, 10000);
        
      } else {
        addMessage('system', 'Speech recognition not supported in this browser');
        stream.getTracks().forEach(track => track.stop());
      }
      
    } catch (error) {
      console.error('Microphone test failed:', error);
      addMessage('system', `Microphone test failed: ${error.message}`);
    }
  };

return (

    <PageWrapper>
      <div className="voice-chat-page">
        {/* --- Floating Settings Panel (remains hidden) --- */}
        <div className={`floating-settings ${showTTSSettings ? 'visible' : ''}`}>
          <div className="settings-panel">
            <div className="settings-header">
              <h3>Voice Settings</h3>
              <button
                onClick={() => setShowTTSSettings(false)}
                className="close-settings-btn"
              >
                <X size={18} />
              </button>
            </div>
            {/* (Settings content goes here...) */}
          </div>
        </div>

        {/* --- Desktop App Container --- */}
        <div className="desktop-app-container">
          {/* Main Content Area (Full Width) */}
          <div className="main-content-area">
            {/* NEW: Hero/Chat Block - Top Section */}
            <div className="hero-chat-block">
              {/* Hero Heading */}
              <div className="hero-heading-section">
                <h1 className="hero-main-title">Build applications with XVERTA</h1>
                <p className="hero-subtitle">Create, iterate, and launch your next application by talking with XVERTA.</p>
              </div>

              <div className="centered-content-block">
                {/* NEW: Top Chatbox Component */}
                <div className="top-chatbox-component">
                {/* Chat Messages Display Area */}
                <div className="chatbox-messages-area">
                  <div ref={chatContainerRef} className="conversation-messages">
                    {conversation.map((message, index) => (
                      <div key={index} className={`message ${message.type} fade-in`}>
                        {message.type === 'ai' && <div className="ai-avatar"></div>}
                        <div className={`message-bubble`}>
                          <div className="whitespace-pre-wrap">{message.content}</div>
                          <div className="message-time">
                            {message.timestamp.toLocaleTimeString([], {
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </div>
                        </div>
                      </div>
                    ))}

                    {/* Show suggestion chips only when conversation has just the welcome message */}
                    {conversation.length === 1 && conversation[0].type === 'ai' && (
                      <div className="suggestion-chips-container fade-in">
                        {suggestionChips.map((chip, index) => (
                          <button
                            key={index}
                            className="suggestion-chip"
                            onClick={() => handleSuggestionClick(chip.prompt)}
                            disabled={isLoading}
                          >
                            <span className="chip-text">{chip.text}</span>
                          </button>
                        ))}
                      </div>
                    )}

                    {isLoading && (
                      <div className="loading-indicator fade-in">
                        <Loader size={16} className="animate-spin" />
                        <span>AI is thinking...</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Chat Input Bar */}
                <div className="chatbox-input-bar">
                  <div className="main-input-controls">
                    {/* Mic Button (left side - always visible) */}
                    <button
                      className={`unified-mic-btn ${
                        isRecording || isListening ? 'recording' : ''
                      }`}
                      onClick={isRecording ? stopRecording : startRecording}
                      title={isRecording ? 'Stop Recording' : 'Start Recording'}
                    >
                      {isRecording ? <Square size={18} /> : <Mic size={18} />}
                    </button>

                    {/* Text Input (adapts to mode) */}
                    <div className="hero-text-input-container">
                      <input
                        type="text"
                        value={textInput}
                        onChange={(e) => setTextInput(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && sendTextMessage()}
                        placeholder={getPlaceholder()}
                        className="hero-text-input"
                        disabled={isLoading}
                      />
                      <button
                        onClick={sendTextMessage}
                        disabled={!textInput.trim() || isLoading}
                        className="hero-send-btn"
                        title="Send Message"
                      >
                        <ArrowRight size={16} />
                      </button>
                    </div>

                    {/* Settings and Audio Controls */}
                    <div className="input-side-controls">
                      <button
                        className={`side-control-btn ${showTTSSettings ? 'active' : ''}`}
                        onClick={() => setShowTTSSettings(!showTTSSettings)}
                        title="Voice Settings"
                      >
                        <Settings size={18} />
                      </button>
                      <button
                        className={`side-control-btn ${isMuted ? 'active' : ''}`}
                        onClick={() => setIsMuted(!isMuted)}
                        title={isMuted ? 'Unmute Audio' : 'Mute Audio'}
                      >
                        {isMuted ? <VolumeX size={18} /> : <Volume2 size={18} />}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              </div>
            </div>

            {/* NEW: Project Block - Below Hero Section */}
            <div className="project-block">
              <div className="project-block-inner">
                <div className="below-chatbox-content">
                {projectHistory && projectHistory.length > 0 && (
                  <div className="jump-back-in-section">
                    {/* Interactive Header Bar */}
                    <div className="jump-back-in-header">
                      <h2 className="empty-state-section-title">Jump Right Back In</h2>
                      
                      <div className="jump-back-in-controls">
                        {/* Search Bar */}
                        <div className="project-search-container">
                          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="search-icon">
                            <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.5"/>
                            <path d="M11 11L14 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                          </svg>
                          <input 
                            type="text" 
                            placeholder="Search projects..."
                            className="project-search-input"
                          />
                        </div>
                        
                        {/* Filter/Sort Dropdown */}
                        <select className="project-sort-select">
                          <option value="recent">Last edited</option>
                          <option value="name">Name (A-Z)</option>
                          <option value="oldest">Oldest first</option>
                        </select>
                        
                        {/* View All Button */}
                        <button className="view-all-btn">
                          View All
                          <ArrowRight size={14} />
                        </button>
                      </div>
                    </div>
                    
                    <div className="project-cards-grid">
                      {projectHistory.slice(0, 6).map((project, index) => (
                        <div key={project.slug || index} className="project-card">
                          <div className="project-card-header">
                            <div className="project-card-info">
                              <h4 className="project-card-name">{project.name || 'Unnamed Project'}</h4>
                              <p className="project-card-meta">
                                Edited {project.created_date ? formatTimeAgo(new Date(project.created_date * 1000).toISOString()) : 'recently'}
                              </p>
                            </div>
                          </div>
                          
                          {/* Live Preview Container */}
                          <div className="project-card-preview">
                            <iframe
                              src={`/api/sandbox-preview/${project.slug}`}
                              title={`Preview of ${project.name}`}
                              className="project-preview-iframe"
                              sandbox="allow-scripts allow-same-origin"
                              scrolling="no"
                            />
                          </div>
                          
                          <div className="project-card-actions">
                            <button 
                              className="project-card-btn primary"
                              onClick={() => handleEditProject(project)}
                            >
                              Open Project
                            </button>
                            <button 
                              className="project-card-btn"
                              onClick={() => handlePreviewProject(project)}
                            >
                              Preview
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}


              </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </PageWrapper>
  );
};export default VoiceChatInterface;
