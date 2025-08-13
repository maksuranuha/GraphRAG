import streamlit as st
from dotenv import load_dotenv
import os
from neo4j import GraphDatabase
from langchain_groq import ChatGroq

load_dotenv()

st.set_page_config(page_title="Game Finder", page_icon="🎮", layout="wide")

st.markdown("""
<style>
.main-header {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    padding: 1rem;
    border-radius: 10px;
    text-align: center;
    margin-bottom: 2rem;
}
.method-badge {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: bold;
    margin: 0.25rem;
}
.rag-badge { background: #e3f2fd; color: #1565c0; }
.graph-badge { background: #f3e5f5; color: #7b1fa2; }
.hybrid-badge { background: #e8f5e8; color: #2e7d32; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>🎮 Game Finder</h1><p>An Ultimate Game Discovery Guide</p></div>', unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

@st.cache_resource
def initialize_system():
    llm = ChatGroq(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.3-70b-versatile",
        temperature=0.1
    )
    
    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
    )
    
    return llm, driver

def semantic_search(driver, query, top_k=5):
    try:
        with driver.session() as session:
            result = session.run("""
            WITH genai.vector.encode(
                $question,
                "OpenAI",
                {
                  token: $openAiApiKey,
                  endpoint: $openAiEndpoint
                }) AS question_embedding
            CALL db.index.vector.queryNodes(
                'story_game_embeddings',
                $top_k,
                question_embedding
            ) YIELD node AS game, score
            WHERE game.user_review > 6.0
            RETURN game.name, game.summary, game.user_review, game.platform, score
            ORDER BY score DESC
            """, parameters={
                'openAiApiKey': os.getenv("OPENAI_API_KEY"),
                'openAiEndpoint': os.getenv("OPENAI_ENDPOINT_EMBEDDINGS"),
                'question': query,
                'top_k': top_k
            })
            return list(result)
    except Exception as e:
        st.error(f"🔍 Semantic search failed: {e}")
        return []

def graph_traversal_search(driver, game_name):
    try:
        with driver.session() as session:
            result = session.run("""
            MATCH (g:Game)
            WHERE toLower(g.name) CONTAINS toLower($game_name)
            WITH g
            OPTIONAL MATCH (g)-[r:SIMILAR_STORY]->(similar:Game)
            WHERE similar.user_review > 7.0
            OPTIONAL MATCH (g)-[:SAME_PLATFORM]->(platform_rec:Game)
            WHERE platform_rec.user_review > 8.0
            OPTIONAL MATCH (g)-[:BELONGS_TO]->(genre:Genre)<-[:BELONGS_TO]-(genre_rec:Game)
            WHERE genre_rec.user_review > 7.5 AND genre_rec <> g
            RETURN g.name as original_game,
                   g.summary as original_summary,
                   g.user_review as original_rating,
                   collect(DISTINCT {name: similar.name, similarity: r.similarity, rating: similar.user_review})[0..3] as similar_games,
                   collect(DISTINCT {name: platform_rec.name, rating: platform_rec.user_review})[0..3] as platform_recommendations,
                   collect(DISTINCT {name: genre_rec.name, rating: genre_rec.user_review})[0..2] as genre_recommendations
            LIMIT 1
            """, parameters={'game_name': game_name})
            return list(result)
    except Exception as e:
        st.error(f"🕸️ Graph traversal failed: {e}")
        return []

def hybrid_ragat_search(driver, query):
    semantic_results = semantic_search(driver, query, 5)
    graph_results = []
    game_keywords = [
        'witcher', 'zelda', 'mass effect', 'final fantasy', 'last of us', 
        'god of war', 'horizon', 'cyberpunk', 'assassin', 'elder scrolls',
        'persona', 'nier', 'bioshock', 'red dead', 'ghost of tsushima'
    ]
    
    for keyword in game_keywords:
        if keyword in query.lower():
            graph_results = graph_traversal_search(driver, keyword)
            break
    
    return semantic_results, graph_results

def format_game_recommendation(game, method="semantic", score=None):
    rating = f"⭐ {game.get('game.user_review', game.get('rating', 'N/A'))}/10" 
    platform = game.get('game.platform', game.get('platform', 'Multiple platforms'))
    summary = game.get('game.summary', game.get('summary', 'No summary available'))
    
    if len(summary) > 150:
        summary = summary[:150] + "..."
    
    method_badge = {
        "semantic": '<span class="method-badge rag-badge">🔍 RAG Match</span>',
        "graph": '<span class="method-badge graph-badge">🕸️ Graph Link</span>',
        "hybrid": '<span class="method-badge hybrid-badge">🚀 RAGAT</span>'
    }
    
    score_text = f" (Score: {score:.3f})" if score else ""
    
    return f"""
    <div class="game-card">
        {method_badge.get(method, '')}
        <h4>🎮 {game.get('game.name', game.get('name', 'Unknown Game'))}</h4>
        <p><strong>{rating}</strong> • <em>{platform}</em>{score_text}</p>
        <p>{summary}</p>
    </div>
    """

def process_with_ragat(driver, llm, query):
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.markdown("** RAGAT Pipeline:**")
        progress = st.progress(0)
        status = st.empty()
    
    status.text("RAG: Semantic search...")
    progress.progress(25)
    semantic_results, graph_results = hybrid_ragat_search(driver, query)
    
    status.text(" AT: Graph traversal...")
    progress.progress(50)
    
    status.text(" LLM: Generating response...")
    progress.progress(75)
    
    with col1:
        if semantic_results or graph_results:
            st.markdown("### Results")
            
            if semantic_results:
                st.markdown("#### **RAG Component** - Semantic Matches")
                for i, game in enumerate(semantic_results[:3]):
                    score = game.get('score', 0)
                    st.markdown(format_game_recommendation(game, "semantic", score), unsafe_allow_html=True)
            
            if graph_results and len(graph_results) > 0:
                result = graph_results[0]
                st.markdown("#### 🕸️ **AT Component** - Graph Connections")
                
                if result['similar_games'] and any(g['name'] for g in result['similar_games']):
                    st.markdown("**Story-Similar Games:**")
                    for similar in result['similar_games']:
                        if similar['name']:
                            st.markdown(format_game_recommendation(similar, "graph"), unsafe_allow_html=True)
                
                if result['platform_recommendations'] and any(g['name'] for g in result['platform_recommendations']):
                    st.markdown("**Platform Recommendations:**")
                    for rec in result['platform_recommendations'][:2]:
                        if rec['name']:
                            st.markdown(format_game_recommendation(rec, "graph"), unsafe_allow_html=True)
            
            st.markdown("#### **LLM Enhancement**")
            context = []
            if semantic_results:
                context.extend([f"{g['game.name']}: {g['game.summary']}" for g in semantic_results[:3]])
            if graph_results:
                for result in graph_results:
                    if result['similar_games']:
                        context.extend([f"{g['name']}: Connected via story similarity" for g in result['similar_games'] if g['name']])
            
            if context:
                llm_prompt = f"""Based on these game recommendations: {'; '.join(context[:5])}, 
                provide a thoughtful analysis of why these games match the query: "{query}". 
                Focus on narrative themes, gameplay elements, and what makes them special for story-focused gamers."""
                
                try:
                    llm_response = llm.invoke(llm_prompt)
                    st.markdown(f" **AI Curator's Analysis:**\n\n{llm_response.content}")
                except Exception as e:
                    st.info(" The games above represent excellent matches based on story elements and player ratings.")
        
        else:
            st.warning(" No RAGAT matches found. Trying basic database search...")
            with driver.session() as session:
                basic_results = session.run("""
                MATCH (g:Game)
                WHERE toLower(g.summary) CONTAINS toLower($query) 
                   OR toLower(g.name) CONTAINS toLower($query)
                   AND g.user_review > 7.0
                RETURN g.name, g.summary, g.user_review, g.platform
                ORDER BY g.user_review DESC
                LIMIT 5
                """, parameters={'query': query})
                
                basic_list = list(basic_results)
                if basic_list:
                    st.markdown("### Basic Search Results")
                    for game in basic_list:
                        st.markdown(format_game_recommendation(game, "basic"), unsafe_allow_html=True)
                else:
                    st.error("No games found. Try different keywords!")
    
    progress.progress(100)

llm, driver = initialize_system()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            st.markdown(message["content"], unsafe_allow_html=True)
        else:
            st.markdown(message["content"])

if prompt := st.chat_input("What kind of game are you searching?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        process_with_ragat(driver, llm, prompt)
        st.session_state.messages.append({
            "role": "assistant", 
            "content": f" Analysis completed for: '{prompt}'"
        })

# Sidebar
with st.sidebar:
    st.header("Quick Searches:")
    
    examples = [
        "Games like The Witcher 3",
        "Best RPGs with deep stories", 
        "Highest rated story games",
        "Emotional narrative games"
    ]
    
    for example in examples:
        if st.button(example):
            st.session_state.messages.append({"role": "user", "content": example})
            st.rerun()
    