import streamlit as st
from dotenv import load_dotenv
import os
from langchain_neo4j import Neo4jGraph
from langchain_neo4j import GraphCypherQAChain
from langchain.prompts.prompt import PromptTemplate

load_dotenv()

st.set_page_config(page_title="Story Game Finder", page_icon="📖", layout="wide")
st.title("📖 Story Game Finder")
st.markdown("Find your next great story adventure!")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_example" not in st.session_state:
    st.session_state.selected_example = None

@st.cache_resource
def initialize_system():
    from langchain_groq import ChatGroq
    
    llm = ChatGroq(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        model_name="mixtral-8x7b-32768",
        temperature=0.1
    )

    kg = Neo4jGraph(
        url=os.getenv("NEO4J_URI"),
        username=os.getenv("NEO4J_USERNAME"),
        password=os.getenv("NEO4J_PASSWORD"),
        database=os.getenv("NEO4J_DATABASE", "neo4j")
    )
    
    CYPHER_TEMPLATE = """
    You are creating Cypher queries for a story-focused game recommendation system.
    Focus on narrative quality, story depth, and player ratings.
    
    Schema: {schema}

    Available relationships and patterns:
    - (g:Game)-[:AVAILABLE_ON]->(p:Platform)
    - (g:Game)-[:SIMILAR_STORY]->(g2:Game) [with similarity score]
    - (g:Game)-[:SIMILAR_RATING]->(g2:Game) [games with similar ratings]
    - (g:Game)-[:SAME_PLATFORM]->(g2:Game) [quality games on same platform]
    - (g:Game)-[:BELONGS_TO]->(genre:Genre)

    Query patterns for story games:
    
    1. Highest rated stories:
    MATCH (g:Game) WHERE g.user_review > 8.0 AND g.has_story = true 
    RETURN g.name, g.summary, g.user_review, g.platform ORDER BY g.user_review DESC LIMIT 5
    
    2. Platform-specific quality games:
    MATCH (g:Game)-[:AVAILABLE_ON]->(p:Platform {{name: "PlayStation 4"}}) 
    WHERE g.user_review > 7.0 AND g.has_story = true
    RETURN g.name, g.summary, g.user_review ORDER BY g.user_review DESC LIMIT 5
    
    3. Vector similarity search (use for "similar to" queries):
    WITH genai.vector.encode($search_term, "OpenAI", {{token: "{openai_api_key}", endpoint: "{openai_endpoint}"}}) AS query_embedding 
    CALL db.index.vector.queryNodes('story_game_embeddings', 5, query_embedding) 
    YIELD node AS game, score 
    WHERE game.user_review > 6.0 
    RETURN game.name, game.summary, game.user_review, score ORDER BY score DESC
    
    4. Graph-based story connections:
    MATCH (g1:Game)-[r:SIMILAR_STORY]->(g2:Game) 
    WHERE g1.name CONTAINS $game_name 
    RETURN g2.name, g2.summary, g2.user_review, r.similarity ORDER BY r.similarity DESC LIMIT 3
    
    5. Genre-based recommendations:
    MATCH (g:Game)-[:BELONGS_TO]->(genre:Genre {{name: $genre_name}})
    WHERE g.user_review > 7.5
    RETURN g.name, g.summary, g.user_review ORDER BY g.user_review DESC LIMIT 5
    
    6. Platform quality connections:
    MATCH (seed:Game)-[:SAME_PLATFORM]->(rec:Game)
    WHERE seed.name CONTAINS $game_name AND rec.user_review > 8.0
    RETURN rec.name, rec.summary, rec.user_review ORDER BY rec.user_review DESC LIMIT 3

    Question: {question}
    """

    QA_TEMPLATE = """
    You are a passionate gaming curator specializing in narrative experiences.
    Focus on story elements, character development, and emotional impact.
    Use the provided context to give detailed, enthusiastic recommendations.

    Context: {context}
    Question: {question}

    Provide detailed explanations about:
    - Why these games match the request
    - Story highlights and themes
    - Emotional impact and character development
    - What makes each narrative special

    Answer:
    """

    cypher_prompt = PromptTemplate.from_template(CYPHER_TEMPLATE)
    qa_prompt = PromptTemplate.from_template(QA_TEMPLATE)

    return GraphCypherQAChain.from_llm(
        llm,
        graph=kg,
        cypher_prompt=cypher_prompt,
        qa_prompt=qa_prompt,
        verbose=True,
        allow_dangerous_requests=True
    ), kg

def semantic_search(kg, query, top_k=5):
    try:
        result = kg.query("""
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
        """, params={
            'openAiApiKey': os.getenv("OPENAI_API_KEY"),
            'openAiEndpoint': os.getenv("OPENAI_ENDPOINT_EMBEDDINGS"),
            'question': query,
            'top_k': top_k
        })
        return result
    except Exception as e:
        st.error(f"Semantic search failed: {e}")
        return []

def graph_traversal_search(kg, game_name):
    try:
        result = kg.query("""
        MATCH (g:Game)
        WHERE toLower(g.name) CONTAINS toLower($game_name)
        OPTIONAL MATCH (g)-[r:SIMILAR_STORY]->(similar:Game)
        OPTIONAL MATCH (g)-[:SAME_PLATFORM]->(platform_rec:Game)
        WHERE platform_rec.user_review > 7.5
        RETURN g.name as original_game,
               g.summary as original_summary,
               collect(DISTINCT {name: similar.name, similarity: r.similarity})[0..3] as similar_games,
               collect(DISTINCT platform_rec.name)[0..3] as platform_recommendations
        LIMIT 1
        """, params={'game_name': game_name})
        return result
    except Exception as e:
        st.error(f"Graph search failed: {e}")
        return []

def hybrid_ragat_search(kg, query):
    semantic_results = semantic_search(kg, query, 3)
    
    graph_results = []
    game_keywords = ['witcher', 'zelda', 'mass effect', 'final fantasy', 'last of us', 'god of war', 'horizon']
    for keyword in game_keywords:
        if keyword in query.lower():
            graph_results = graph_traversal_search(kg, keyword)
            break
    
    return semantic_results, graph_results

chain, kg = initialize_system()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def process_question(prompt):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Searching for story gems..."):
            try:
                if any(word in prompt.lower() for word in ['similar', 'like', 'recommend based on']):
                    st.info("🔍 Using hybrid RAG+Graph search for personalized recommendations")
                    semantic_results, graph_results = hybrid_ragat_search(kg, prompt)
                    
                    response_parts = []
                    if semantic_results:
                        response_parts.append("**📚 Story Matches from AI Analysis:**")
                        for game in semantic_results[:3]:
                            rating = f" ({game['game.user_review']}/10)" if game['game.user_review'] else ""
                            response_parts.append(f"• **{game['game.name']}**{rating}")
                            response_parts.append(f"  _{game['game.summary'][:120]}..._")
                    
                    if graph_results and graph_results[0]['similar_games']:
                        response_parts.append("\n**🔗 Connected Stories from Game Network:**")
                        for similar in graph_results[0]['similar_games']:
                            if similar['name']:
                                response_parts.append(f"• {similar['name']}")
                    
                    if response_parts:
                        answer = "\n".join(response_parts)
                    else:
                        answer = "No specific matches found, trying general search..."
                        response = chain.invoke({
                            'query': prompt,
                            'question': prompt,
                            'schema': kg.get_schema,
                            'openai_api_key': os.getenv("OPENAI_API_KEY"),
                            'openai_endpoint': os.getenv("OPENAI_ENDPOINT_EMBEDDINGS")
                        })
                        answer = response.get('result', 'No recommendations found.')
                else:
                    response = chain.invoke({
                        'query': prompt,
                        'question': prompt,
                        'schema': kg.get_schema,
                        'openai_api_key': os.getenv("OPENAI_API_KEY"),
                        'openai_endpoint': os.getenv("OPENAI_ENDPOINT_EMBEDDINGS")
                    })
                    answer = response.get('result', 'No story games found.')
                
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
            except Exception as e:
                error_msg = f"Something went wrong: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

if st.session_state.selected_example:
    process_question(st.session_state.selected_example)
    st.session_state.selected_example = None

if prompt := st.chat_input("What kind of story are you looking for?"):
    process_question(prompt)

st.sidebar.header("Story Categories:")
examples = [
    "Show me the highest rated story games",
    "Find games similar to The Witcher 3",
    "What are the best PlayStation exclusives with great stories?",
    "Recommend emotional narrative games like The Last of Us",
    "Find RPGs with deep character development",
    "Show me Nintendo games with amazing stories",
    "What story games are perfect for beginners?",
    "Find adventure games with branching storylines"
]

for example in examples:
    if st.sidebar.button(example):
        st.session_state.selected_example = example
        st.rerun()