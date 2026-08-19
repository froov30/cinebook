# Contributing to CineBook

Thank you for considering contributing to CineBook! This document provides guidelines to help you get started.

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+**
- **MySQL 8.0** (via XAMPP or standalone) — *optional, SQLite fallback is built-in*

### Development Setup

```bash
# Clone the repository
git clone https://github.com/froov30/cinebook.git
cd cinebook

# Create a virtual environment
python -m venv venv
source venv/bin/activate    # Linux/macOS
# venv\Scripts\Activate.ps1  # Windows PowerShell

# Install dependencies
pip install -r requirements.txt

# Setup the database
python run_setup.py

# Run the dashboard
streamlit run app/streamlit_app.py
```

### Running Tests

```bash
pytest tests/ -v
```

All 16 tests must pass before submitting a pull request.

## 📋 Code Style

- **Python**: Follow PEP 8 conventions
- **SQL**: Use uppercase keywords (`SELECT`, `INSERT`, `CREATE TABLE`)
- **Docstrings**: Every public function must have a docstring with type hints
- **Commits**: Use clear, descriptive commit messages

## 🔄 Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Run the full test suite (`pytest tests/ -v`)
5. Commit with a descriptive message
6. Push to your fork and open a Pull Request

## 🐛 Reporting Issues

When reporting a bug, please include:
- Steps to reproduce
- Expected vs actual behaviour
- Python version and OS
- Database engine (MySQL or SQLite)

## 📜 License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
