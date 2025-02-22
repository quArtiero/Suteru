import QuestionDisplay from '../components/QuestionDisplay';

function Quiz() {
  return (
    <div className="container mx-auto p-4">
      {currentQuestion && (
        <QuestionDisplay
          question={currentQuestion.question}
          options={currentQuestion.options}
        />
      )}
    </div>
  );
}

export default Quiz; 