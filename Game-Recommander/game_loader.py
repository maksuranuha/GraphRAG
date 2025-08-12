import csv
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

def execute_query(driver, cypher, params=None):
    try:
        with driver.session() as session:
            return session.run(cypher, params)
    except Exception as e:
        print(f"Error: {e}")

def safe_string(value):
    return str(value).strip() if value and str(value).strip() else None

def safe_float(value):
    try:
        return float(value) if value and str(value).strip() else None
    except:
        return None

def create_constraints(driver):
    constraints = [
        "CREATE CONSTRAINT game_id IF NOT EXISTS FOR (g:Game) REQUIRE g.game_id IS UNIQUE",
        "CREATE CONSTRAINT platform_name IF NOT EXISTS FOR (p:Platform) REQUIRE p.name IS UNIQUE"
    ]
    for constraint in constraints:
        execute_query(driver, constraint)

def create_indexes(driver):
    indexes = [
        "CREATE INDEX game_name IF NOT EXISTS FOR (g:Game) ON (g.name)",
        "CREATE INDEX game_rating IF NOT EXISTS FOR (g:Game) ON (g.user_review)",
        "CREATE INDEX platform_name_idx IF NOT EXISTS FOR (p:Platform) ON (p.name)"
    ]
    for index in indexes:
        execute_query(driver, index)

def create_game_node(driver, game_id, name, platform, release_date, summary, user_review):
    query = """
    MERGE (g:Game {game_id: $game_id})
    SET g.name = $name,
        g.platform = $platform,
        g.release_date = $release_date,
        g.summary = $summary,
        g.user_review = $user_review,
        g.has_story = CASE WHEN $summary IS NOT NULL THEN true ELSE false END
    """
    execute_query(driver, query, {
        'game_id': game_id,
        'name': name,
        'platform': platform,
        'release_date': release_date,
        'summary': summary,
        'user_review': user_review
    })

def create_platform_node(driver, platform):
    if platform:
        execute_query(driver, "MERGE (p:Platform {name: $platform})", {'platform': platform})

def create_relationships(driver, game_id, platform):
    if platform:
        query = """
        MATCH (g:Game {game_id: $game_id}), (p:Platform {name: $platform})
        MERGE (g)-[:AVAILABLE_ON]->(p)
        """
        execute_query(driver, query, {'game_id': game_id, 'platform': platform})

def create_rating_relationships(driver):
    print("Creating rating-based relationships...")
    execute_query(driver, """
    MATCH (g1:Game), (g2:Game)
    WHERE g1 <> g2 
      AND g1.user_review IS NOT NULL 
      AND g2.user_review IS NOT NULL
      AND abs(g1.user_review - g2.user_review) <= 0.5
      AND g1.user_review > 7.0
    MERGE (g1)-[:SIMILAR_RATING]->(g2)
    """)

def create_platform_relationships(driver):
    print("Creating platform-based relationships...")
    execute_query(driver, """
    MATCH (g1:Game)-[:AVAILABLE_ON]->(p:Platform)<-[:AVAILABLE_ON]-(g2:Game)
    WHERE g1 <> g2 
      AND g1.user_review > 7.0 
      AND g2.user_review > 7.0
    MERGE (g1)-[:SAME_PLATFORM]->(g2)
    """)

def main():
    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
    )
    execute_query(driver, "MATCH (n) DETACH DELETE n")
    
    print("Creating constraints and indexes...")
    create_constraints(driver)
    create_indexes(driver)
    
    row_count = 0
    with open("data/video_games.csv", "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            row_count += 1
            if row_count % 100 == 0:
                print(f"Processed {row_count} games...")
            
            game_id = f"game_{row_count}"
            name = safe_string(row["name"])
            platform = safe_string(row["platform"])
            release_date = safe_string(row["release_date"])
            summary = safe_string(row["summary"])
            user_review = safe_float(row["user_review"])
            
            if not name or not summary:
                continue
                
            create_game_node(driver, game_id, name, platform, release_date, summary, user_review)
            create_platform_node(driver, platform)
            create_relationships(driver, game_id, platform)
    
    print("Creating advanced relationships...")
    create_rating_relationships(driver)
    create_platform_relationships(driver)
    
    with driver.session() as session:
        stats = session.run("""
        RETURN 
            count{(g:Game)} as games,
            count{(p:Platform)} as platforms,
            count{()-[:AVAILABLE_ON]->()} as platform_relations,
            count{()-[:SIMILAR_RATING]->()} as rating_relations
        """).single()
        
        print(f"\nDatabase loaded successfully:")
        print(f"Games: {stats['games']}")
        print(f"Platforms: {stats['platforms']}")
        print(f"Platform relationships: {stats['platform_relations']}")
        print(f"Rating relationships: {stats['rating_relations']}")
    
    driver.close()

if __name__ == "__main__":
    main()