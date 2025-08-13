# 🎮 Game Recommendation System With RAGAT

An advanced AI-powered game discovery platform that combines **Retrieval Augmented Generation (RAG)** with **Graph-based Advanced Traversal (AT)** to create the ultimate **RAGAT** system for personalized game recommendations.

<img width="1913" height="903" alt="Screenshot 2025-08-13 142932" src="https://github.com/user-attachments/assets/5c83ea64-8b08-4e89-a66e-30a07160496e" />


## 🌟 Features

### 🔍 **Hybrid RAGAT Architecture**
- **RAG Component**: Semantic search using TF-IDF embeddings and cosine similarity
- **AT Component**: Graph traversal through story similarities, platform relationships, and genre connections
- **LLM Enhancement**: Intelligent analysis and curation using Groq's Llama 3.3 70B model

### 🕸️ **Advanced Graph Database**
- **Neo4j Integration**: Sophisticated relationship modeling between games
- **Multi-dimensional Connections**: Story similarity, platform compatibility, genre relationships, and rating correlations
- **Vector Embeddings**: 512-dimensional TF-IDF vectors for semantic game matching

### 🎯 **Intelligent Recommendation Engine**
- **Semantic Matching**: Find games with similar narratives and themes
- **Graph Traversal**: Discover hidden connections between games
- **Rating-based Filtering**: Focus on high-quality games (6.0+ user ratings)
- **Multi-modal Search**: Text-based queries with contextual understanding

### 🚀 **Modern Tech Stack**
- **Frontend**: Streamlit with custom CSS styling and responsive design
- **Backend**: Python with advanced NLP and graph processing
- **Database**: Neo4j graph database with vector indexing
- **AI/ML**: Groq LLM, scikit-learn, TF-IDF vectorization
- **Deployment**: Local hosting with scalable architecture

## Database Requirements

### **Local Neo4j Installation Highly Recommended**

This system creates an extensive relationship network with **500,000+ connections** between games with embeddings. While Neo4j Aura can handle the data, its browser-based visualization tools struggle with networks of this scale.

**Why Local Neo4j?**
- **Performance**: Better handling of complex graph traversals
- **Visualization**: Full Neo4j Browser capabilities for relationship exploration
- **Memory**: No cloud limitations for large-scale graph operations
- **Development**: Better debugging and query optimization tools

**Neo4j Aura Limitations:**
- Browser visualization becomes unresponsive with 500K+ relationships
- Limited memory allocation for complex queries
- Reduced performance for real-time graph traversals

## 📊 Database Statistics

- **Games**: 18,686 titles with comprehensive metadata
- **Platforms**: 22 gaming platforms
- **Embeddings**: 18,686 semantic vector representations
- **Relationships**: 509,075+ story similarity connections
- **Platform Links**: 18,686 platform relationships
- **Rating Connections**: 1,994 quality-based relationships
  
> **Note:** The dataset used in this project was collected from Kaggle.  
> You can replace it with any other game dataset of your choice by ensuring it has similar fields  
> (e.g., `name`, `summary`, `user_review`, `platform`) and updating the Neo4j database accordingly.


## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Query    │───▶│   RAGAT Engine   │───▶│   Results UI    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  RAG Component   │
                    │ ┌──────────────┐ │
                    │ │ Semantic     │ │
                    │ │ Search       │ │
                    │ │ (TF-IDF)     │ │
                    │ └──────────────┘ │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  AT Component    │
                    │ ┌──────────────┐ │
                    │ │ Graph        │ │
                    │ │ Traversal    │ │
                    │ │ (Neo4j)      │ │
                    │ └──────────────┘ │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ LLM Enhancement  │
                    │ ┌──────────────┐ │
                    │ │ Groq Llama   │ │
                    │ │ 3.3 70B      │ │
                    │ └──────────────┘ │
                    └──────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- **Neo4j Database (LOCAL INSTALLATION REQUIRED)**
  > ⚠️ **Important**: Due to the vast relationship network (500K+ connections), Neo4j Aura's visualization capabilities are limited. A **local Neo4j installation** is strongly recommended for optimal performance and full graph exploration capabilities.
- Groq API key
- OpenAI API key (optional, for enhanced embeddings)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/game-recommendation-system.git
   cd game-recommendation-system
   ```

2. **Create virtual environment**
   ```bash
   python -m venv env
   source env/bin/activate  # Linux/Mac
   # or
   env\Scripts\activate     # Windows
   ```

3. **Install dependencies**
   Create a `requirements.txt` file:
   ```txt
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
   
   Then install:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment setup**
   Create a `.env` file in the root directory:
   ```env
   # Neo4j Configuration
   NEO4J_URI=YOUR_URI
   NEO4J_USERNAME=YOUR_USERNAME
   NEO4J_PASSWORD=YOUR_PASSWORD
   NEO4J_DATABASE=YOUR_DB
   # AURA_INSTANCEID=YOUR_AURA_INSTANCE_ID
   # AURA_INSTANCENAME=YOUR_AURA_INSTANCE_NAME

   # Groq Configuration
   GROQ_API_KEY=gsk_YOUR_API_KEY
   GROQ_MODEL=llama-3.3-70b-versatile

   # OpenAI Configuration (Optional if you want to use OpenAI)
   # OPENAI_API_KEY=sk-YOUR_API_KEY
   # OPENAI_ENDPOINT_EMBEDDINGS=https://api.openai.com/v1/embeddings
   # OPENAI_ENDPOINT=https://api.openai.com/v1
   ```

5. **Data preparation**
   Place your `video_games.csv` file in the `data/` directory with the following columns:
   - `name`: Game title
   - `platform`: Gaming platform
   - `release_date`: Release date
   - `summary`: Game description/story
   - `user_review`: Rating (0-10 scale)

### Database Setup

1. **Load game data**
   ```bash
   python game_loader.py
   ```

2. **Generate embeddings and relationships**
   ```bash
   python game_embedding.py
   ```

3. **Launch the application**
   ```bash
   streamlit run chatbot.py
   ```

## 🎯 Usage Guide

### Basic Search Queries
- "Games like The Witcher 3"
- "Best RPGs with deep stories"
- "Emotional narrative games"
- "Highest rated story games"

### Advanced Features

#### **RAG Component Results**
- Semantic similarity scoring
- Story-based matching
- Contextual game discovery

#### **AT Component Results**
- Story similarity networks
- Platform recommendations  
- Genre-based connections

#### **LLM Enhancement**
- Intelligent analysis of recommendations
- Narrative theme explanations
- Personalized curation insights

## 🔧 Technical Implementation

### Graph Database Schema

```cypher
// Nodes
(g:Game {name, summary, user_review, platform, game_id, embedding})
(p:Platform {name})
(genre:Genre {name})

// Relationships
(g1:Game)-[:SIMILAR_STORY {similarity: float}]->(g2:Game)
(g:Game)-[:AVAILABLE_ON]->(p:Platform)
(g:Game)-[:BELONGS_TO]->(genre:Genre)
(g1:Game)-[:SIMILAR_RATING]->(g2:Game)
(g1:Game)-[:SAME_PLATFORM]->(g2:Game)
```

### Vector Embeddings

- **Dimensionality**: 512 features
- **Method**: TF-IDF with n-grams (1,2)
- **Similarity**: Cosine similarity
- **Index**: Neo4j vector index for fast retrieval

### LLM Integration

- **Model**: Groq Llama 3.3 70B Versatile
- **Temperature**: 0.1 (focused responses)
- **Context**: Game metadata and relationship data
- **Enhancement**: Narrative analysis and thematic explanations

## 📈 Performance Metrics

- **Search Speed**: Sub-second response times
- **Database Size**: 18K+ games with 500K+ relationships
- **Accuracy**: High-precision recommendations based on multiple similarity vectors
- **Scalability**: Handles complex graph traversals efficiently

## 🛠️ Configuration

### Customization Options

```python
# Search parameters
TOP_K_RESULTS = 5
SIMILARITY_THRESHOLD = 0.3
RATING_FILTER = 6.0

# Embedding configuration
MAX_FEATURES = 512
NGRAM_RANGE = (1, 2)
MIN_DF = 2

# LLM settings
TEMPERATURE = 0.1
MAX_TOKENS = 500
```

## 📊 Graph Visualizations

The system creates rich relationship networks:

<img width="891" height="498" alt="similar_rating" src="https://github.com/user-attachments/assets/9a2c8393-1725-4184-b4d3-28ccab18c3de" />
*Similar high-rated games connection network*

<img width="891" height="498" alt="visualisation" src="https://github.com/user-attachments/assets/956075e4-9a3a-4928-9241-f91a7c4f7b60" />
*Visualization*

<img width="891" height="498" alt="similar_story" src="https://github.com/user-attachments/assets/ca80e86f-61f4-4493-bee9-bfe05bcb49e6" />

*Story similarity network showing connected games*

## 🔍 Query Examples and Results

### Database Statistics Query
```cypher
MATCH ()-[r]-() 
RETURN count(r) as total_relationships, 
       count(DISTINCT type(r)) as relationship_types, 
       collect(DISTINCT type(r)) as all_types
```

### Similar Games Discovery
```cypher
MATCH (g1:Game {name: "The Legend of Zelda: Ocarina of Time"}), (g2:Game) 
WHERE g1 <> g2 AND g2.user_review IS NOT NULL AND 
      abs(toFloat(g1.user_review) - toFloat(g2.user_review)) <= 0.4
RETURN g2.name, g2.user_review
```

## 🚀 Future Enhancements

### Planned Features
- [ ] **Real-time Updates**: Dynamic game database synchronization
- [ ] **User Profiles**: Personalized recommendation learning
- [ ] **Advanced Filtering**: Multi-criteria search capabilities
- [ ] **Social Features**: Community ratings and reviews
- [ ] **Mobile App**: Cross-platform accessibility
- [ ] **API Endpoint**: RESTful API for third-party integrations

### Technical Improvements
- [ ] **Caching Layer**: Redis integration for faster responses
- [ ] **Batch Processing**: Optimized embedding generation
- [ ] **A/B Testing**: Recommendation algorithm comparison
- [ ] **Monitoring**: Performance and usage analytics

### Development Guidelines
- Follow PEP 8 style guidelines
- Add unit tests for new features
- Update documentation as needed
- Ensure compatibility with existing codebase

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
