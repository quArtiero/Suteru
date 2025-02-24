document.addEventListener('DOMContentLoaded', function() {
    console.log('Form.js carregado!'); // Debug
    
    const gradeSelect = document.getElementById('grade');
    const topicSelect = document.getElementById('topic');
    const newTopicInput = document.getElementById('new_topic');

    if (!gradeSelect || !topicSelect) {
        console.log('Elementos não encontrados:', {
            grade: !!gradeSelect,
            topic: !!topicSelect
        });
        return;
    }

    console.log('Elementos encontrados, iniciando setup...'); // Debug

    // Popula os grades (fixos)
    GRADES.forEach(grade => {
        const option = document.createElement('option');
        option.value = grade;
        option.textContent = grade;
        gradeSelect.appendChild(option);
    });

    // Adiciona opção "Outro" no select de tópicos
    const otherOption = document.createElement('option');
    otherOption.value = "other";
    otherOption.textContent = "Outro (especificar)";
    topicSelect.appendChild(otherOption);

    // Mostra/esconde input para novo tópico
    topicSelect.addEventListener('change', function() {
        if (this.value === 'other') {
            newTopicInput.style.display = 'block';
            newTopicInput.required = true;
        } else {
            newTopicInput.style.display = 'none';
            newTopicInput.required = false;
        }
    });

    // Mantém a seleção após submit
    const urlParams = new URLSearchParams(window.location.search);
    const selectedGrade = urlParams.get('grade');
    const selectedTopic = urlParams.get('topic');

    if (selectedGrade) {
        gradeSelect.value = selectedGrade;
    }
    if (selectedTopic) {
        topicSelect.value = selectedTopic;
    }
}); 