import pandas as pd
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
import hashlib
import re
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
import spacy
import numpy as np
from textstat import flesch_reading_ease, flesch_kincaid_grade, automated_readability_index

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Install spacy model: python -m spacy download en_core_web_sm")
    nlp = None

load_dotenv()

class AIGALoader:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"), 
            auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
        )
        self.db = os.getenv("NEO4J_DATABASE", "neo4j")
        self.stop_words = set(stopwords.words('english'))
        
    def execute_query(self, query, params=None):
        with self.driver.session(database=self.db) as session:
            return session.run(query, params or {})

    def extract_ai_linguistic_features(self, text):
        """Extract linguistic features that distinguish AI from human abstracts"""
        if not text or len(text) < 20:
            return {}
            
        sentences = sent_tokenize(text)
        words = word_tokenize(text.lower())
        words_clean = [w for w in words if w.isalpha()]
        
        # Enhanced AI patterns for better detection
        ai_connectors = ['furthermore', 'moreover', 'additionally', 'consequently', 'therefore', 
                        'however', 'nevertheless', 'nonetheless', 'in contrast', 'similarly',
                        'specifically', 'particularly', 'notably', 'importantly', 'essentially']
        ai_hedging = ['potentially', 'possibly', 'likely', 'suggests', 'indicates', 'appears',
                     'seems', 'tends', 'might', 'could', 'may', 'presumably', 'apparently']
        ai_intensifiers = ['significantly', 'substantially', 'considerably', 'notably', 'remarkably',
                          'particularly', 'especially', 'exceptionally', 'extremely', 'highly']
        
        # AI-specific phrase patterns
        ai_phrases = ['it is important to note', 'it should be noted', 'it is worth noting',
                     'in conclusion', 'in summary', 'to summarize', 'overall', 'in general']
        
        connector_count = sum(1 for word in words_clean if word in ai_connectors)
        hedging_count = sum(1 for word in words_clean if word in ai_hedging)
        intensifier_count = sum(1 for word in words_clean if word in ai_intensifiers)
        
        # Count AI phrases
        text_lower = text.lower()
        ai_phrase_count = sum(1 for phrase in ai_phrases if phrase in text_lower)
        
        features = {
            'word_count': len(words_clean),
            'sentence_count': len(sentences),
            'avg_sentence_length': len(words_clean) / len(sentences) if sentences else 0,
            'avg_word_length': np.mean([len(w) for w in words_clean]) if words_clean else 0,
            'unique_word_ratio': len(set(words_clean)) / len(words_clean) if words_clean else 0,
            'punctuation_density': sum(1 for c in text if c in '.,;:!?()[]') / len(text) if text else 0,
            'connector_density': connector_count / len(words_clean) if words_clean else 0,
            'hedging_density': hedging_count / len(words_clean) if words_clean else 0,
            'intensifier_density': intensifier_count / len(words_clean) if words_clean else 0,
            'ai_phrase_count': ai_phrase_count,
            'flesch_reading_ease': flesch_reading_ease(text),
            'flesch_kincaid_grade': flesch_kincaid_grade(text),
            'automated_readability': automated_readability_index(text),
            'covid_terms': self._count_covid_terms(text)
        }
        
        if nlp:
            doc = nlp(text[:1000])  # Limit for performance
            pos_counts = Counter([token.pos_ for token in doc])
            total_tokens = len(doc)
            
            features.update({
                'noun_ratio': pos_counts.get('NOUN', 0) / total_tokens if total_tokens else 0,
                'verb_ratio': pos_counts.get('VERB', 0) / total_tokens if total_tokens else 0,
                'adj_ratio': pos_counts.get('ADJ', 0) / total_tokens if total_tokens else 0,
                'adv_ratio': pos_counts.get('ADV', 0) / total_tokens if total_tokens else 0,
                'entity_count': len(doc.ents),
                'entity_density': len(doc.ents) / total_tokens if total_tokens else 0
            })
            
        return features

    def _count_covid_terms(self, text):
        """Count COVID-19 related terms"""
        covid_terms = ['covid', 'coronavirus', 'sars-cov-2', 'pandemic', 'lockdown', 
                      'vaccine', 'vaccination', 'quarantine', 'social distancing', 'mask',
                      'ventilator', 'icu', 'hospital', 'mortality', 'symptom']
        text_lower = text.lower()
        return sum(1 for term in covid_terms if term in text_lower)

    def extract_keywords(self, abstract, title="", max_keywords=15):
        """Enhanced keyword extraction for AI-GA abstracts"""
        combined = f"{title} {abstract}" if abstract else title
        if not combined:
            return []
            
        # Remove common academic phrases first
        academic_stopwords = ['study', 'research', 'analysis', 'paper', 'article', 
                             'findings', 'results', 'conclusion', 'method', 'approach']
        
        if nlp:
            doc = nlp(combined.lower())
            keywords = []
            
            for token in doc:
                if (token.is_alpha and len(token.text) > 3 and not token.is_stop 
                    and token.pos_ in ['NOUN', 'ADJ', 'VERB'] 
                    and token.lemma_ not in academic_stopwords):
                    keywords.append(token.lemma_)
                    
            # Add COVID-specific terms
            covid_keywords = ['covid19', 'coronavirus', 'pandemic', 'vaccine', 'healthcare']
            for keyword in covid_keywords:
                if keyword in combined.lower():
                    keywords.append(keyword)
                    
        else:
            tokens = word_tokenize(combined.lower())
            keywords = [word for word in tokens 
                       if word.isalpha() and len(word) > 3 
                       and word not in self.stop_words 
                       and word not in academic_stopwords]
        
        return [word for word, _ in Counter(keywords).most_common(max_keywords)]

    def create_constraints(self):
        constraints = [
            "CREATE CONSTRAINT abstract_id IF NOT EXISTS FOR (a:Abstract) REQUIRE a.id IS UNIQUE",
            "CREATE CONSTRAINT keyword_name IF NOT EXISTS FOR (k:Keyword) REQUIRE k.name IS UNIQUE",
            "CREATE CONSTRAINT pattern_name IF NOT EXISTS FOR (p:Pattern) REQUIRE p.name IS UNIQUE"
        ]
        
        for constraint in constraints:
            try:
                self.execute_query(constraint)
            except Exception as e:
                print(f"Constraint might already exist: {e}")

    def load_ai_ga_dataset(self, file_path):
        print(f"Loading AI-GA dataset from {file_path}")
        
        df = pd.read_csv(file_path)
        processed = 0
        
        for _, row in df.iterrows():
            abstract = str(row.get('abstract', '')).strip()
            title = str(row.get('title', '')).strip()
            label = bool(row.get('label', 0))  # 1 = AI generated, 0 = human
            
            if not abstract or abstract == 'nan' or len(abstract) < 30:
                continue
            
            abstract_id = f"aiga_{hashlib.md5((title + abstract[:50]).encode()).hexdigest()[:12]}"
            keywords = self.extract_keywords(abstract, title)
            features = self.extract_ai_linguistic_features(abstract)
            
            # Create abstract node with comprehensive features
            self.execute_query("""
                MERGE (a:Abstract {id: $id})
                SET a.title = $title,
                    a.text = $abstract,
                    a.generated = $generated,
                    a.type = $type,
                    a.source = 'ai_ga_dataset',
                    a.domain = 'covid19_research',
                    a.word_count = $word_count,
                    a.sentence_count = $sentence_count,
                    a.avg_sentence_length = $avg_sentence_length,
                    a.avg_word_length = $avg_word_length,
                    a.unique_word_ratio = $unique_word_ratio,
                    a.punctuation_density = $punctuation_density,
                    a.connector_density = $connector_density,
                    a.hedging_density = $hedging_density,
                    a.intensifier_density = $intensifier_density,
                    a.ai_phrase_count = $ai_phrase_count,
                    a.flesch_reading_ease = $flesch_reading_ease,
                    a.flesch_kincaid_grade = $flesch_kincaid_grade,
                    a.automated_readability = $automated_readability,
                    a.covid_terms = $covid_terms,
                    a.noun_ratio = $noun_ratio,
                    a.verb_ratio = $verb_ratio,
                    a.adj_ratio = $adj_ratio,
                    a.adv_ratio = $adv_ratio,
                    a.entity_count = $entity_count,
                    a.entity_density = $entity_density
            """, {
                'id': abstract_id, 'title': title, 'abstract': abstract,
                'generated': label, 
                'type': 'ai_generated' if label else 'human_written',
                **features
            })
            
            # Add keywords
            for keyword in keywords:
                self.execute_query("MERGE (k:Keyword {name: $name})", {'name': keyword})
                self.execute_query("""
                    MATCH (a:Abstract {id: $abstract_id}), (k:Keyword {name: $keyword})
                    MERGE (a)-[:CONTAINS_KEYWORD]->(k)
                """, {'abstract_id': abstract_id, 'keyword': keyword})
            
            # Create AI pattern analysis - enhanced for better detection
            if features['connector_density'] > 0.025:  # Increased threshold
                self.execute_query("MERGE (p:Pattern {name: 'high_connectors', type: 'ai_indicator'})")
                self.execute_query("""
                    MATCH (a:Abstract {id: $abstract_id}), (p:Pattern {name: 'high_connectors'})
                    MERGE (a)-[:HAS_PATTERN]->(p)
                """, {'abstract_id': abstract_id})
                
            if features['hedging_density'] > 0.02:  # Increased threshold
                self.execute_query("MERGE (p:Pattern {name: 'high_hedging', type: 'ai_indicator'})")
                self.execute_query("""
                    MATCH (a:Abstract {id: $abstract_id}), (p:Pattern {name: 'high_hedging'})
                    MERGE (a)-[:HAS_PATTERN]->(p)
                """, {'abstract_id': abstract_id})
            
            if features['ai_phrase_count'] > 1:  # New pattern for AI phrases
                self.execute_query("MERGE (p:Pattern {name: 'formal_phrases', type: 'ai_indicator'})")
                self.execute_query("""
                    MATCH (a:Abstract {id: $abstract_id}), (p:Pattern {name: 'formal_phrases'})
                    MERGE (a)-[:HAS_PATTERN]->(p)
                """, {'abstract_id': abstract_id})
                
            if features['avg_sentence_length'] > 28:  # Adjusted for better detection
                self.execute_query("MERGE (p:Pattern {name: 'long_sentences', type: 'complexity_indicator'})")
                self.execute_query("""
                    MATCH (a:Abstract {id: $abstract_id}), (p:Pattern {name: 'long_sentences'})
                    MERGE (a)-[:HAS_PATTERN]->(p)
                """, {'abstract_id': abstract_id})
            
            processed += 1
            if processed % 1000 == 0:
                print(f"Processed {processed} abstracts")
        
        return processed

    def clear_database(self):
        print("Clearing existing data...")
        self.execute_query("MATCH (n) DETACH DELETE n")

    def show_detailed_stats(self):
        stats = {}
        
        # Basic counts
        result = self.execute_query("MATCH (a:Abstract) RETURN count(a) as count").single()
        stats['total_abstracts'] = result['count'] if result else 0
        
        result = self.execute_query("MATCH (a:Abstract {generated: true}) RETURN count(a) as count").single()
        stats['ai_abstracts'] = result['count'] if result else 0
        
        result = self.execute_query("MATCH (k:Keyword) RETURN count(k) as count").single()
        stats['keywords'] = result['count'] if result else 0
        
        result = self.execute_query("MATCH (p:Pattern) RETURN count(p) as count").single()
        stats['patterns'] = result['count'] if result else 0
        
        print(f"\n{'='*60}")
        print("AI-GA DATASET ANALYSIS")
        print(f"{'='*60}")
        print(f"Total Abstracts: {stats['total_abstracts']}")
        print(f"  - AI Generated: {stats['ai_abstracts']}")
        print(f"  - Human Written: {stats['total_abstracts'] - stats['ai_abstracts']}")
        print(f"Keywords Extracted: {stats['keywords']}")
        print(f"AI Patterns Found: {stats['patterns']}")
        
        # Enhanced feature comparison
        print(f"\n{'='*40}")
        print("ENHANCED LINGUISTIC FEATURES")
        print(f"{'='*40}")
        
        ai_features = self.execute_query("""
            MATCH (a:Abstract {generated: true})
            RETURN avg(a.avg_sentence_length) as avg_sent_len,
                   avg(a.connector_density) as avg_connectors,
                   avg(a.hedging_density) as avg_hedging,
                   avg(a.unique_word_ratio) as avg_uniqueness,
                   avg(a.flesch_reading_ease) as avg_readability,
                   avg(a.ai_phrase_count) as avg_ai_phrases
        """).single()
        
        human_features = self.execute_query("""
            MATCH (a:Abstract {generated: false})
            RETURN avg(a.avg_sentence_length) as avg_sent_len,
                   avg(a.connector_density) as avg_connectors,
                   avg(a.hedging_density) as avg_hedging,
                   avg(a.unique_word_ratio) as avg_uniqueness,
                   avg(a.flesch_reading_ease) as avg_readability,
                   avg(a.ai_phrase_count) as avg_ai_phrases
        """).single()
        
        if ai_features and human_features:
            print("Average Sentence Length:")
            print(f"  AI: {ai_features['avg_sent_len']:.2f} | Human: {human_features['avg_sent_len']:.2f}")
            print("Connector Density:")
            print(f"  AI: {ai_features['avg_connectors']:.4f} | Human: {human_features['avg_connectors']:.4f}")
            print("Hedging Language:")
            print(f"  AI: {ai_features['avg_hedging']:.4f} | Human: {human_features['avg_hedging']:.4f}")
            print("AI Phrases Count:")
            print(f"  AI: {ai_features['avg_ai_phrases']:.2f} | Human: {human_features['avg_ai_phrases']:.2f}")
            print("Vocabulary Uniqueness:")
            print(f"  AI: {ai_features['avg_uniqueness']:.3f} | Human: {human_features['avg_uniqueness']:.3f}")
            print("Reading Ease:")
            print(f"  AI: {ai_features['avg_readability']:.2f} | Human: {human_features['avg_readability']:.2f}")

    def load_all_data(self, clear=True):
        if clear:
            self.clear_database()
            
        self.create_constraints()
        
        # Only load AI-GA dataset as requested
        if os.path.exists("data/ai-ga-dataset.csv"):
            self.load_ai_ga_dataset("data/ai-ga-dataset.csv")
        else:
            print("AI-GA dataset not found at data/ai-ga-dataset.csv")
            print("Please ensure the file exists in the data directory")
            
        self.show_detailed_stats()

    def close(self):
        self.driver.close()

if __name__ == "__main__":
    loader = AIGALoader()
    try:
        loader.load_all_data()
    finally:
        loader.close()