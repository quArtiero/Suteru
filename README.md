# 🌍 Šutēru – Knowledge That Transforms 📚🍽️  

## What is Šutēru?  
Šutēru is a **social impact initiative** designed to bridge the gap between **education and hunger relief**. It is a platform where **learning leads to real-world impact**—every correct answer in an educational quiz results in a donation that helps fight food insecurity.  

### 🌟 Our Vision  
We believe that **knowledge should drive action**. In a world where education and food insecurity remain pressing issues, Šutēru connects **students, companies, and NGOs** to create a system where **learning directly benefits communities in need**.  

### 🎯 How It Works  
- **Users engage with quizzes** in subjects like math, science, and history.  
- **Each correct answer translates into a food donation**, funded by corporate partners.  
- **NGOs distribute the donations** to those in need, ensuring transparency and measurable impact.  

### 🚀 Why It Matters  
Millions of people face **daily food insecurity**, while access to quality education remains **unequal**. Šutēru creates a **win-win solution** where learners **gain knowledge** while making a **real difference in the world**.  

### 🔜 Project Status  
Šutēru is currently **in development**. We are working on building the platform, forming partnerships, and refining our impact model. Stay tuned for updates as we get closer to launching!  

📢 **Want to collaborate or support us? Reach out!**  

## Estrutura do Projeto

```
suteru/
├── app/
│   ├── __init__.py           # Inicialização do app Flask
│   ├── routes/               # Rotas da aplicação
│   │   ├── admin.py         # Rotas administrativas
│   │   ├── auth.py          # Rotas de autenticação
│   │   ├── main.py          # Rotas principais
│   │   └── quiz.py          # Rotas de quizzes
│   ├── models/              # Modelos do banco de dados
│   ├── templates/           # Templates HTML
│   ├── static/              # Arquivos estáticos
│   ├── utils/              # Utilitários
│   │   ├── database.py     # Funções do banco de dados
│   │   └── helpers.py      # Funções auxiliares
│   └── config.py           # Configurações
├── backups/                # Scripts de backup
├── tests/                 # Testes
├── requirements.txt       # Dependências
└── run.py                # Ponto de entrada
```

## Configuração

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/suteru.git
cd suteru
```

2. Crie um ambiente virtual e instale as dependências:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente:
```bash
export SECRET_KEY="sua-chave-secreta"
export internal_db_url="sua-url-do-banco"
```

4. Execute o aplicativo:
```bash
python run.py
```

## Contribuindo

1. Faça um Fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo LICENSE para detalhes.  
