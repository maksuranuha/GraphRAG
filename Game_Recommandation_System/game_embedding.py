from dotenv import load_dotenv
import os
from langchain_community.graphs import Neo4jGraph

load_dotenv()

kg = Neo4jGraph(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD"),
    database=os.getenv("NEO4J_DATABASE", "neo4j"),
)

print("Creating vector index...")
kg.query("""
CREATE VECTOR INDEX story_game_embeddings IF NOT EXISTS
FOR (g:Game) ON (g.embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 1536,
    `vector.similarity_function`: 'cosine'
  }
}
""")

print("Generating story-focused embeddings...")
kg.query("""
MATCH (g:Game)
WHERE g.name IS NOT NULL AND g.summary IS NOT NULL
OPTIONAL MATCH (g)-[:AVAILABLE_ON]->(p:Platform)
WITH g, collect(DISTINCT p.name) AS platforms
WITH g, 
    'Story Game: ' + g.name + 
    CASE WHEN size(platforms) > 0 
         THEN ' available on ' + reduce(s = '', platform IN platforms | s + platform + ' ') 
         ELSE CASE WHEN g.platform IS NOT NULL THEN ' on ' + g.platform ELSE '' END
    END +
    CASE WHEN g.release_date IS NOT NULL 
         THEN ' released ' + g.release_date + '. ' 
         ELSE '. ' 
    END +
    'Story: ' + g.summary +
    CASE WHEN g.user_review IS NOT NULL 
         THEN ' Player rating: ' + toString(g.user_review) + '/10' 
         ELSE '' 
    END AS story_description
WITH g, genai.vector.encode(
    story_description,
    "OpenAI",
    {
      token: $openAiApiKey,
      endpoint: $openAiEndpoint
    }) AS vector
WHERE vector IS NOT NULL
CALL db.create.setNodeVectorProperty(g, "embedding", vector)
RETURN count(g) as embedded_games
""", params={
    'openAiApiKey': os.getenv("OPENAI_API_KEY"),
    'openAiEndpoint': os.getenv("OPENAI_ENDPOINT_EMBEDDINGS")
})

print("Creating story similarity relationships...")
try:
    result = kg.query("""
    MATCH (g1:Game), (g2:Game)
    WHERE g1 <> g2 
      AND g1.embedding IS NOT NULL 
      AND g2.embedding IS NOT NULL
      AND g1.user_review > 7.0 
      AND g2.user_review > 7.0
    WITH g1, g2, 
         round(gds.similarity.cosine(g1.embedding, g2.embedding) * 1000) / 1000 as similarity
    WHERE similarity > 0.85
    MERGE (g1)-[r:SIMILAR_STORY]->(g2)
    SET r.similarity = similarity
    RETURN count(r) as story_relationships
    """)
    print(f"Created {result[0]['story_relationships']} story similarity relationships")
except Exception as e:
    print(f"Similarity relationships creation failed: {e}")
    print("Creating basic story connections instead...")
    kg.query("""
    MATCH (g1:Game)-[:AVAILABLE_ON]->(p:Platform)<-[:AVAILABLE_ON]-(g2:Game)
    WHERE g1 <> g2 
      AND g1.user_review > 8.0 
      AND g2.user_review > 8.0
      AND g1.embedding IS NOT NULL 
      AND g2.embedding IS NOT NULL
    WITH g1, g2, p
    MERGE (g1)-[r:STORY_CONNECTION]->(g2)
    SET r.connection_type = 'platform_quality'
    """)

print("Creating genre relationships from summaries...")
kg.query("""
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

stats = kg.query("""
RETURN 
    count{(g:Game)} as total_games,
    count{(g:Game WHERE g.embedding IS NOT NULL)} as games_with_embeddings,
    count{()-[:SIMILAR_STORY]->()} as story_similarities,
    count{()-[:BELONGS_TO]->()} as genre_relationships,
    count{(genre:Genre)} as detected_genres
""")

print(f"\nEmbedding Statistics:")
print(f"Total games: {stats[0]['total_games']}")
print(f"Games with embeddings: {stats[0]['games_with_embeddings']}")
print(f"Story similarities: {stats[0]['story_similarities']}")
print(f"Genre relationships: {stats[0]['genre_relationships']}")
print(f"Detected genres: {stats[0]['detected_genres']}")