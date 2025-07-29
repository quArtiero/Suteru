// Form.js - Funcionalidades do formulário
document.addEventListener('DOMContentLoaded', function() {
    const formElements = document.querySelectorAll('.form-control, .form-select');
    const submitButtons = document.querySelectorAll('button[type="submit"]');
    
    if (formElements.length > 0 && submitButtons.length > 0) {
        // Configurar validação de formulários
        formElements.forEach(element => {
            element.addEventListener('blur', function() {
                validateField(this);
            });
        });
        
        // Configurar submissão de formulários
        submitButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                if (!validateForm(this.closest('form'))) {
                    e.preventDefault();
                }
            });
        });
    }
});

function validateField(field) {
    const value = field.value.trim();
    const fieldName = field.name;
    
    // Remover classes de erro anteriores
    field.classList.remove('is-invalid');
    field.classList.remove('is-valid');
    
    // Validações específicas por campo
    if (fieldName === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            field.classList.add('is-invalid');
            return false;
        }
    }
    
    if (fieldName === 'password' && value) {
        if (value.length < 6) {
            field.classList.add('is-invalid');
            return false;
        }
    }
    
    if (field.required && !value) {
        field.classList.add('is-invalid');
        return false;
    }
    
    field.classList.add('is-valid');
    return true;
}

function validateForm(form) {
    const fields = form.querySelectorAll('.form-control, .form-select');
    let isValid = true;
    
    fields.forEach(field => {
        if (!validateField(field)) {
            isValid = false;
        }
    });
    
    return isValid;
} 