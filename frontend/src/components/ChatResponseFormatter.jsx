import React from 'react';

const ChatResponseFormatter = ({ message, type = 'ai' }) => {
  // Function to format the message with better readability
  const formatMessage = (text) => {
    if (!text) return '';
    
    // Split into sections based on headers
    const sections = text.split(/(?=^##?\s)/m);
    
    return sections.map((section, index) => {
      // Check if it's a header
      const headerMatch = section.match(/^(##?\s*)(.+)$/m);
      if (headerMatch) {
        const [, headerPrefix, headerText] = headerMatch;
        const isMainHeader = headerPrefix.startsWith('##');
        const isSubHeader = headerPrefix.startsWith('#');
        
        return (
          <div key={index} className={`chat-section ${isMainHeader ? 'main-header' : isSubHeader ? 'sub-header' : 'content'}`}>
            <h4 className="section-header" style={{ 
              color: isMainHeader ? '#00d4ff' : '#fafafa',
              fontSize: isMainHeader ? '18px' : '16px',
              marginBottom: '12px',
              marginTop: index > 0 ? '20px' : '0'
            }}>
              {headerText.trim()}
            </h4>
            {section.replace(/^##?\s*.+$/m, '').trim() && (
              <div className="section-content">
                {formatContent(section.replace(/^##?\s*.+$/m, '').trim())}
              </div>
            )}
          </div>
        );
      } else {
        return (
          <div key={index} className="chat-section content">
            <div className="section-content">
              {formatContent(section.trim())}
            </div>
          </div>
        );
      }
    });
  };

  // Function to format content with proper styling
  const formatContent = (content) => {
    if (!content) return null;
    
    // Split by lines and process each line
    const lines = content.split('\n');
    
    return lines.map((line, index) => {
      const trimmedLine = line.trim();
      if (!trimmedLine) return <br key={index} />;
      
      // Check for bullet points
      if (trimmedLine.startsWith('•') || trimmedLine.startsWith('-')) {
        return (
          <div key={index} className="bullet-point">
            <span className="bullet">•</span>
            <span className="bullet-text">{trimmedLine.substring(1).trim()}</span>
          </div>
        );
      }
      
      // Check for numbered lists
      const numberedMatch = trimmedLine.match(/^(\d+)\.\s(.+)$/);
      if (numberedMatch) {
        return (
          <div key={index} className="numbered-point">
            <span className="number">{numberedMatch[1]}.</span>
            <span className="numbered-text">{numberedMatch[2]}</span>
          </div>
        );
      }
      
      // Check for bold text
      if (trimmedLine.includes('**')) {
        const parts = trimmedLine.split(/(\*\*[^*]+\*\*)/g);
        return (
          <div key={index} className="formatted-line">
            {parts.map((part, partIndex) => {
              if (part.startsWith('**') && part.endsWith('**')) {
                return <strong key={partIndex} style={{ color: '#00d4ff' }}>{part.slice(2, -2)}</strong>;
              }
              return <span key={partIndex}>{part}</span>;
            })}
          </div>
        );
      }
      
      // Check for emojis and format them
      const emojiMatch = trimmedLine.match(/^([🚨⚠️✅❌🔒🛡️🔐🌐🎯⚡📂🔍📊💡🔧📝ℹ️]+)\s(.+)$/);
      if (emojiMatch) {
        return (
          <div key={index} className="emoji-line">
            <span className="emoji">{emojiMatch[1]}</span>
            <span className="emoji-text">{emojiMatch[2]}</span>
          </div>
        );
      }
      
      // Regular text
      return (
        <div key={index} className="regular-line">
          {trimmedLine}
        </div>
      );
    });
  };

  // Function to detect message type and apply appropriate styling
  const getMessageStyle = () => {
    if (type === 'user') {
      return {
        background: 'rgba(0, 212, 255, 0.1)',
        border: '1px solid rgba(0, 212, 255, 0.2)',
        padding: '16px',
        borderRadius: '12px',
        marginBottom: '16px'
      };
    } else {
      return {
        background: 'rgba(255, 255, 255, 0.05)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        padding: '20px',
        borderRadius: '12px',
        marginBottom: '16px',
        fontSize: '14px',
        lineHeight: '1.6'
      };
    }
  };

  return (
    <div className="chat-message" style={getMessageStyle()}>
      <div className="message-header" style={{ 
        color: type === 'user' ? '#00d4ff' : '#fafafa',
        fontWeight: '600',
        marginBottom: '12px',
        fontSize: '14px'
      }}>
        {type === 'user' ? '👤 You' : '🤖 AI Security Advisor'}
      </div>
      
      <div className="message-content">
        {formatMessage(message)}
      </div>
    </div>
  );
};

export default ChatResponseFormatter; 