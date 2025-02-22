import RichTextEditor from '../../components/RichTextEditor';

function AddQuestion() {
  // ... existing code ...

  return (
    <div>
      // ... existing code ...
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700">
          Pergunta
        </label>
        <RichTextEditor
          value={questionData.question}
          onChange={(content) => setQuestionData({...questionData, question: content})}
        />
      </div>

      <div className="space-y-4">
        {questionData.options.map((option, index) => (
          <div key={index}>
            <label className="block text-sm text-gray-600">
              Opção {index + 1}
            </label>
            <RichTextEditor
              value={option.text}
              onChange={(content) => {
                const newOptions = [...questionData.options];
                newOptions[index] = { ...newOptions[index], text: content };
                setQuestionData({ ...questionData, options: newOptions });
              }}
            />
          </div>
        ))}
      </div>
      // ... existing code ...
    </div>
  );
} 