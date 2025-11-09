import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Volume2, VolumeX, MessageCircle, Loader, Play, Square, Settings, BrainCircuit, ArrowRight } from 'lucide-react';
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
  
  // Real-time conversation states
  const [isRealTimeMode, setIsRealTimeMode] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [realTimeTranscript, setRealTimeTranscript] = useState('');
  const [voiceActivityTimer, setVoiceActivityTimer] = useState(null);
  const [silenceTimer, setSilenceTimer] = useState(null);
  const [speechAPIFailures, setSpeechAPIFailures] = useState(0);
  
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

  // Initialize with greeting
  useEffect(() => {
    const greeting = {
      type: 'ai',
      content: "Hello! I'm your coding buddy and I'm very excited to help you build something. What idea do you have in mind?",
      timestamp: new Date()
    };
    setConversation([greeting]);
    
    // Speak the greeting only once with proper language
    const timer = setTimeout(() => {
      if (!isMuted) {
        speakText(greeting.content, 'en-US');
      }
    }, 1500); // Longer delay to ensure TTS settings are loaded
    
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
    if (textInput.trim()) {
      addMessage('user', textInput);
      sendToAI(textInput);
      setTextInput('');
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
          addMessage('system', `✅ Microphone test successful! I heard: "${transcript}"`);
          stream.getTracks().forEach(track => track.stop());
        };
        
        testRecognition.onerror = (event) => {
          if (event.error === 'network') {
            addMessage('system', `❌ Web Speech API network error. This is a Chrome/Google service issue. Solution: Use manual recording (click orb) or try Firefox browser.`);
          } else {
            addMessage('system', `❌ Speech recognition test failed: ${event.error}`);
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
        addMessage('system', '⚠️ Speech recognition not supported in this browser');
        stream.getTracks().forEach(track => track.stop());
      }
      
    } catch (error) {
      console.error('Microphone test failed:', error);
      addMessage('system', `❌ Microphone test failed: ${error.message}`);
    }
  };

return (
    <PageWrapper>
      <style>{`
        :root {
          --bg-black: #000000;
          --card-bg: #1a1a1a;
          --card-border: #333333;
          --text-primary: #ffffff;
          --text-secondary: #aaaaaa;
          --accent: #ffffff;
          --accent-text: #000000; /* NEW: For text on white buttons */
          --danger-text: #ef4444;
          --danger-bg: rgba(239, 68, 68, 0.1);
          --danger-border: rgba(239, 68, 68, 0.3);
        }

        .voice-chat-page {
          background: var(--bg-black);
          color: var(--text-primary);
          min-height: 100vh;
          font-family: "Inter", sans-serif;
          position: relative;
        }

        /* Lovable-Inspired Single-Focus Layout */
        .lovable-layout {
          height: 100vh;
          position: relative;
          overflow: hidden;
        }

        .magical-chat-container {
          height: 100vh;
          display: flex;
          flex-direction: column;
          max-width: 1200px;
          margin: 0 auto;
          padding: 0 2rem;
          position: relative;
          z-index: 1;
        }

        /* Chat Messages Section - Top Half */
        .chat-messages-section {
          flex: 1;
          display: flex;
          flex-direction: column;
          justify-content: flex-end;
          padding: 2rem 0;
          min-height: 0;
        }

        .conversation-messages {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
          overflow-y: auto;
          padding: 1rem;
          background: rgba(0, 0, 0, 0.3);
          backdrop-filter: blur(20px);
          border-radius: 20px;
          border: 1px solid rgba(255, 255, 255, 0.1);
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
          max-height: 60vh;
          scrollbar-width: none;
        }

        .conversation-messages::-webkit-scrollbar {
          display: none;
        }

        /* Hero Input Section - Bottom Half */
        .hero-input-section {
          flex-shrink: 0;
          padding: 2rem 0;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 2rem;
        }

        /* Suggested Prompts */
        .suggested-prompts {
          width: 100%;
          max-width: 800px;
        }

        .prompt-suggestions {
          display: flex;
          flex-wrap: wrap;
          gap: 0.75rem;
          justify-content: center;
          margin-bottom: 1rem;
        }

        .suggestion-pill {
          background: rgba(255, 255, 255, 0.1);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.2);
          border-radius: 25px;
          padding: 0.75rem 1.5rem;
          color: var(--text-primary);
          font-size: 0.875rem;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.3s ease;
          white-space: nowrap;
        }

        .suggestion-pill:hover {
          background: rgba(255, 255, 255, 0.2);
          border-color: rgba(255, 255, 255, 0.4);
          transform: translateY(-2px);
        }

        /* Main Input Controls */
        .main-input-controls {
          display: flex;
          align-items: center;
          gap: 2rem;
          width: 100%;
          max-width: 800px;
        }

        /* Hero Voice Orb */
        .hero-orb-container {
          flex-shrink: 0;
        }

        .hero-voice-orb {
          position: relative;
          width: 80px;
          height: 80px;
          cursor: pointer;
          transition: all 0.4s ease;
        }

        .hero-voice-orb:hover {
          transform: scale(1.1);
        }

        .hero-orb-outer {
          position: absolute;
          inset: 0;
          border-radius: 50%;
          background: conic-gradient(from 180deg at 50% 50%, #ffffff 0%, #888888 50%, #ffffff 100%);
          animation: spin 15s linear infinite;
          filter: blur(12px);
          opacity: 0.8;
        }

        .hero-orb-inner {
          position: absolute;
          inset: 6px;
          background: rgba(0, 0, 0, 0.8);
          backdrop-filter: blur(20px);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          border: 2px solid rgba(255, 255, 255, 0.3);
          transition: all 0.4s ease;
        }

        .hero-voice-orb.recording .hero-orb-outer {
          animation: pulse 1.5s infinite, spin 15s linear infinite;
          background: conic-gradient(from 180deg at 50% 50%, #ff4444 0%, #ff6666 50%, #ff4444 100%);
          opacity: 1;
        }

        .hero-voice-orb.recording .hero-orb-inner {
          background: rgba(255, 68, 68, 0.3);
        }

        /* Hero Text Input */
        .hero-text-input-container {
          flex: 1;
          position: relative;
        }

        .hero-text-input {
          width: 100%;
          background: rgba(255, 255, 255, 0.1);
          backdrop-filter: blur(20px);
          border: 2px solid rgba(255, 255, 255, 0.2);
          border-radius: 25px;
          padding: 1.25rem 4rem 1.25rem 2rem;
          color: var(--text-primary);
          font-size: 1.125rem;
          font-weight: 500;
          outline: none;
          transition: all 0.3s ease;
        }

        .hero-text-input:focus {
          border-color: rgba(255, 255, 255, 0.5);
          background: rgba(255, 255, 255, 0.15);
          box-shadow: 0 0 30px rgba(255, 255, 255, 0.1);
        }

        .hero-text-input::placeholder {
          color: rgba(255, 255, 255, 0.6);
          font-weight: 400;
        }

        .hero-send-btn {
          position: absolute;
          right: 0.5rem;
          top: 50%;
          transform: translateY(-50%);
          background: var(--accent);
          border: none;
          border-radius: 50%;
          width: 50px;
          height: 50px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: var(--accent-text);
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .hero-send-btn:hover {
          transform: translateY(-50%) scale(1.1);
          box-shadow: 0 8px 25px rgba(255, 255, 255, 0.3);
        }

        /* Status and Controls */
        .status-controls {
          display: flex;
          justify-content: space-between;
          align-items: center;
          width: 100%;
          max-width: 800px;
        }

        .chat-status {
          font-size: 0.875rem;
          color: var(--text-secondary);
          font-weight: 500;
        }

        .chat-status .listening {
          color: var(--accent);
          font-weight: 600;
        }

        .floating-controls {
          display: flex;
          gap: 0.75rem;
        }

        .floating-btn {
          background: rgba(255, 255, 255, 0.1);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.2);
          border-radius: 50%;
          width: 44px;
          height: 44px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: var(--text-secondary);
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .floating-btn:hover {
          background: rgba(255, 255, 255, 0.2);
          color: var(--text-primary);
          transform: translateY(-2px);
        }

        .floating-btn.active {
          background: var(--accent);
          border-color: var(--accent);
          color: var(--accent-text);
        }

        /* Floating Settings Panel */
        .floating-settings {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.8);
          backdrop-filter: blur(10px);
          z-index: 1000;
          display: flex;
          align-items: center;
          justify-content: center;
          opacity: 0;
          pointer-events: none;
          transition: all 0.3s ease;
        }

        .floating-settings.visible {
          opacity: 1;
          pointer-events: all;
        }

        .settings-glass-panel {
          background: rgba(0, 0, 0, 0.9);
          backdrop-filter: blur(20px);
          border: 1px solid rgba(255, 255, 255, 0.2);
          border-radius: 20px;
          padding: 2rem;
          max-width: 500px;
          width: 90%;
          max-height: 80vh;
          overflow-y: auto;
        }

        .settings-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1.5rem;
        }

        .settings-header h3 {
          margin: 0;
          font-size: 1.25rem;
          font-weight: 600;
          color: var(--text-primary);
        }

        .close-settings-btn {
          background: rgba(255, 255, 255, 0.1);
          border: 1px solid rgba(255, 255, 255, 0.2);
          border-radius: 50%;
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: var(--text-secondary);
          cursor: pointer;
          font-size: 1.25rem;
          transition: all 0.2s ease;
        }

        .close-settings-btn:hover {
          background: rgba(255, 255, 255, 0.2);
          color: var(--text-primary);
        }

        /* Remove old canvas styles - replaced with lovable layout */

        .tts-settings-panel {
          background: #111111;
          border-bottom: 1px solid var(--card-border);
          padding: 1.5rem;
          flex-shrink: 0;
        }

        .settings-section h4 {
          margin: 0 0 1.25rem 0;
          color: var(--text-primary);
          font-size: 1rem;
          font-weight: 600;
        }

        .setting-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 1rem;
          gap: 1.5rem;
        }

        .setting-row label {
          color: var(--text-secondary);
          font-size: 0.875rem;
          min-width: 100px;
          font-weight: 500;
        }

        .setting-select {
          background: var(--card-bg);
          border: 1px solid var(--card-border);
          border-radius: 0.375rem;
          color: var(--text-primary);
          padding: 0.5rem 0.75rem;
          font-size: 0.875rem;
          flex: 1;
        }

        .setting-select:focus {
          outline: none;
          border-color: var(--accent);
        }

        .voice-clone-section {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          flex: 1;
        }

        .voice-file-input {
          display: none;
        }

        .voice-file-label {
          background: var(--card-bg);
          border: 1px solid var(--card-border);
          border-radius: 0.375rem;
          color: var(--text-secondary);
          padding: 0.5rem 1rem;
          font-size: 0.875rem;
          cursor: pointer;
          transition: all 0.2s;
          text-align: center;
          flex: 1;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .voice-file-label:hover {
          background: #2a2a2a;
          color: var(--text-primary);
        }

        .clear-voice-btn {
          background: var(--danger-bg);
          border: 1px solid var(--danger-border);
          border-radius: 0.375rem;
          color: var(--danger-text);
          padding: 0.375rem 0.75rem;
          font-size: 0.8rem;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s;
        }

        .clear-voice-btn:hover {
          background: rgba(239, 68, 68, 0.2);
        }

        .test-tts-btn {
          background: var(--accent);
          border: 1px solid var(--accent);
          border-radius: 0.375rem;
          color: var(--accent-text);
          padding: 0.6rem 1rem;
          font-size: 0.875rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }

        .test-tts-btn:hover:not(:disabled) {
          background: transparent;
          color: var(--accent);
        }

        .test-tts-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .project-title {
          font-weight: 700;
          font-size: 1.125rem;
          color: var(--text-primary);
        }

        .canvas-content {
          flex: 1;
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }

        .conversation-display {
          flex: 1;
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }

        .conversation-header {
          padding: 1rem 1.5rem;
          border-bottom: 1px solid var(--card-border);
          display: flex;
          align-items: center;
          gap: 0.75rem;
          flex-shrink: 0;
        }

        .ai-avatar {
          width: 2rem;
          height: 2rem;
          border-radius: 50%;
          background: var(--accent);
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 700;
          font-size: 0.875rem;
          color: var(--accent-text);
          flex-shrink: 0;
        }

        .conversation-messages {
          flex: 1;
          overflow-y: auto;
          padding: 1.5rem 1.5rem 1rem 1.5rem;
          display: flex;
          flex-direction: column;
          gap: 1.25rem;
        }

        .message {
          display: flex;
          gap: 0.75rem;
          align-items: flex-start;
          max-width: 85%;
        }

        .message.user {
          justify-content: flex-end;
          align-self: flex-end;
        }
        
        .message.ai {
          align-self: flex-start;
        }

        .message.system {
          max-width: 100%;
          align-self: center;
        }

        .message.user .message-bubble {
          background: var(--accent);
          color: var(--accent-text);
          border-radius: 1.25rem 1.25rem 0.25rem 1.25rem;
        }

        .message.ai .message-bubble {
          background: var(--card-bg);
          color: var(--text-primary);
          border: 1px solid var(--card-border);
          border-radius: 1.25rem 1.25rem 1.25rem 0.25rem;
        }

        .message.system .message-bubble {
          background: transparent;
          color: var(--text-secondary);
          font-size: 0.8rem;
          text-align: center;
          border-radius: 1rem;
          margin: 0 auto;
          padding: 0.25rem 1rem;
        }

        .message-bubble {
          padding: 0.875rem 1.25rem;
          font-size: 0.9rem;
          line-height: 1.6;
          white-space: pre-wrap;
          max-width: 450px;
        }
        
        .message-bubble .whitespace-pre-wrap {
          white-space: pre-wrap;
        }

        .message-time {
          font-size: 0.75rem;
          opacity: 0.6;
          margin-top: 0.375rem;
        }
        
        .message.user .message-time {
          color: #333333;
        }

        /* --- UNIFIED CHAT LAYOUT: Seamless conversation-to-input flow --- */
        .unified-voice-controls {
          padding: 1rem 1.5rem 1.25rem 1.5rem;
          background: #0a0a0a;
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
          flex-shrink: 0;
          border-top: 1px solid rgba(51, 51, 51, 0.3);
        }

        .voice-orb-container {
          display: flex;
          justify-content: center;
          align-items: center;
          margin-bottom: 0rem;
        }

        .voice-orb {
          position: relative;
          width: 56px;
          height: 56px;
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
          background: conic-gradient(from 180deg at 50% 50%, #ffffff 0%, #aaaaaa 50%, #ffffff 100%);
          animation: spin 10s linear infinite;
          filter: blur(8px);
          opacity: 0.7;
          transition: all 0.3s ease;
        }

        .orb-inner {
          position: absolute;
          inset: 4px;
          background: #111111;
          border-radius: 50%;
          z-index: 10;
          display: flex;
          align-items: center;
          justify-content: center;
          border: 1px solid var(--card-border);
          transition: all 0.3s ease;
        }

        .orb-inner svg {
          width: 1.5rem;
          height: 1.5rem;
          color: var(--text-secondary);
          transition: color 0.3s ease;
        }
        
        .voice-orb:hover .orb-inner svg {
          color: var(--text-primary);
        }

        .voice-orb.recording .orb-outer {
          animation: pulse 1.5s infinite, spin 10s linear infinite;
          background: conic-gradient(from 180deg at 50% 50%, var(--danger-text) 0%, #dc2626 50%, var(--danger-text) 100%);
          opacity: 1;
        }
        
        .voice-orb.recording .orb-inner {
          background: var(--danger-bg);
          border-color: var(--danger-border);
        }

        .voice-orb.recording .orb-inner svg {
          color: var(--danger-text);
        }

        .text-input-container {
          position: relative;
          width: 100%;
          max-width: 100%;
          margin: 0.75rem 0 0 0;
        }

        .text-input {
          width: 100%;
          background: var(--card-bg);
          border: 1px solid var(--card-border);
          border-radius: 1.5rem;
          color: var(--text-primary);
          font-size: 0.95rem;
          padding: 0.875rem 3.5rem 0.875rem 1.25rem;
          transition: all 0.2s ease;
          font-family: "Inter", sans-serif;
        }

        .text-input:focus {
          outline: none;
          border-color: var(--accent);
          box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.1);
        }

        .text-input::placeholder {
          color: var(--text-secondary);
          opacity: 0.7;
        }

        .send-button {
          position: absolute;
          right: 0.5rem;
          top: 50%;
          transform: translateY(-50%);
          width: 2.25rem;
          height: 2.25rem;
          border-radius: 50%;
          background: var(--accent);
          border: none;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .send-button:hover:not(:disabled) {
          transform: translateY(-50%) scale(1.1);
          box-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
        }

        .send-button:disabled {
          opacity: 0.4;
          cursor: not-allowed;
        }

        .send-button svg {
          width: 1rem;
          height: 1rem;
          color: var(--accent-text);
        }

        /* --- Status text below orb --- */
        .chat-status-text {
          font-size: 0.75rem;
          color: var(--text-secondary);
          text-align: center;
          min-height: 1.5rem;
          display: flex;
          flex-direction: column;
          justify-content: center;
          line-height: 1.4;
        }

        .control-buttons {
          display: flex;
          gap: 0.5rem;
        }

        .control-btn {
          background: var(--card-bg);
          border: 1px solid var(--card-border);
          border-radius: 0.5rem;
          padding: 0.6rem;
          color: var(--text-secondary);
          cursor: pointer;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .control-btn:hover {
          background: #2a2a2a;
          color: var(--text-primary);
        }

        /* --- UPDATED: Active state is solid white --- */
        .control-btn.active {
          background: var(--accent);
          border-color: var(--accent);
          color: var(--accent-text);
        }

        .loading-indicator {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.75rem 1rem;
          background: var(--card-bg);
          border-radius: 1rem;
          color: var(--text-secondary);
          font-size: 0.875rem;
          align-self: flex-start;
          margin-left: 0.75rem;
        }

        /* --- NEW: Secondary Controls Grid --- */
        .secondary-controls-grid {
          display: grid;
          grid-template-columns: 1fr;
          gap: 1rem;
          width: 100%;
          max-width: 700px;
          margin: 0 auto;
        }
        
        @media (min-width: 640px) {
          .secondary-controls-grid {
            grid-template-columns: 1fr 1fr;
          }
        }

        .mic-selector-group, .project-history-group {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .mic-selector-group label, .project-history-group label {
          font-size: 0.8rem;
          font-weight: 600;
          color: var(--text-secondary);
        }
        
        .mic-selector-group select {
          width: 100%;
          background: var(--card-bg);
          border: 1px solid var(--card-border);
          border-radius: 0.5rem;
          color: var(--text-primary);
          font-size: 0.85rem;
          padding: 0.6rem;
          font-family: "Inter", sans-serif;
        }
        
        .project-history-group button {
          background: var(--card-bg);
          border: 1px solid var(--card-border);
          border-radius: 0.5rem;
          color: var(--text-secondary);
          font-size: 0.85rem;
          padding: 0.6rem;
          cursor: pointer;
          transition: all 0.2s ease;
          font-family: "Inter", sans-serif;
          font-weight: 500;
        }
        
        .project-history-group button:hover {
          background: #2a2a2a;
          color: var(--text-primary);
        }
        
        .project-history-panel {
          background: var(--bg-black);
          border: 1px solid var(--card-border);
          border-radius: 0.5rem;
          max-height: 200px;
          overflow-y: auto;
          width: 100%;
          max-width: 700px;
          margin: 0 auto;
        }
        
        .project-history-item {
          padding: 0.75rem 1rem;
          border-radius: 0.375rem;
          margin: 0.5rem;
          background: var(--card-bg);
          border: 1px solid var(--card-border);
          cursor: pointer;
          transition: all 0.2s ease;
        }
        
        .project-history-item:hover {
          background: #2a2a2a;
          border-color: #444444;
        }
        
        .project-history-item-name {
          font-size: 0.85rem; 
          font-weight: 600; 
          color: var(--text-primary);
          margin-bottom: 0.25rem;
        }
        
        .project-history-item-details {
          font-size: 0.75rem; 
          color: var(--text-secondary);
          margin-bottom: 0.6rem;
        }
        
        .project-history-item-actions {
          display: flex; 
          gap: 0.5rem;
        }
        
        .project-history-btn {
          background: rgba(255, 255, 255, 0.1);
          border: 1px solid var(--card-border);
          border-radius: 0.25rem;
          color: #ffffff;
          font-size: 0.75rem;
          padding: 0.25rem 0.6rem;
          cursor: pointer;
          transition: all 0.2s;
        }
        
        .project-history-btn:hover {
          background: rgba(255, 255, 255, 0.2);
        }

        .project-history-empty {
          padding: 1.5rem; 
          text-align: center; 
          color: var(--text-secondary);
          font-size: 0.85rem;
        }

        /* --- NEW: Footer Hint Text --- */
        .chat-footer-hint {
          font-size: 0.75rem;
          color: var(--text-secondary);
          text-align: center;
          margin-top: 0.5rem;
          line-height: 1.5;
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
        {/* Magical Single-Focus Layout */}
        <div className="lovable-layout">
          {/* Floating Settings Panel */}
          <div className={`floating-settings ${showTTSSettings ? 'visible' : ''}`}>
            <div className="settings-glass-panel">
              <div className="settings-header">
                <h3>Voice Settings</h3>
                <button
                  onClick={() => setShowTTSSettings(false)}
                  className="close-settings-btn"
                >
                  ×
                </button>
              </div>

              {/* TTS Settings Content */}
              <div className="settings-section">
                <div className="settings-section">
                  <h4>Text-to-Speech Settings</h4>
                  
                  <div className="setting-row">
                    <label>TTS Engine:</label>
                    <select 
                      value={ttsEngine} 
                      onChange={(e) => {
                        setTtsEngine(e.target.value);
                        if (e.target.value !== 'chatterbox') {
                          setVoiceCloneFile(null);
                        }
                      }}
                      className="setting-select"
                    >
                      <option value="chatterbox">Chatterbox TTS (Premium)</option>
                      <option value="google">Google Cloud TTS (High Quality)</option>
                    </select>
                  </div>

                  <div className="setting-row">
                    <label>Language/Voice:</label>
                    <select 
                      value={ttsLanguage} 
                      onChange={(e) => {
                        setTtsLanguage(e.target.value);
                        console.log('Voice changed to:', e.target.value);
                        addMessage('system', `Voice changed to: ${e.target.options[e.target.selectedIndex].text}`);
                      }}
                      className="setting-select"
                    >
                      {(supportedLanguages || []).map(lang => (
                        <option key={lang.code} value={lang.code}>
                          {lang.name} {lang.engine === 'chatterbox' ? '(Premium)' : ''}
                        </option>
                      ))}
                    </select>
                  </div>

                  {ttsEngine === 'chatterbox' && (
                    <div className="setting-row">
                      <label>Voice Cloning:</label>
                      <div className="voice-clone-section">
                        <input
                          type="file"
                          accept="audio/*"
                          onChange={(e) => setVoiceCloneFile(e.target.files[0])}
                          className="voice-file-input"
                          id="voice-clone-input"
                        />
                        <label htmlFor="voice-clone-input" className="voice-file-label">
                          {voiceCloneFile ? voiceCloneFile.name : 'Upload Voice Sample'}
                        </label>
                        {voiceCloneFile && (
                          <button 
                            onClick={() => setVoiceCloneFile(null)}
                            className="clear-voice-btn"
                          >
                            Clear
                          </button>
                        )}
                      </div>
                    </div>
                  )}

                  <div className="setting-row">
                    <div style={{ display: 'flex', gap: '0.5rem', flex: 1 }}>
                      <button 
                        onClick={testTTSSettings}
                        className="test-tts-btn"
                        disabled={isPlaying}
                        style={{ flex: 1 }}
                      >
                        {isPlaying ? 'Playing...' : 'Test Current Voice'}
                      </button>
                      <button 
                        onClick={async () => {
                          const quickTest = `This is ${supportedLanguages.find(lang => lang.code === ttsLanguage)?.name || ttsLanguage}`;
                          await speakText(quickTest, ttsLanguage);
                        }}
                        className="test-tts-btn"
                        disabled={isPlaying}
                        style={{ 
                          flex: 0, 
                          padding: '0.5rem',
                          background: 'var(--card-bg)',
                          borderColor: 'var(--card-border)',
                          color: 'var(--text-primary)'
                        }}
                        title="Quick voice preview"
                      >
                        Test
                      </button>
                    </div>
                  </div>

                  <div className="setting-row" style={{ flexDirection: 'column', alignItems: 'stretch', gap: '0.5rem' }}>
                    <label style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--text-secondary)' }}>Quick Voice Samples:</label>
                    <div style={{ display: 'flex', gap: '0.25rem', flexWrap: 'wrap' }}>
                      {[
                        { code: 'en-US', text: 'Hello from America!', flag: '(US)' },
                        { code: 'en-GB', text: 'Greetings from Britain!', flag: '(UK)' },
                        { code: 'es-ES', text: '¡Hola desde España!', flag: '(Spain)' },
                        { code: 'fr-FR', text: 'Bonjour de France!', flag: '(France)' },
                        { code: 'de-DE', text: 'Hallo aus Deutschland!', flag: '(Germany)' }
                      ].filter(sample => supportedLanguages.some(lang => lang.code === sample.code))
                      .map(sample => (
                        <button
                          key={sample.code}
                          onClick={async () => {
                            console.log(`Playing sample: ${sample.code} - "${sample.text}"`);
                            addMessage('system', `Playing ${sample.flag} ${sample.code}: "${sample.text}"`);
                            const originalLang = ttsLanguage;
                            await speakText(sample.text, sample.code);
                            setTimeout(() => {
                              addMessage('system', `Voice sample complete. Current setting: ${supportedLanguages.find(lang => lang.code === originalLang)?.name || originalLang}`);
                            }, 1000);
                          }}
                          disabled={isPlaying}
                          style={{
                            background: ttsLanguage === sample.code ? 'var(--accent)' : 'var(--card-bg)',
                            border: ttsLanguage === sample.code ? '1px solid var(--accent)' : '1px solid var(--card-border)',
                            borderRadius: '0.25rem',
                            color: ttsLanguage === sample.code ? 'var(--accent-text)' : 'var(--text-secondary)',
                            fontSize: '0.75rem',
                            padding: '0.375rem 0.6rem',
                            cursor: 'pointer',
                            transition: 'all 0.2s',
                            fontWeight: ttsLanguage === sample.code ? '600' : '400',
                          }}
                          title={`Test ${sample.code} voice ${ttsLanguage === sample.code ? '(Current)' : ''}`}
                        >
                          {sample.flag} {sample.code.split('-')[0].toUpperCase()}
                          {ttsLanguage === sample.code && ' ✓'}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Single-Focus Chat Interface */}
          <div className="magical-chat-container">
            {/* Chat Messages - Top Half */}
            <div className="chat-messages-section">
              <div ref={chatContainerRef} className="conversation-messages">
                {conversation.map((message, index) => (
                  <div key={index} className={`message ${message.type}`}>
                    {message.type === 'ai' && (
                      <div className="ai-avatar">✨</div>
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

            {/* Hero Input Section - Bottom Half */}
            <div className="hero-input-section">
              {/* Suggested Prompts */}
              <div className="suggested-prompts">
                <div className="prompt-suggestions">
                  <button
                    onClick={() => {
                      setTextInput("Create a modern e-commerce website");
                      addMessage('user', "Create a modern e-commerce website");
                      sendToAI("Create a modern e-commerce website");
                      setTextInput('');
                    }}
                    className="suggestion-pill"
                  >
                    Create e-commerce site
                  </button>
                  <button
                    onClick={() => {
                      setTextInput("Build a social media dashboard");
                      addMessage('user', "Build a social media dashboard");
                      sendToAI("Build a social media dashboard");
                      setTextInput('');
                    }}
                    className="suggestion-pill"
                  >
                    Social media dashboard
                  </button>
                  <button
                    onClick={() => {
                      setTextInput("Deploy my project to production");
                      addMessage('user', "Deploy my project to production");
                      sendToAI("Deploy my project to production");
                      setTextInput('');
                    }}
                    className="suggestion-pill"
                  >
                    Deploy project
                  </button>
                  <button
                    onClick={() => {
                      setTextInput("Run security scan on my code");
                      addMessage('user', "Run security scan on my code");
                      sendToAI("Run security scan on my code");
                      setTextInput('');
                    }}
                    className="suggestion-pill"
                  >
                    Security scan
                  </button>
                </div>
              </div>

              {/* Main Input Controls */}
              <div className="main-input-controls">
                {/* Voice Orb */}
                <div className="hero-orb-container">
                  <div 
                    className={`hero-voice-orb ${(isRecording || isListening) ? 'recording' : ''}`}
                    onClick={isRealTimeMode ? (isRecording ? stopRecording : startRecording) : (isRecording ? stopRecording : startRecording)}
                  >
                    <div className="hero-orb-outer"></div>
                    <div className="hero-orb-inner">
                      {isRealTimeMode ? (
                        isRecording ? <Square size={32} /> : (isListening ? <BrainCircuit size={32} /> : <Mic size={32} />)
                      ) : (
                        isRecording ? <Square size={32} /> : <Mic size={32} />
                      )}
                    </div>
                  </div>
                </div>

                {/* Text Input */}
                <div className="hero-text-input-container">
                  <input
                    type="text"
                    value={textInput}
                    onChange={(e) => setTextInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendTextMessage()}
                    placeholder="Ask Lovable to create a landing page for my startup..."
                    className="hero-text-input"
                    disabled={isLoading}
                  />
                  <button 
                    onClick={sendTextMessage}
                    disabled={!textInput.trim() || isLoading}
                    className="hero-send-btn"
                  >
                    <ArrowRight size={24} />
                  </button>
                </div>
              </div>

              {/* Status and Controls */}
              <div className="status-controls">
                <div className="chat-status">
                  {isRealTimeMode ? (
                    <span className={isListening ? 'listening' : ''}>
                      {speechAPIFailures >= 3 ? 'Manual mode (API unavailable)' :
                      isRecording ? 'Recording...' : (isListening ? '🎤 Listening...' : 'Voice mode active')}
                    </span>
                  ) : (
                    <span>
                      {isRecording && 'Recording...'}
                      {isPlaying && 'AI Speaking...'}
                      {audioStoppedMessage && audioStoppedMessage}
                      {!isRecording && !isPlaying && !audioStoppedMessage && 'Ready to create magic'}
                    </span>
                  )}
                </div>

                <div className="floating-controls">
                  <button
                    onClick={() => setIsMuted(!isMuted)}
                    className={`floating-btn ${isMuted ? 'active' : ''}`}
                    title={isMuted ? 'Enable audio' : 'Mute audio'}
                  >
                    {isMuted ? <VolumeX size={18} /> : <Volume2 size={18} />}
                  </button>
                  
                  <button
                    onClick={() => setShowTTSSettings(!showTTSSettings)}
                    className={`floating-btn ${showTTSSettings ? 'active' : ''}`}
                    title="Voice Settings"
                  >
                    <Settings size={18} />
                  </button>
                  
                  <button
                    onClick={toggleRealTimeMode}
                    className={`floating-btn ${isRealTimeMode ? 'active' : ''}`}
                    title="Real-time voice mode"
                  >
                    <BrainCircuit size={18} />
                  </button>

                  {isPlaying && (
                    <button
                      onClick={stopSpeaking}
                      className="floating-btn active"
                      title="Stop speaking"
                    >
                      <Square size={18} />
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </PageWrapper>
  );
};

export default VoiceChatInterface;