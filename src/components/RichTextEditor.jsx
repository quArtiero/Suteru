import React, { useEffect } from 'react';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css';
import 'katex/dist/katex.min.css';
import 'quill-better-table/dist/quill-better-table.css';

// Importações condicionais para evitar erros no lado do servidor
const loadDependencies = async () => {
  if (typeof window !== 'undefined') {
    const katex = await import('katex');
    window.katex = katex.default;

    const Quill = await import('quill');
    const BetterTable = await import('quill-better-table');
    
    // Registrar o módulo de tabela
    Quill.default.register('modules/better-table', BetterTable.default);
  }
};

const RichTextEditor = ({ value, onChange }) => {
  useEffect(() => {
    loadDependencies();
  }, []);

  const modules = {
    toolbar: {
      container: [
        [{ 'header': [1, 2, 3, false] }],
        ['bold', 'italic', 'underline', 'strike'],
        [{ 'script': 'sub'}, { 'script': 'super' }],
        ['formula'],
        [{ 'list': 'ordered'}, { 'list': 'bullet' }],
        ['link', 'image'],
        ['clean']
      ],
    },
    formula: true,
    'better-table': {
      operationMenu: {
        items: {
          unmergeCells: {
            text: 'Unmerge cells',
          },
        },
      },
    },
  };

  const formats = [
    'header',
    'bold', 'italic', 'underline', 'strike',
    'script',
    'list', 'bullet',
    'link', 'image',
    'formula'
  ];

  return (
    <div className="rich-text-editor">
      <ReactQuill 
        theme="snow"
        value={value}
        onChange={onChange}
        modules={modules}
        formats={formats}
        className="h-[300px] mb-12"
      />
      <style jsx global>{`
        .ql-formula {
          background: white !important;
          color: #444 !important;
        }
        .ql-editor {
          min-height: 200px;
        }
      `}</style>
    </div>
  );
};

export default RichTextEditor; 