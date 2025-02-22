import React, { useState } from 'react';
import RichTextEditor from '../components/RichTextEditor';

const YourPage = () => {
  const [content, setContent] = useState('');

  const handleChange = (value) => {
    setContent(value);
  };

  return (
    <div className="container mx-auto p-4">
      <h1>Rich Text Editor</h1>
      <RichTextEditor 
        value={content} 
        onChange={handleChange}
      />
      
      {/* If you need to see the HTML content */}
      <div className="mt-4">
        <h2>Output:</h2>
        <div dangerouslySetInnerHTML={{ __html: content }} />
      </div>
    </div>
  );
};

export default YourPage; 