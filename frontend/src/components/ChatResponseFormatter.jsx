import React from 'react';

// A robust function to parse a line of text for markdown (bold, code).
const parseInlineMarkdown = (line) => {
    // Regex to find **bold** or `code` segments.
    const regex = /(\*\*.*?\*\*|\`.*?\`)/g;
    const parts = line.split(regex);

    return parts.map((part, index) => {
        // Handle **bold** text
        if (part.startsWith('**') && part.endsWith('**')) {
            return <strong key={index}>{part.slice(2, -2)}</strong>;
        }
        // Handle `code` text
        if (part.startsWith('`') && part.endsWith('`')) {
            // The <code> tag is styled in the parent ReportPage.jsx
            return <code key={index}>{part.slice(1, -1)}</code>;
        }
        // Handle plain text
        return part;
    });
};

const ChatResponseFormatter = ({ message }) => {
    if (!message) return null;

    // A more structured approach to render markdown content.
    const renderFormattedMessage = () => {
        const blocks = [];
        const lines = message.split('\n');
        let currentList = [];

        lines.forEach((line, index) => {
            const trimmedLine = line.trim();

            // Check for bullet points (starting with '-' or '•')
            if (trimmedLine.startsWith('- ') || trimmedLine.startsWith('• ')) {
                // Add the content of the list item, parsing it for bold/code.
                currentList.push(
                    <li key={index}>
                        {parseInlineMarkdown(trimmedLine.substring(2))}
                    </li>
                );
            } else {
                // If we were building a list, push it to blocks and reset.
                if (currentList.length > 0) {
                    blocks.push(<ul key={`ul-${index}`}>{currentList}</ul>);
                    currentList = [];
                }
                // Handle regular paragraphs (non-empty lines).
                if (trimmedLine) {
                    blocks.push(
                        <p key={index}>
                            {parseInlineMarkdown(trimmedLine)}
                        </p>
                    );
                }
            }
        });

        // If the message ends with a list, make sure to add it.
        if (currentList.length > 0) {
            blocks.push(<ul key={`ul-final`}>{currentList}</ul>);
        }

        return blocks;
    };

    // The main container div's className should be set by the parent
    // (e.g., className="chat-message ai-message").
    // All styling is now inherited from the parent's stylesheet.
    return (
        <div className="formatted-content">
            {renderFormattedMessage()}
        </div>
    );
};

export default ChatResponseFormatter;