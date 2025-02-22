import React from 'react';
import 'katex/dist/katex.min.css';

const QuestionDisplay = ({ question, options }) => {
  return (
    <div className="question-container p-4 rounded-lg bg-white shadow">
      {/* Renderiza a pergunta com o HTML formatado */}
      <div className="question-text mb-4">
        <div 
          className="prose max-w-none"
          dangerouslySetInnerHTML={{ __html: question }}
        />
      </div>

      {/* Renderiza as opções */}
      <div className="options-list space-y-3">
        {options.map((option, index) => (
          <div key={index} className="option-item flex items-start gap-2">
            <input
              type="radio"
              name="question-option"
              id={`option-${index}`}
              className="mt-1"
            />
            <label 
              htmlFor={`option-${index}`}
              className="flex-1"
            >
              <div 
                className="prose max-w-none"
                dangerouslySetInnerHTML={{ __html: option.text }}
              />
            </label>
          </div>
        ))}
      </div>

      <style jsx global>{`
        /* Estilos para garantir que as fórmulas matemáticas apareçam corretamente */
        .katex-display {
          margin: 1em 0;
          overflow-x: auto;
          overflow-y: hidden;
        }
        
        /* Estilos para imagens dentro das questões */
        .prose img {
          max-width: 100%;
          height: auto;
        }
        
        /* Estilos para tabelas */
        .ql-table {
          border-collapse: collapse;
          width: 100%;
        }
        
        .ql-table td {
          border: 1px solid #ddd;
          padding: 8px;
        }
      `}</style>
    </div>
  );
};

export default QuestionDisplay; 