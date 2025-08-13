import csv
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
import time

load_dotenv()

def create_driver():
    return GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD")),
        max_connection_lifetime=10 * 60, 
        keep_alive=True,
        max_connection_pool_size=10, 
        connection_timeout=30,
        connection_acquisition_timeout=60  
    )

def test_connection(driver):
    try:
        with driver.session() as session:
            result = session.run("RETURN 'Connection successful' as message")
            print(result.single()["message"])
            return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

def execute_query_with_fresh_connection(driver, cypher, params=None, retries=3):
    for attempt in range(retries):
        try:
            with driver.session() as session:
                result = session.run(cypher, params)
                return list(result)
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                print(f"Waiting {2 ** attempt} seconds before retry...")
                time.sleep(2 ** attempt)
                if not test_connection(driver):
                    print("Connection lost, recreating driver...")
                    driver.close()
                    driver = create_driver()
            else:
                print(f"Query failed after {retries} attempts: {e}")
                return None
    return driver  

def execute_query(driver, cypher, params=None, retries=3):
    for attempt in range(retries):
        try:
            with driver.session() as session:
                result = session.run(cypher, params)
                return result
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"Query failed after {retries} attempts: {e}")
                return None

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
        result = execute_query(driver, constraint)
        if result is None:
            print(f"Failed to create constraint: {constraint}")

def create_indexes(driver):
    indexes = [
        "CREATE INDEX game_name IF NOT EXISTS FOR (g:Game) ON (g.name)",
        "CREATE INDEX game_rating IF NOT EXISTS FOR (g:Game) ON (g.user_review)",
        "CREATE INDEX platform_name_idx IF NOT EXISTS FOR (p:Platform) ON (p.name)"
    ]
    for index in indexes:
        result = execute_query(driver, index)
        if result is None:
            print(f"Failed to create index: {index}")

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
    return execute_query(driver, query, {
        'game_id': game_id,
        'name': name,
        'platform': platform,
        'release_date': release_date,
        'summary': summary,
        'user_review': user_review
    })

def create_platform_node(driver, platform):
    if platform:
        return execute_query(driver, "MERGE (p:Platform {name: $platform})", {'platform': platform})

def create_relationships(driver, game_id, platform):
    if platform:
        query = """
        MATCH (g:Game {game_id: $game_id}), (p:Platform {name: $platform})
        MERGE (g)-[:AVAILABLE_ON]->(p)
        """
        return execute_query(driver, query, {'game_id': game_id, 'platform': platform})

def create_rating_relationships_batched(driver):
    """Create rating relationships for top games only - avoids memory issues"""
    print("Creating rating relationships for high-quality games...")
    
    # Check how many great games we have
    check_query = """
    MATCH (g:Game) 
    WHERE toFloat(g.user_review) >= 8.5
    RETURN count(g) as excellent_games
    """
    
    result = execute_query_with_fresh_connection(driver, check_query)
    if result and len(result) > 0:
        count = result[0]['excellent_games']
        print(f"Found {count} excellent games (rating 8.5+)")
        
        if count == 0:
            print("No highly rated games found - trying lower threshold...")
            # Try with lower rating if no excellent games found
            check_query = """
            MATCH (g:Game) 
            WHERE toFloat(g.user_review) >= 7.5
            RETURN count(g) as good_games
            """
            result = execute_query_with_fresh_connection(driver, check_query)
            if result and len(result) > 0:
                count = result[0]['good_games']
                print(f"Found {count} good games (rating 7.5+)")
    
    # Connect only the best games to avoid memory problems
    print("Connecting similar high-rated games...")
    query = """
    MATCH (g1:Game), (g2:Game)
    WHERE toFloat(g1.user_review) >= 8.5 
      AND toFloat(g2.user_review) >= 8.5
      AND g1 <> g2
      AND abs(toFloat(g1.user_review) - toFloat(g2.user_review)) <= 0.4
    WITH g1, g2 LIMIT 1000
    MERGE (g1)-[:SIMILAR_RATING]->(g2)
    MERGE (g2)-[:SIMILAR_RATING]->(g1)
    RETURN count(*) as created
    """
    
    result = execute_query_with_fresh_connection(driver, query)
    
    if result and len(result) > 0 and result[0]['created']:
        created = result[0]['created'] * 2  # bidirectional relationships
        print(f"Successfully created {created} rating relationships!")
        return driver
    
    # If that didn't work, try an even simpler approach
    print("Trying with smaller batch of top games...")
    simple_query = """
    MATCH (g1:Game), (g2:Game)
    WHERE toFloat(g1.user_review) >= 9.0 
      AND toFloat(g2.user_review) >= 9.0
      AND g1 <> g2
    WITH g1, g2 LIMIT 100
    MERGE (g1)-[:SIMILAR_RATING]->(g2)
    MERGE (g2)-[:SIMILAR_RATING]->(g1)
    RETURN count(*) as created
    """
    
    result = execute_query_with_fresh_connection(driver, simple_query)
    
    if result and len(result) > 0:
        created = result[0]['created'] * 2
        print(f"Created {created} relationships between masterpiece games (9.0+ rating)")
    else:
        print("Could not create rating relationships - try using Neo4j Desktop for better memory handling")
    
    return driver

def batch_process_games(driver, games_batch):
    for game_data in games_batch:
        game_id, name, platform, release_date, summary, user_review = game_data
        
        if create_game_node(driver, game_id, name, platform, release_date, summary, user_review):
            create_platform_node(driver, platform)
            create_relationships(driver, game_id, platform)

def main():
    driver = create_driver()
    if not test_connection(driver):
        print("Cannot connect to Neo4j. Check your credentials and network.")
        return
    
    print("Clearing database...")
    if execute_query(driver, "MATCH (n) DETACH DELETE n") is None:
        print("Failed to clear database")
        return
    
    print("Creating constraints and indexes...")
    create_constraints(driver)
    create_indexes(driver)
    
    row_count = 0
    batch_size = 50
    games_batch = []
    
    try:
        with open("data/video_games.csv", "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                row_count += 1
                
                game_id = f"game_{row_count}"
                name = safe_string(row["name"])
                platform = safe_string(row["platform"])
                release_date = safe_string(row["release_date"])
                summary = safe_string(row["summary"])
                user_review = safe_float(row["user_review"])
                
                if not name or not summary:
                    continue
                
                games_batch.append((game_id, name, platform, release_date, summary, user_review))
                
                if len(games_batch) >= batch_size:
                    batch_process_games(driver, games_batch)
                    games_batch = []
                    print(f"Processed {row_count} games...")
            
            if games_batch:
                batch_process_games(driver, games_batch)
        
        print("\nStarting relationship creation...")
        print("This focuses on high-quality games to avoid memory issues...")
        
        driver = create_rating_relationships_batched(driver)
        
        # Skip platform relationships for now to avoid errors
        print("Skipping platform relationships to avoid connection issues...")
        
        print("Getting final statistics...")
        try:
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
                
                if stats['rating_relations'] > 0:
                    print(f"You have {stats['rating_relations']} rating-based connections between similar games.")
                else:
                    print(f"\nTip: Consider using Neo4j Desktop for better memory handling and more relationships.")
                    
        except Exception as e:
            print(f"Failed to get final stats: {e}")
    
    except FileNotFoundError:
        print("CSV file not found. Make sure 'data/video_games.csv' exists.")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    main()