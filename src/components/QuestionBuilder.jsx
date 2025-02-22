import React, { useState } from 'react';
import RichTextEditor from './RichTextEditor';

const QuestionBuilder = () => {
  const [question, setQuestion] = useState('');
  const [options, setOptions] = useState(['', '', '', '']);

  return (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700">
          Question
        </label>
        <RichTextEditor 
          value={question}
          onChange={setQuestion}
        />
      </div>

      <div className="space-y-4">
        <label className="block text-sm font-medium text-gray-700">
          Options
        </label>
        {options.map((option, index) => (
          <div key={index}>
            <label className="block text-sm text-gray-600">
              Option {index + 1}
            </label>
            <RichTextEditor 
              value={option}
              onChange={(newValue) => {
                const newOptions = [...options];
                newOptions[index] = newValue;
                setOptions(newOptions);
              }}
            />
          </div>
        ))}
      </div>
    </div>
  );
};

export default QuestionBuilder; 