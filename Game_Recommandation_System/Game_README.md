# 📖 Game Recommandation System

An intelligent game finder that combines **Graph RAG + RAGAT** to find amazing story-driven games. Built with Neo4j, OpenAI embeddings, and Streamlit.

## 🎯 What It Does

Finds story games using two powerful approaches:
- **Vector Search**: AI understands game themes and narratives
- **Graph Traversal**: Discovers connections between quality games
- **Hybrid Intelligence**: Automatically picks the best method for your query

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Neo4j Database (local or cloud)
- OpenAI API key
- Groq API key

### Installation

```bash
git clone https://github.com/maksuranuha/game-recommander.git
cd game-recommander
pip install -r requirements.txt
```

### Environment Setup

Create `.env` file:
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j

OPENAI_API_KEY=sk-your-key
OPENAI_ENDPOINT_EMBEDDINGS=https://api.openai.com/v1/embeddings

GROQ_API_KEY=gsk_your-key
```

### Data Setup

1. Place your `video_games.csv` in `data/` folder with columns:
   - `name` - Game title
   - `platform` - Gaming platform  
   - `release_date` - When released
   - `summary` - Story description
   - `user_review` - Rating score

2. Run the setup:
```bash
python game_loader.py
python game_embedding.py
streamlit run chatbot.py
```

## 🏗️ System Architecture

### Game Loader (`game_loader.py`)
- Loads CSV data into Neo4j
- Creates smart relationships between games
- Sets up performance indexes

**Relationships Created:**
- `AVAILABLE_ON` - Game to platform connections
- `SIMILAR_RATING` - Games with similar scores
- `SAME_PLATFORM` - Quality games on same platform

### Embedding System (`game_embedding.py`)
- Generates story-focused embeddings
- Creates advanced relationships
- Auto-detects genres from summaries

**Advanced Relationships:**
- `SIMILAR_STORY` - Thematically similar games
- `BELONGS_TO` - Genre classifications

### Chatbot Interface (`chatbot.py`)
- Streamlit web interface
- Hybrid RAG+RAGAT implementation
- Intelligent query routing

## 🔍 How It Works

### Smart Query Detection
- **"Similar to Witcher"** → Uses hybrid search
- **"Best RPGs"** → Uses graph traversal  
- **"Emotional games"** → Uses vector similarity

### RAG + RAGAT Pipeline
1. **Semantic Search**: Vector embeddings find thematic matches
2. **Graph Traversal**: Explores game connections and relationships
3. **Hybrid Results**: Combines both approaches for better recommendations

## 💡 Example Queries

- "Find games similar to The Last of Us"
- "What are the highest rated story games?"
- "Show me PlayStation exclusives with great narratives"
- "Recommend emotional RPGs with character development"

## 📊 Database Schema

```
(Game)-[:AVAILABLE_ON]->(Platform)
(Game)-[:SIMILAR_STORY]->(Game)
(Game)-[:SIMILAR_RATING]->(Game)  
(Game)-[:SAME_PLATFORM]->(Game)
(Game)-[:BELONGS_TO]->(Genre)
```

## 📝 Requirements

Create `requirements.txt`:
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

## 🎮 Features

- **Story Focus**: Emphasizes narrative quality over gameplay mechanics
- **Quality Filtering**: Only recommends games with good ratings
- **Platform Aware**: Finds games available on your preferred systems  
- **Theme Understanding**: AI grasps story themes and emotional elements
- **Connected Discovery**: Finds hidden gems through game relationships
