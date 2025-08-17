# 🔍 Authenticity Detector

> **Advanced AI-powered system for detecting fake news and AI-generated content using Neo4j Graph Database and Large Language Models**

## 🎯 Overview

The **Authenticity Detector** is a sophisticated system that combines graph databases, vector embeddings, and large language models to detect fake news and AI-generated content with high accuracy. Built for researchers, journalists, and content moderators who need reliable authenticity verification.

### 🔥 Key Features

- **📰 Fake News Detection**: Identify misinformation across political, health, and social topics
- **🤖 AI Content Detection**: Distinguish between human-written and AI-generated essays/articles  
- **🔍 Semantic Search**: Find similar content patterns using advanced vector embeddings
- **📊 Pattern Analysis**: Discover trends in misinformation and AI content generation
- **💬 Interactive Chat**: Natural language queries powered by Groq and OpenAI
- **☁️ Cloud-Ready**: Works with Azure Neo4j Aura (no local database required)

## 🗂️ Datasets

This project analyzes a comprehensive dataset named ai-ga data:
### 🤖 LLM AI-Generated Text Dataset  
- **Source**: [Kaggle - LLM Detect AI Generated Text](https://www.kaggle.com/datasets/sunilthite/llm-detect-ai-generated-text-dataset)
- **Size**: ~28,000 essays
- **Content**: Student essays and AI-generated equivalents
- **Labels**: Human-written (0) vs AI-generated (1)
- **Features**: Essay text, generation label

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Neo4j Aura account (free tier available)
- OpenAI API key
- Groq API key

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/maksuranuha/authenticity-detector.git
cd authenticity-detector
```

2. **Set up virtual environment**
```bash
python -m venv env
# Windows:
env\Scripts\activate
# Mac/Linux:
source env/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

4. **Download datasets**
   - Download datasets from Kaggle links above
   - Place CSV files in `data/` folder:
     - `data/Fake.csv`
     - `data/True.csv` 
     - `data/AI_generated.csv`

5. **Configure environment**
```bash
# Create .env file
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j

OPENAI_API_KEY=sk-your-openai-key
GROQ_API_KEY=your-groq-key
GROQ_MODEL=mixtral-8x7b-32768
```

### 🏃‍♂️ Running the System

**Step 1: Load Data**
```bash
python optimized_loader.py
```
*Loads and processes 73,000+ articles/essays (~2-5 minutes)*

**Step 2: Generate Embeddings**
```bash
python optimized_embeddings.py
```
*Creates vector embeddings for similarity search (~10-20 minutes)*

**Step 3: Test Accuracy**
```bash
python test.py
```
*Validates system performance with real samples*

**Step 4: Launch Application**
```bash
streamlit run chatbot.py
```
*Opens web interface at `http://localhost:8501`*

## 💡 Usage Examples

### Interactive Queries
```
"Show me fake news patterns in politics"
"Find AI-generated essays about technology"
"What are the most deceptive content topics?"
"Compare human vs AI writing styles"
"Find articles similar to election fraud claims"
```

### Programmatic Access
```python
from langchain_neo4j import Neo4jGraph

kg = Neo4jGraph(url=NEO4J_URI, username=USERNAME, password=PASSWORD)

# Find fake news by subject
result = kg.query("""
    MATCH (a:Article)-[:HAS_SUBJECT]->(s:Subject {name: "politics"})
    WHERE a.is_fake = true
    RETURN a.title, a.date
    ORDER BY a.date DESC LIMIT 10
""")
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │    │   Processing    │    │   Analysis      │
│                 │    │                 │    │                 │
│ • Fake News CSV │───▶│ • NLP Pipeline  │───▶│ • Graph Queries │
│ • Real News CSV │    │ • Keyword Ext.  │    │ • Vector Search │
│ • AI Essays CSV │    │ • Embeddings    │    │ • LLM Analysis  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Neo4j Graph   │    │   Vector Index  │    │   Streamlit UI  │
│                 │    │                 │    │                 │
│ • Articles      │◀───│ • Embeddings    │◀───│ • Chat Interface│
│ • Essays        │    │ • Similarity    │    │ • Visualizations│
│ • Relationships │    │ • Search        │    │ • Reports       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📊 Key Components

### 🔧 Core Modules

| Module | Purpose | Key Features |
|--------|---------|--------------|
| `optimized_loader.py` | Data ingestion | Enhanced NLP, deduplication, relationship mapping |
| `optimized_embeddings.py` | Vector generation | Context-aware embeddings, similarity indices |
| `chatbot.py` | User interface | Natural language queries, real-time analysis |
| `test.py` | Accuracy validation | Performance metrics, sample testing |

### 🧠 AI Models Used

- **OpenAI GPT-3.5/4**: Content classification and analysis
- **OpenAI text-embedding-3-small**: Semantic vector embeddings  
- **Groq Mixtral-8x7B**: Fast inference for chat responses
- **spaCy**: Advanced NLP for keyword extraction

### 📈 Graph Schema

```cypher
// News Articles
(Article)-[:HAS_SUBJECT]->(Subject)
(Article)-[:CONTAINS_KEYWORD]->(Keyword)

// Essays
(Essay)-[:CONTAINS_KEYWORD]->(Keyword)

// Properties
Article: {id, title, text, is_fake, date, embedding}
Essay: {id, title, text, generated, word_count, embedding}
Subject: {name}
Keyword: {name}
```

## 📋 Requirements

```
neo4j
python-dotenv
pandas
numpy
langchain
langchain-openai
langchain-community
langchain-neo4j
langchain-groq
openai
streamlit
nltk
spacy
scikit-learn
tqdm
```

## 🚢 Deployment

### Local Development
```bash
streamlit run chatbot.py
```

### Cloud Deployment (Streamlit Cloud)
1. Push to GitHub
2. Connect to Streamlit Cloud
3. Add environment variables
4. Deploy automatically

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📚 Research & References

- **Graph-Based Fake News Detection**: Leveraging relationship patterns
- **Vector Embeddings for Content Analysis**: Semantic similarity approaches
- **LLM-Based Classification**: Comparing human vs AI-generated text
- **Neo4j Vector Indexing**: Optimizing similarity search performance

**⭐ If this project helps you, please give it a star!**