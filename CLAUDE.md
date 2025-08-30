# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Kakao AlimTalk template auto-generation AI service designed to help small business owners create compliant templates without manually understanding complex approval policies. The AI automatically generates templates that comply with Kakao's AlimTalk policies based on user input.

**Tech Stack**: LangChain, Agent, Tools, RAG, LangGraph, FAISS, MySQL 8.4

## Commands

### Environment Setup
```bash
# Activate virtual environment (already exists)
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run main application
python main.py
```

### Development
```bash
# Run Jupyter notebooks for experimentation
jupyter lab notebooks/

# Create FAISS vectors (when implemented)
python scripts/create_vectors.py

# Setup database (when implemented)
python scripts/setup_db.py
```

## Architecture

### Core Directory Structure (Planned)
- **app/core/**: Core business logic
  - `chatbot.py`: LangChain-based conversational chatbot
  - `template_generator.py`: LangGraph workflow for template generation
  - `policy_validator.py`: Kakao policy compliance validation
- **app/services/**: Service layer
  - `rag_service.py`: RAG implementation for policy document retrieval
  - `vector_service.py`: FAISS vector search and similarity matching
- **app/models/**: Data models and MySQL database connections
- **app/api/**: FastAPI REST API endpoints

### Data Organization
- **data/policies/**: Kakao AlimTalk policy documents (currently contains `infotalk.md`)
- **data/vectors/**: FAISS index files for preprocessed policy data
- **data/templates/**: Sample approved templates
- **notebooks/**: Jupyter notebooks for prototyping and experimentation

### Development Workflow
1. Prototype and experiment in `notebooks/`
2. Modularize validated logic into `app/core/`
3. Write unit tests in `tests/`
4. Expose functionality via `app/api/`

## Key Technologies by Location
- **LangChain**: Conversation flow management in `app/core/chatbot.py`
- **RAG**: Policy document search in `app/services/rag_service.py`  
- **LangGraph**: Template generation workflow in `app/core/template_generator.py`
- **FAISS**: Vector search in `app/services/vector_service.py`
- **MySQL**: Database models in `app/models/`

## Current State
- Basic project structure with main.py placeholder
- README.md with detailed architecture plan
- Jupyter notebooks for experimentation (01_data_exploration.ipynb, faiss_test_*.ipynb)
- Initial policy document (infotalk.md) in data/policies/
- Empty requirements.txt and .env files ready for configuration

## Development Notes
- Project uses Korean language documentation
- Focus on compliance with Kakao's complex AlimTalk approval policies
- FAISS indexes are generated in notebooks/ and should be moved to data/vectors/
- Environment variables should be configured in .env based on .env.example