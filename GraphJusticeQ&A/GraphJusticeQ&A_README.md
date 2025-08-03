
# 🔍 GraphJusticeQ&A
A Knowledge Graph-based Question Answering system for Interpol fugitive data using Neo4j, LangChain, and LLMs.

## Implementation
We built this using:
- **Neo4j AuraDB**: Our graph database brain
- **LangChain**: For connecting everything together  
- **Groq LLM**: The AI that understands your questions
- **Python**: Because, well, Python is the Base

The system automatically converts natural language questions into database queries, searches the graph, and gives you human-friendly answers.

### Dataset
We're using real Interpol fugitive data from:
```
https://github.com/ali-ce/datasets/blob/master/Interpol-Most-Wanted/Fugitives.csv
```

### Data Loading with Neo4J
We are directly fetching it from web using Cypher:
```cypher
LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/ali-ce/datasets/master/Interpol-Most-Wanted/Fugitives.csv' AS row
MERGE (f:Fugitive {fugitiveId: row.Fugitive})
SET
  f.name = row.Fugitive,
  f.dateOfBirth = CASE WHEN row.`Date of Birth` =~ '\\d{4}' THEN date(row.`Date of Birth` + '-01-01') ELSE NULL END,
  f.currentAge = toInteger(row.`Current Age (approx.)`),
  f.sex = row.Sex,
  f.status = row.Status,
  f.details = row.Details,
  f.yearOfInterpolOperation = row.`Year of Interpol operation`,
  f.source = row.Source,
  f.interpolRedNoticeProfile = row.`Interpol Red Notice Profile`,
  f.image = row.Image,
  f.reasonDetails = row.`Details of reason wanted for`
```

- **Fugitive HAS_NATIONALITY→ Country**: Connects the fugitive to their nationality.
- **Fugitive WANTED_BY→ Organization**: Connects the fugitive to the organization (e.g., Belarus, FBI) who is requesting their arrest.
- **Fugitive WANTED_FOR→ Crime**: Connects the fugitive to the type of crime they are wanted for (e.g., Fraud, Theft).
- **Fugitive BELIEVED_IN_COUNTRY→ Country**: Connects the fugitive to one or more countries they may be hiding in (e.g., Angola, Ukraine, Russia).

## 🚀 Installation and Setup

### Prerequisites
- Colab
- Neo4j AuraDB account
- Groq API key

### Environment Setup
```python
# Neo4j Configuration from neo4j auradb!
NEO4J_URI = "neo4j+s://your-database-uri"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "your-password"

# Groq API Configuration
GROQ_API_KEY = "your-groq-api-key"
```

## 💻 Code Implementation

1. **🔍 Loads Data**  
   Reads a CSV of Interpol fugitives directly from GitHub.

2. **🧾 Converts Rows to Narrative**  
   Each fugitive's record is transformed into a story-style paragraph.

3. **✂️ Splits Text**  
   Chunks text into smaller segments for better LLM parsing.

4. **🔄 Transforms Text to Graph**  
   Uses `LLMGraphTransformer` to extract entities like Person, Crime, Country, etc.

5. **🏗️ Builds Neo4j Graph**  
   Creates nodes and relationships:  
   - `Person`, `Location`, `Organization`, `Crime`  
   - `WANTED_FOR`, `HIDING_IN`, `CITIZEN_OF`, `WANTED_BY`

6. **❓ Natural Language Q&A**  
   `GraphCypherQAChain` converts user questions → Cypher queries → answers.

7. **💬 Interactive CLI Chat**  
   Terminal-based chatbot to explore fugitives, locations, crimes, and agencies.

---
---

## 📊 Graph Stats

| Type         | Count |
|--------------|-------|
| Fugitives    | 95    |
| Countries    | 85    |
| Organizations| 50    |
| Crime Types  | 49    |

---

## 💡 Example Questions

- “How many fugitives are in the database?”
- “Who is wanted by the FBI?”
- “Are there any female fugitives?”
- “Which fugitives are hiding in Brazil?”
- “What crimes is John Doe wanted for?”

---

## 🎯 Example Usage

```
🔍 GraphJusticeQ&A
Type 'quit' to exit

You: Show me fugitives from the United States
🤖 Searching...
GraphJusticeQ&A: Kenneth Andrew CRAIG, Bailey Martin COULTER, Christopher Ward DEININGER, John Edward HAMILTON, Frank Cornelis LEFRANDT Jr., Catherine Elizabeth GREIG, Robert William FISHER are fugitives from the United States.
(Query: Counted fugitives)
------------------------------

You: How many male vs female fugitives are there?
🤖 Searching...
GraphJusticeQ&A: There are 92 male fugitives and 3 female fugitives.
(Query: Searched database)
------------------------------
```

## 🔧 Features

- **Natural Language Queries**: Ask questions in plain English
- **Graph-Based Reasoning**: Leverages relationship data for accurate answers
- **Real-time Search**: Interactive chat interface for dynamic queries
- **Explainable AI**: Shows the Cypher queries generated for transparency
- **Multi-relationship Support**: Handles complex relationships between entities

## 🎯 Use Cases

- **Law Enforcement**: Quick access to fugitive information
- **Research**: Academic studies on criminal patterns
- **Journalism**: Investigative reporting support
- **Education**: Learning about knowledge graphs and AI

## ⚠️ Disclaimer

This project is for educational and research purposes only. The data used is from publicly available Interpol sources.
Always verify information through official channels for any real-world applications.


