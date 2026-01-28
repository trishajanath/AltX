import React from 'react';
import { useNavigate } from 'react-router-dom';

const ChatOption = ({ userId }) => {
  const navigate = useNavigate();

  const handleTextClick = () => {
    navigate(`/chat/${userId}`);
  };

  return (
    <div className="flex justify-center items-center h-screen">
      <button
        className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
        onClick={handleTextClick}
      >
        Text Them!
      </button>
    </div>
  );
};

export default ChatOption;