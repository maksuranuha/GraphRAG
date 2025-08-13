from dotenv import load_dotenv
import os
from neo4j import GraphDatabase
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle

load_dotenv()

def create_driver():
    return GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD")),
        max_connection_lifetime=10 * 60,
        keep_alive=True
    )

def test_groq_connection():
    try:
        from langchain_groq import ChatGroq
        llm = ChatGroq(
            groq_api_key=os.getenv("GROQ_API_KEY"),
            model_name="llama-3.1-8b-instant",
            temperature=0.1
        )
        response = llm.invoke("Hello")
        return True
    except Exception as e:
        print(f"Groq API failed: {e}")
        return False

def create_tfidf_embeddings(driver):
    with driver.session() as session:
        games = session.run("""
        MATCH (g:Game)
        WHERE g.name IS NOT NULL AND g.summary IS NOT NULL
        OPTIONAL MATCH (g)-[:AVAILABLE_ON]->(p:Platform)
        WITH g, collect(DISTINCT p.name) AS platforms
        RETURN g.game_id, g.name, g.summary, g.user_review, g.platform, platforms
        """).data()
    
    if not games:
        print("No games found!")
        return 0
    
    story_texts = []
    game_ids = []
    
    for game in games:
        platforms = game['platforms'] if game['platforms'] else []
        platform_text = f" available on {', '.join(platforms)}" if platforms else ""
        if not platform_text and game['g.platform']:
            platform_text = f" on {game['g.platform']}"
        
        rating_text = f" Player rating: {game['g.user_review']}/10" if game['g.user_review'] else ""
        
        story_description = f"Story Game: {game['g.name']}{platform_text}. Story: {game['g.summary']}{rating_text}"
        story_texts.append(story_description)
        game_ids.append(game['g.game_id'])
    
    vectorizer = TfidfVectorizer(
        max_features=512,
        stop_words='english',
        ngram_range=(1, 2),
        min_df=2
    )
    
    tfidf_matrix = vectorizer.fit_transform(story_texts)
    
    with open('tfidf_vectorizer.pkl', 'wb') as f:
        pickle.dump(vectorizer, f)
    
    embedded_count = 0
    
    with driver.session() as session:
        for i, game_id in enumerate(game_ids):
            try:
                embedding = tfidf_matrix[i].toarray().flatten().tolist()
                
                session.run("""
                MATCH (g:Game {game_id: $game_id})
                CALL db.create.setNodeVectorProperty(g, "embedding", $embedding)
                """, parameters={
                    'game_id': game_id,
                    'embedding': embedding
                })
                
                embedded_count += 1
                    
            except Exception as e:
                print(f"Failed to store embedding for {game_id}: {e}")
                continue
    
    print(f"Created {embedded_count} embeddings")
    return embedded_count

def create_similarity_relationships(driver):
    with driver.session() as session:
        games = session.run("""
        MATCH (g:Game)
        WHERE g.embedding IS NOT NULL AND g.user_review > 6.0
        RETURN g.game_id, g.name, g.embedding, g.user_review
        """).data()
        
        if len(games) < 2:
            print("Not enough games with embeddings")
            return
        
        embeddings = []
        game_info = []
        
        for game in games:
            embeddings.append(game['g.embedding'])
            game_info.append({
                'id': game['g.game_id'],
                'name': game['g.name'],
                'rating': game['g.user_review']
            })
        
        similarity_matrix = cosine_similarity(embeddings)
        
        relationships_created = 0
        
        for i in range(len(game_info)):
            for j in range(i + 1, len(game_info)):
                similarity = similarity_matrix[i][j]
                
                if (similarity > 0.3 and 
                    game_info[i]['rating'] > 7.0 and 
                    game_info[j]['rating'] > 7.0):
                    
                    try:
                        session.run("""
                        MATCH (g1:Game {game_id: $game_id1})
                        MATCH (g2:Game {game_id: $game_id2})
                        MERGE (g1)-[r:SIMILAR_STORY]->(g2)
                        SET r.similarity = $similarity
                        MERGE (g2)-[r2:SIMILAR_STORY]->(g1)
                        SET r2.similarity = $similarity
                        """, parameters={
                            'game_id1': game_info[i]['id'],
                            'game_id2': game_info[j]['id'],
                            'similarity': float(similarity)
                        })
                        
                        relationships_created += 1
                        
                    except Exception as e:
                        print(f"Failed to create relationship: {e}")
        
        print(f"Created {relationships_created} similarity relationships")

def main():
    driver = create_driver()
    
    if not test_groq_connection():
        print("Groq API test failed, continuing with TF-IDF embeddings...")
    
    print("Creating vector index...")
    with driver.session() as session:
        session.run("""
        CREATE VECTOR INDEX story_game_embeddings IF NOT EXISTS
        FOR (g:Game) ON (g.embedding)
        OPTIONS {
          indexConfig: {
            `vector.dimensions`: 512,
            `vector.similarity_function`: 'cosine'
          }
        }
        """)

    print("Generating embeddings...")
    embedded_count = create_tfidf_embeddings(driver)
    
    if embedded_count == 0:
        print("No embeddings created. Exiting.")
        driver.close()
        return

    create_similarity_relationships(driver)

    print("Creating genre relationships...")
    with driver.session() as session:
        session.run("""
        MATCH (g:Game)
        WHERE g.summary IS NOT NULL
        WITH g,
             CASE 
                 WHEN g.summary =~ '(?i).*(RPG|role.playing|character.*level|quest).*' THEN 'RPG'
                 WHEN g.summary =~ '(?i).*(action|combat|fight|battle).*' THEN 'Action'
                 WHEN g.summary =~ '(?i).*(adventure|explore|journey).*' THEN 'Adventure'
                 WHEN g.summary =~ '(?i).*(strategy|tactical|plan).*' THEN 'Strategy'
                 WHEN g.summary =~ '(?i).*(puzzle|solve|mystery).*' THEN 'Puzzle'
                 WHEN g.summary =~ '(?i).*(racing|car|speed).*' THEN 'Racing'
                 WHEN g.summary =~ '(?i).*(sport|football|soccer|basketball).*' THEN 'Sports'
                 ELSE 'General'
             END as detected_genre
        MERGE (genre:Genre {name: detected_genre})
        MERGE (g)-[:BELONGS_TO]->(genre)
        """)

    print("Creating platform relationships...")
    with driver.session() as session:
        session.run("""
        MATCH (g1:Game)-[:AVAILABLE_ON]->(p:Platform)<-[:AVAILABLE_ON]-(g2:Game)
        WHERE g1 <> g2 
          AND g1.user_review > 8.0 
          AND g2.user_review > 8.0
        MERGE (g1)-[r:SAME_PLATFORM]->(g2)
        SET r.platform = p.name
        """)

    with driver.session() as session:
        stats = session.run("""
        RETURN 
            count{(g:Game)} as total_games,
            count{(g:Game WHERE g.embedding IS NOT NULL)} as games_with_embeddings,
            count{()-[:SIMILAR_STORY]->()} as story_similarities,
            count{()-[:BELONGS_TO]->()} as genre_relationships,
            count{()-[:SAME_PLATFORM]->()} as platform_relationships,
            count{(genre:Genre)} as detected_genres
        """).single()

        print(f"Total games: {stats['total_games']}")
        print(f"Games with embeddings: {stats['games_with_embeddings']}")
        print(f"Story similarities: {stats['story_similarities']}")
        print(f"Genre relationships: {stats['genre_relationships']}")
        print(f"Platform relationships: {stats['platform_relationships']}")
        print(f"Detected genres: {stats['detected_genres']}")

    driver.close()

if __name__ == "__main__":
    main()