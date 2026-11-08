# 💳 Personal Finance Hub

A containerized, local-first multi-user household finance platform built with **Python (Streamlit)**, **MySQL**, and **Ollama (AI Categorization)**. Designed for data privacy, automated bank statement parsing, and bulletproof duplicate prevention.

---

## 🛠️ Tech Stack & Architecture

- **Frontend / UI**: [Streamlit](https://streamlit.io/) (Interactive web dashboard with tabbed workflows)
- **Database**: MySQL 8.0 running inside Docker with persistent named volumes (`mysql_data`)
- **Backend Processing**: Python, Pandas, Regex file validation, and Cryptographic Hash generation (`sha256`)
- **AI Categorization**: Local LLM via [Ollama](https://ollama.com/) for automated merchant classification, impulse scoring, and subscription detection
- **Environment & Logging**: `python-dotenv`, dual-output logging (`finance_app.log`)

---

## 📂 Project Structure

```text
Finance_App/
│
├── .env                      # Environment variables (DB credentials, Ollama model)
├── config.py                 # Central config, logging setup, and DB configuration
├── app.py                    # Streamlit web application entry point
├── docker-compose.yml        # Docker setup for MySQL & Streamlit with live reloading
├── Dockerfile                # Container instructions for Streamlit
├── requirements.txt          # Python dependencies
├── init.sql                  # Automated database schema initialization
├── finance_app.log           # Persistent application log file
│
├── src/                      # Source code package
│   ├── __init__.py           
│   ├── db_manager.py         # Handles SQL queries, account lookups, and transaction inserts
│   └── processor.py          # CSV parser, file validator, hashing engine, and Ollama integration
│
└── uploads/                  # Local folder for archived, standardized bank CSV statements