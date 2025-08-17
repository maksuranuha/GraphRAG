import os
from dotenv import load_dotenv
from langchain_neo4j import Neo4jGraph
from openai import OpenAI
from tavily import TavilyClient
import time
from typing import List, Dict
import numpy as np
import re
import hashlib

load_dotenv()

class AIGADetectionSystem:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        self.kg = Neo4jGraph(
            url=os.getenv("NEO4J_URI"),
            username=os.getenv("NEO4J_USERNAME"), 
            password=os.getenv("NEO4J_PASSWORD"),
            database=os.getenv("NEO4J_DATABASE", "neo4j")
        )
        
    def create_vector_indices(self):
        indices = [
            {
                'name': 'abstract_embeddings',
                'label': 'Abstract',
                'property': 'embedding',
                'dimensions': 1536,
                'similarity': 'cosine'
            },
            {
                'name': 'plagiarism_embeddings',
                'label': 'Abstract',
                'property': 'plagiarism_embedding', 
                'dimensions': 1536,
                'similarity': 'cosine'
            }
        ]
        
        for idx in indices:
            query = f"""
            CREATE VECTOR INDEX {idx['name']} IF NOT EXISTS
            FOR (n:{idx['label']}) ON (n.{idx['property']})
            OPTIONS {{
                indexConfig: {{
                    `vector.dimensions`: {idx['dimensions']},
                    `vector.similarity_function`: '{idx['similarity']}'
                }}
            }}
            """
            try:
                self.kg.query(query)
                print(f"✓ Created index: {idx['name']}")
            except Exception as e:
                print(f"Index {idx['name']} might exist: {e}")

    def get_embedding(self, text: str, model="text-embedding-3-small") -> List[float]:
        try:
            text = text.replace("\n", " ").strip()
            text = text[:8000] if len(text) > 8000 else text
            
            response = self.openai_client.embeddings.create(input=[text], model=model)
            return response.data[0].embedding
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return None

    def check_plagiarism_with_tavily(self, text: str, title: str = "") -> Dict:
        try:
            key_phrases = self.extract_key_phrases(text)
            plagiarism_results = {
                'found_matches': 0,
                'total_searches': 0,
                'matches': [],
                'plagiarism_score': 0.0
            }
            
            for phrase in key_phrases[:3]: 
                if len(phrase) > 10:  
                    search_query = f'"{phrase}"'  
                    
                    try:
                        response = self.tavily_client.search(
                            query=search_query,
                            search_depth="basic",
                            max_results=5,
                            include_domains=["pubmed.ncbi.nlm.nih.gov", "arxiv.org", "biorxiv.org", "medrxiv.org"]
                        )
                        
                        plagiarism_results['total_searches'] += 1
                        
                        if response.get('results'):
                            for result in response['results']:
                                content = result.get('content', '')
                                if self.check_text_similarity(phrase, content):
                                    plagiarism_results['found_matches'] += 1
                                    plagiarism_results['matches'].append({
                                        'phrase': phrase,
                                        'url': result.get('url'),
                                        'title': result.get('title'),
                                        'snippet': content[:200]
                                    })
                        
                        time.sleep(0.5) 
                        
                    except Exception as e:
                        print(f"Tavily search error: {e}")
                        continue
            
            if plagiarism_results['total_searches'] > 0:
                plagiarism_results['plagiarism_score'] = plagiarism_results['found_matches'] / plagiarism_results['total_searches']
            
            return plagiarism_results
            
        except Exception as e:
            print(f"Plagiarism check error: {e}")
            return {'found_matches': 0, 'total_searches': 0, 'matches': [], 'plagiarism_score': 0.0}

    def extract_key_phrases(self, text: str, min_length: int = 15) -> List[str]:
        sentences = text.split('.')
        phrases = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) >= min_length and not self.is_generic_phrase(sentence):
                phrases.append(sentence)
                
        words = text.split()
        for i in range(len(words) - 7):
            phrase = ' '.join(words[i:i+8])
            if len(phrase) >= min_length and not self.is_generic_phrase(phrase):
                phrases.append(phrase)
                
        return phrases[:10]  

    def is_generic_phrase(self, phrase: str) -> bool:
        generic_words = ['the', 'this', 'that', 'these', 'those', 'in', 'on', 'at', 'to', 'for', 'of', 'with']
        words = phrase.lower().split()
        generic_count = sum(1 for word in words if word in generic_words)
        return generic_count / len(words) > 0.6 if words else True

    def check_text_similarity(self, phrase1: str, phrase2: str, threshold: float = 0.8) -> bool:
        words1 = set(phrase1.lower().split())
        words2 = set(phrase2.lower().split())
        
        if not words1 or not words2:
            return False
            
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        jaccard_similarity = len(intersection) / len(union)
        return jaccard_similarity > threshold

    def create_enhanced_abstract_embeddings(self):
        abstracts = self.kg.query("""
            MATCH (a:Abstract)
            WHERE a.embedding IS NULL
            OPTIONAL MATCH (a)-[:CONTAINS_KEYWORD]->(k:Keyword)
            OPTIONAL MATCH (a)-[:HAS_PATTERN]->(p:Pattern)
            RETURN a.id, a.title, a.text, a.generated, a.word_count, a.type,
                   a.avg_sentence_length, a.unique_word_ratio, a.flesch_reading_ease,
                   a.connector_density, a.hedging_density, a.covid_terms, a.ai_phrase_count,
                   collect(DISTINCT k.name)[..10] as keywords,
                   collect(DISTINCT p.name)[..5] as patterns
            LIMIT 500
        """)
        
        processed = 0
        for abstract in abstracts:
            context_text = self._build_ai_detection_context(abstract)
            content_embedding = self.get_embedding(context_text)
            
            if content_embedding:
                plagiarism_results = self.check_plagiarism_with_tavily(
                    abstract.get('a.text', ''), 
                    abstract.get('a.title', '')
                )
                
                plagiarism_context = self._build_plagiarism_context(abstract, plagiarism_results)
                plagiarism_embedding = self.get_embedding(plagiarism_context)
                
                ai_score = self._calculate_enhanced_ai_likelihood_score(abstract)
                
                self.kg.query("""
                    MATCH (a:Abstract {id: $id})
                    SET a.embedding = $content_embedding,
                        a.plagiarism_embedding = $plagiarism_embedding,
                        a.plagiarism_score = $plagiarism_score,
                        a.plagiarism_matches = $plagiarism_matches,
                        a.ai_likelihood_score = $ai_score,
                        a.plagiarism_checked = true
                """, {
                    'id': abstract['a.id'],
                    'content_embedding': content_embedding,
                    'plagiarism_embedding': plagiarism_embedding,
                    'plagiarism_score': plagiarism_results['plagiarism_score'],
                    'plagiarism_matches': len(plagiarism_results['matches']),
                    'ai_score': ai_score
                })
                
                for match in plagiarism_results['matches']:
                    match_id = f"match_{hashlib.md5(match['url'].encode()).hexdigest()[:8]}"
                    self.kg.query("""
                        MERGE (m:PlagiarismMatch {id: $match_id})
                        SET m.url = $url,
                            m.title = $title,
                            m.snippet = $snippet,
                            m.phrase = $phrase
                    """, {
                        'match_id': match_id,
                        'url': match.get('url', ''),
                        'title': match.get('title', ''),
                        'snippet': match.get('snippet', ''),
                        'phrase': match.get('phrase', '')
                    })
                    
                    self.kg.query("""
                        MATCH (a:Abstract {id: $abstract_id}), (m:PlagiarismMatch {id: $match_id})
                        MERGE (a)-[:HAS_PLAGIARISM_MATCH]->(m)
                    """, {'abstract_id': abstract['a.id'], 'match_id': match_id})
                
                processed += 1
                if processed % 50 == 0:
                    print(f"Processed {processed} abstracts (with plagiarism check)")
                    time.sleep(1)  
                    
    def _build_ai_detection_context(self, abstract):
        title = abstract.get('a.title', '')
        text = abstract.get('a.text', '')
        keywords = abstract.get('keywords', [])
        patterns = abstract.get('patterns', [])
        
        connector_density = abstract.get('a.connector_density', 0)
        hedging_density = abstract.get('a.hedging_density', 0)
        ai_phrases = abstract.get('a.ai_phrase_count', 0)
        
        context = f"Title: {title}\n\nAbstract: {text}\n\n"
        
        if keywords:
            context += f"Keywords: {', '.join(keywords[:10])}\n\n"
            
        if patterns:
            context += f"Linguistic patterns: {', '.join(patterns)}\n\n"
            
        if connector_density > 0.02:
            context += "High connector word usage detected.\n"
        if hedging_density > 0.015:
            context += "High hedging language detected.\n"
        if ai_phrases > 1:
            context += "Formal AI-style phrases detected.\n"
            
        return context

    def _build_plagiarism_context(self, abstract, plagiarism_results):
        text = abstract.get('a.text', '')
        title = abstract.get('a.title', '')
        
        context = f"Title: {title}\nText: {text}\n\n"
        
        if plagiarism_results['matches']:
            context += "Potential plagiarism matches found:\n"
            for match in plagiarism_results['matches'][:3]:
                context += f"- {match.get('phrase', '')[:100]}...\n"
                
        context += f"Plagiarism score: {plagiarism_results['plagiarism_score']:.3f}"
        return context

    def _calculate_enhanced_ai_likelihood_score(self, abstract) -> float:
        score = 0.0
        
        connector_density = abstract.get('a.connector_density', 0)
        if connector_density > 0.025:
            score += 0.35
        elif connector_density > 0.02:
            score += 0.20
        elif connector_density > 0.015:
            score += 0.10
            
        hedging_density = abstract.get('a.hedging_density', 0)
        if hedging_density > 0.025:
            score += 0.30
        elif hedging_density > 0.02:
            score += 0.20
        elif hedging_density > 0.015:
            score += 0.10
            
        ai_phrase_count = abstract.get('a.ai_phrase_count', 0)
        if ai_phrase_count > 2:
            score += 0.25
        elif ai_phrase_count > 1:
            score += 0.15
        elif ai_phrase_count > 0:
            score += 0.05
            
        avg_sent_len = abstract.get('a.avg_sentence_length', 0)
        if 22 <= avg_sent_len <= 32:  
            score += 0.20
        elif avg_sent_len > 35:  
            score += 0.10
            
        readability = abstract.get('a.flesch_reading_ease', 0)
        covid_terms = abstract.get('a.covid_terms', 0)
        if readability > 55 and covid_terms > 3:
            score += 0.15
        elif readability > 60:
            score += 0.10
            
        unique_ratio = abstract.get('a.unique_word_ratio', 1)
        if unique_ratio < 0.7:
            score += 0.15
        elif unique_ratio < 0.75:
            score += 0.10
            
        return min(score, 1.0)

    def find_similar_abstracts(self, text: str, limit: int = 5, threshold: float = 0.8):
        embedding = self.get_embedding(text)
        if not embedding:
            return []
            
        similar = self.kg.query("""
            CALL db.index.vector.queryNodes('abstract_embeddings', $limit, $embedding)
            YIELD node, score
            WHERE score > $threshold
            RETURN node.id as id, node.title as title, node.generated as generated,
                   node.ai_likelihood_score as ai_score, score
            ORDER BY score DESC
        """, {
            'embedding': embedding,
            'limit': limit,
            'threshold': threshold
        })
        
        return list(similar)

    def detect_ai_text(self, text: str, title: str = "") -> Dict:
        similar_abstracts = self.find_similar_abstracts(f"{title} {text}")
        from collections import Counter
        import nltk
        from nltk.tokenize import word_tokenize, sent_tokenize
        
        sentences = sent_tokenize(text)
        words = word_tokenize(text.lower())
        words_clean = [w for w in words if w.isalpha()]
        
        ai_connectors = ['furthermore', 'moreover', 'additionally', 'consequently', 'therefore', 
                        'however', 'nevertheless', 'nonetheless', 'in contrast', 'similarly',
                        'specifically', 'particularly', 'notably', 'importantly', 'essentially']
        ai_phrases = ['it is important to note', 'it should be noted', 'it is worth noting',
                     'in conclusion', 'in summary', 'to summarize', 'overall', 'in general']
        
        connector_count = sum(1 for word in words_clean if word in ai_connectors)
        ai_phrase_count = sum(1 for phrase in ai_phrases if phrase in text.lower())
        
        features = {
            'word_count': len(words_clean),
            'avg_sentence_length': len(words_clean) / len(sentences) if sentences else 0,
            'connector_density': connector_count / len(words_clean) if words_clean else 0,
            'ai_phrase_count': ai_phrase_count,
            'unique_word_ratio': len(set(words_clean)) / len(words_clean) if words_clean else 0
        }
        
        ai_score = 0.0
        if features['connector_density'] > 0.025:
            ai_score += 0.35
        if features['ai_phrase_count'] > 1:
            ai_score += 0.25
        if 22 <= features['avg_sentence_length'] <= 32:
            ai_score += 0.20
        if features['unique_word_ratio'] < 0.7:
            ai_score += 0.15
            
        result = {
            'ai_probability': min(ai_score, 1.0),
            'prediction': 'AI Generated' if ai_score > 0.5 else 'Human Written',
            'confidence': abs(ai_score - 0.5) * 2, 
            'features': features,
            'similar_abstracts': similar_abstracts,
            'reasoning': self._generate_reasoning(features, ai_score)
        }
        
        return result

    def _generate_reasoning(self, features, ai_score):
        reasoning = []
        if features['connector_density'] > 0.025:
            reasoning.append("High usage of connecting words typical of AI writing")
        if features['ai_phrase_count'] > 1:
            reasoning.append("Multiple formal phrases commonly used by AI models")
        if 22 <= features['avg_sentence_length'] <= 32:
            reasoning.append("Sentence length in typical AI range")
        if features['unique_word_ratio'] < 0.7:
            reasoning.append("Lower vocabulary diversity suggests AI generation")
        
        if not reasoning:
            reasoning.append("Features suggest human writing patterns")
            
        return "; ".join(reasoning)

    def batch_process_texts(self, texts_with_metadata: List[Dict]):
        results = []
        
        for item in texts_with_metadata:
            text = item.get('text', '')
            title = item.get('title', '')
            
            if len(text) < 50:  
                continue
                
            result = self.detect_ai_text(text, title)
            result['metadata'] = item
            results.append(result)
            
        return results

    def get_detection_stats(self):
        stats = self.kg.query("""
            MATCH (a:Abstract)
            WHERE a.ai_likelihood_score IS NOT NULL
            RETURN a.generated as actual,
                   count(*) as count,
                   avg(a.ai_likelihood_score) as avg_ai_score,
                   min(a.ai_likelihood_score) as min_score,
                   max(a.ai_likelihood_score) as max_score
        """)
        
        return list(stats)

if __name__ == "__main__":
    detector = AIGADetectionSystem()
    detector.create_vector_indices()
    detector.create_enhanced_abstract_embeddings()
    
    sample_text = """
    This study aims to investigate the potential impact of COVID-19 on healthcare systems. 
    Furthermore, we analyze the effectiveness of various intervention strategies. 
    The results suggest that comprehensive approaches are significantly more effective. 
    In conclusion, it is important to note that coordinated responses yield better outcomes.
    """
    
    result = detector.detect_ai_text(sample_text, "COVID-19 Healthcare Analysis")
    print(f"Prediction: {result['prediction']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"AI Probability: {result['ai_probability']:.2f}")
    print(f"Reasoning: {result['reasoning']}")