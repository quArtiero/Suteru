# 🌍 Šutēru – Knowledge That Transforms Lives

<div align="center">

![Šutēru Logo](app/static/images/logo.png)

**A revolutionary platform where education meets social impact**

[![Flask](https://img.shields.io/badge/Flask-2.3.2-blue?style=flat-square&logo=flask)](https://flask.palletsprojects.com/)
[![Python](https://img.shields.io/badge/Python-3.13-blue?style=flat-square&logo=python)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue?style=flat-square&logo=postgresql)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

[🚀 Live Demo](#) | [📖 Documentation](#setup) | [🤝 Contributing](#contributing) | [🎯 Roadmap](#roadmap)

</div>

## 🌟 What is Šutēru?

Šutēru is a **gamified educational platform** that transforms knowledge into real-world social impact. Every quiz answered correctly generates points that convert into **actual food donations** for vulnerable communities.

### 🎯 Real Impact, Real Numbers

<div align="center">

| 📊 **Current Impact** | 🎯 **Achievement** |
|:---------------------:|:------------------:|
| **12,504+** | Meals Donated |
| **1,000kg** | Rice Donated to Projeto Arrastão |
| **100+** | Active Students |
| **55** | Achievement Badges |

</div>

## ✨ Key Features

### 🧠 **Educational Excellence**
- **Multi-subject quizzes** (Math, Physics, Chemistry, Biology, History, Literature, Philosophy)
- **Grade-specific content** (1º ano to 3º ano do Ensino Médio)
- **Adaptive difficulty levels** (Easy, Medium, Hard)
- **Real-time progress tracking**

### 🏆 **Gamification & Achievements**
- **55 unique achievements** across different categories
- **Subject-specific challenges** (answer 20 math questions, etc.)
- **Progress tracking** with visual indicators
- **Leaderboard system** with fair ranking

### 🎨 **Modern User Experience**
- **Glassmorphism design** with blue color palette
- **Responsive design** for all devices
- **Smooth animations** and interactions
- **Highlighted impact cards** showing donation progress

### 🔐 **Flexible Authentication**
- **Login with username OR email**
- **Secure password hashing**
- **Role-based access control** (User/Admin)
- **WTForms validation**

### 📊 **Comprehensive Admin Panel**
- **User management** with promote/demote capabilities
- **Question bank management**
- **Performance analytics** by subject
- **Top users tracking** (excluding admin users)
- **Suggestion review system**

### ⚡ **Performance Optimized**
- **Database caching** (30-second cache for stats)
- **Singleton connection pattern** for PostgreSQL
- **Optimized queries** excluding admin users from leaderboards
- **Reduced animation overhead**

## 🏗️ Architecture

```
Šutēru/
├── 🚀 app/
│   ├── 📋 routes/              # Application routes
│   │   ├── admin.py           # Admin dashboard & management
│   │   ├── auth.py            # Authentication & user management  
│   │   ├── main.py            # Landing, leaderboard, about
│   │   └── quiz.py            # Quiz logic & question handling
│   ├── 🎨 templates/          # Jinja2 HTML templates
│   │   ├── admin/             # Admin interface templates
│   │   ├── auth/              # Login, register, dashboard
│   │   ├── main/              # Public pages
│   │   └── quiz/              # Quiz interface
│   ├── 💎 static/             # Frontend assets
│   │   ├── css/               # Modern CSS with design system
│   │   ├── js/                # JavaScript utilities
│   │   └── images/            # Assets & partner logos
│   ├── 🛠️ utils/              # Backend utilities
│   │   ├── database.py        # PostgreSQL operations
│   │   └── constants.py       # App constants
│   ├── 📝 forms.py            # WTForms definitions
│   └── ⚙️ config.py           # Application configuration
├── 📊 scripts/                # Database initialization
├── 📄 requirements.txt        # Python dependencies
└── 🎯 run.py                  # Application entry point
```

## 🚀 Quick Start

### Prerequisites
- **Python 3.13+**
- **PostgreSQL 16+**
- **Git**

### 1. Clone & Setup
```bash
# Clone the repository
git clone https://github.com/your-username/suteru.git
cd suteru

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Configuration
```bash
# Copy environment template
cp env.example .env

# Edit .env with your database credentials
nano .env
```

**Environment Variables:**
```env
# Security
SECRET_KEY=your-super-secret-key-change-this-in-production

# Database (PostgreSQL required)
internal_db_url=postgresql://username:password@localhost:5432/suteru_db

# Email Configuration (optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Development
FLASK_DEBUG=True
FLASK_ENV=development
```

### 3. Initialize Database
```bash
# Create database and tables
python3 scripts/init_db.py
```

### 4. Launch Application
```bash
# Start the development server
python3 run.py
```

🎉 **Access your app at:** `http://localhost:5001`

## 🎮 Usage Guide

### For Students
1. **Register** with username and email
2. **Choose subject** and grade level
3. **Answer quizzes** to earn points
4. **Track progress** in your dashboard
5. **Unlock achievements** by completing challenges
6. **View impact** - see how many meals your knowledge generated!

### For Administrators
1. **Login** with admin credentials
2. **Manage users** - promote, demote, or remove
3. **Review questions** - approve community suggestions
4. **Monitor stats** - track platform performance
5. **Upload content** - add new questions via CSV

## 🔧 Technical Highlights

### Performance Optimizations
- **Database Connection Pooling** with singleton pattern
- **Query Caching** for frequently accessed statistics
- **Optimized CSS** with reduced animation overhead
- **Admin User Exclusion** from public leaderboards

### Security Features
- **CSRF Protection** with Flask-WTF
- **Secure Password Hashing** using Werkzeug
- **Role-based Access Control**
- **Input Validation** and sanitization

### Design System
- **Modern CSS Variables** for consistent theming
- **Blue Color Palette** (no purple, as per design requirements)
- **Glassmorphism Effects** for premium feel
- **Responsive Grid System** for all screen sizes

## 📈 Impact Metrics

### Current Stats
- **Total Points Generated:** 23,818,998+
- **Meals Equivalent:** 12,504+
- **Rice Donated:** 1,000kg to Projeto Arrastão
- **Active Users:** 100+
- **Questions Answered:** 10,000+

### Conversion Rates
- **1 Point** = 0.16g of food
- **1 Question** = 1.6g of food = 10 points
- **1 Meal** = 80g of food = 500 points
- **50 Questions** = 1 complete meal donation

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### 🐛 Bug Reports
- Use GitHub Issues with the `bug` label
- Include steps to reproduce
- Provide system information

### ✨ Feature Requests
- Use GitHub Issues with the `enhancement` label
- Describe the use case
- Suggest implementation approach

### 💻 Code Contributions
```bash
# 1. Fork the repository
# 2. Create feature branch
git checkout -b feature/amazing-feature

# 3. Make your changes
# 4. Test thoroughly
python -m pytest tests/

# 5. Commit with clear message
git commit -m "feat: add amazing feature"

# 6. Push and create Pull Request
git push origin feature/amazing-feature
```

### 📝 Code Style
- Follow **PEP 8** for Python
- Use **meaningful variable names**
- Add **docstrings** for functions
- Keep **functions small** and focused

## 🛠️ Development

### Running Tests
```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=app tests/
```

### Database Operations
```bash
# Reset database
python scripts/init_db.py --reset

# Add sample data
python scripts/add_sample_data.py

# Backup database
pg_dump suteru_db > backup.sql
```

## 📱 API Documentation

### Public Endpoints
- `GET /` - Landing page with impact statistics
- `GET /leaderboard` - Public leaderboard (excludes admin users)
- `GET /sobre` - About page
- `GET /parceiros` - Partners page

### Authentication Required
- `GET /dashboard` - User dashboard with personal stats
- `GET /conquistas` - User achievements page
- `POST /quiz` - Submit quiz answers

### Admin Only
- `GET /admin` - Admin dashboard
- `POST /admin/users/promote/<id>` - Promote user
- `POST /admin/users/delete/<id>` - Delete user

## 🎯 Roadmap

### 🚧 In Progress
- [ ] Mobile app development
- [ ] API rate limiting
- [ ] Advanced analytics dashboard
- [ ] Multi-language support

### 🔮 Future Plans
- [ ] AI-powered question generation
- [ ] Video-based learning modules
- [ ] Corporate partnership portal
- [ ] Blockchain donation tracking

## 📞 Support & Contact

- **🐛 Issues:** [GitHub Issues](https://github.com/your-username/suteru/issues)
- **💬 Discussions:** [GitHub Discussions](https://github.com/your-username/suteru/discussions)
- **📧 Email:** contact@suteru.com
- **🌐 Website:** [suteru.com](https://suteru.com)

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Projeto Arrastão** - Our first NGO partner
- **Contributors** - Everyone who helped build this platform
- **Students** - The driving force behind our impact
- **Educators** - For providing valuable feedback

---

<div align="center">

**Made with ❤️ for social impact**

*Transforming knowledge into hope, one quiz at a time.*

</div>  
