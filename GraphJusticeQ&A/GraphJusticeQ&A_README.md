# 🔍 GraphJusticeQ&A with Neo4j

A **Knowledge Graph-based Question Answering (KGQA)** system that enables natural language exploration over Interpol fugitive data, powered by **Neo4j**, **LangChain**, and **LLMs**.

---

## 🚧 Motivation

Global law enforcement agencies often release structured datasets of fugitives or persons of interest. However, these datasets are not easily searchable in natural language or interlinked contextually. This project demonstrates how **Knowledge Graphs + LLMs** can bridge that gap.

We aim to show how **real-world law enforcement data** can be transformed into an explainable and queryable graph interface using modern AI pipelines.

---

## 🛠️ Tech Stack Overview

| Component         | Purpose                                            |
|------------------|----------------------------------------------------|
| 🧠 **Neo4j AuraDB**     | Graph database to model relationships in data   |
| 🔗 **LangChain**        | Chains the LLM + Cypher query generation        |
| 🤖 **Groq LLM**         | Translates questions into graph queries         |
| 🐍 **Python**           | Orchestrates the whole pipeline                 |

---

## 🌐 Neo4j AuraDB

**Neo4j AuraDB** is a fully managed cloud-based graph database that enables real-time graph analysis with zero infrastructure hassle. It uses a **Property Graph Model** consisting of:

- 🟢 **Nodes** — Represent entities like `Fugitive`, `Country`, `Crime`, `Organization`
- 🔗 **Relationships** — Connect nodes (e.g., `WANTED_FOR`, `HAS_NATIONALITY`, `BELIEVED_IN_COUNTRY`)
- 🧩 **Properties** — Key-value pairs holding attributes for nodes and edges

> Think of it like:  
> **Entities (nodes)** + **Context (relationships)** + **Attributes (properties)** = A graph you can ask questions about.

---

## 📦 Dataset
The dataset used in this project is derived from publicly available Interpol Red Notice records, compiled and hosted in the following GitHub repository:  
📂 **Fugitives.csv** — [View on GitHub](https://github.com/ali-ce/datasets/blob/master/Interpol-Most-Wanted/Fugitives.csv)

This CSV file includes fields such as fugitive name, age, nationality, sex, wanted status, crime details, and Red Notice profile links.
---

## 📥 Data Ingestion

We use a simple Cypher script to directly load and model the data from the GitHub CSV:

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
## 🔗 Example Relationships

```cypher
(:Fugitive)-[:HAS_NATIONALITY]->(:Country)
(:Fugitive)-[:WANTED_BY]->(:Organization)
(:Fugitive)-[:WANTED_FOR]->(:Crime)
(:Fugitive)-[:BELIEVED_IN_COUNTRY]->(:Country)
```
## 🧠 System Architecture
```cypher
                ┌──────────────┐
                │  User Query  │
                └──────┬───────┘
                       ↓
                ┌──────────────┐
                │  LangChain   │ ← Prompt templates + LLM
                └──────┬───────┘
                       ↓
                ┌──────────────┐
                │   Groq LLM   │ ← Natural language → Cypher
                └──────┬───────┘
                       ↓
                ┌──────────────┐
                │   Neo4j DB   │ ← Query and retrieve
                └──────┬───────┘
                       ↓
                ┌──────────────┐
                │ Final Answer │
                └──────────────┘
```
## 💻 Code Highlights

- 🔍 **Load CSV Data**: Fugitives loaded directly from a remote GitHub CSV  
- 📜 **Narrative Transformation**: Each fugitive record is turned into a human-readable paragraph  
- ✂️ **Smart Chunking**: Data is split for token-efficient LLM ingestion  
- 🕸️ **Entity & Relationship Extraction**: Using `LLMGraphTransformer`, structured knowledge is extracted  
- 🌐 **Graph Creation in Neo4j**: Entities like `Person`, `Crime`, `Country`, `Org` are instantiated and linked  
- ❓ **Natural Language Q&A**: `GraphCypherQAChain` turns user queries into Cypher → executes → returns answer  
- 🧠 **CLI Interface**: Lightweight interactive chat in your terminal  

---

## 📊 Sample Graph Stats

| Entity Type    | Count |
|----------------|-------|
| Fugitives      | 95    |
| Countries      | 85    |
| Organizations  | 50    |
| Crime Types    | 49    |

---

## 💬 Sample Questions

These are real questions users can ask:

- "How many fugitives are in the database?"
- "Who is wanted by the FBI?"
- "Are there any female fugitives?"
- "Which fugitives are hiding in Brazil?"
- "What crimes is John Doe wanted for?"

---

## 🧪 Example Output

```bash
🔍 GraphJusticeQ&A
Type 'quit' to exit

You: Show me fugitives from the United States
🤖 Kenneth Andrew CRAIG, Bailey Martin COULTER, ... are fugitives from the United States.

You: How many male vs female fugitives are there?
🤖 There are 92 male fugitives and 3 female fugitives.

## 🔧 Installation & Setup

### Prerequisites

- Google Colab or local Python 3.8+
- Neo4j AuraDB account
- Groq API key

### Configure Environment

```python
NEO4J_URI = "neo4j+s://your-database-uri"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "your-password"
GROQ_API_KEY = "your-groq-api-key"


## 🧠 Why This Matters

This project combines:

- Real-world data (Interpol)
- Knowledge graph modeling
- Prompt-engineered Cypher generation
- Interactive, explainable Q&A over graph data

It serves as a **template** for building trustworthy, explainable, and interactive AI systems for:

- Law enforcement  
- Research labs  
- Investigative journalism  
- AI education and graph reasoning tasks

