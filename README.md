## 📖 What is a Knowledge Graph?
<img width="1702" height="464" alt="Graph_RAG" src="https://github.com/user-attachments/assets/389fd1cb-0a43-4c07-90bb-91603ba4846d" />
Knowledge Graph - Semantic Network of Real World Entities simply, a way to show how things are connected to each other.
Eg. : Events, Situations, concept -> it illustrates the relationship between them! 

Suppose, a 5 years old talking with a friend about his family and pets. And he introduced them as:
- "My mom and dad are a person."
- "Mom and Dad are married."
- "I am their child."
- "We have a dog, his name is Tom"
- "Tom is a dog."
- "Dogs are animals."

Now turn that into a knowledge graph:

| Subject | Relationship | Object |
|---------|-------------|--------|
| Mom | Is a | Person |
| Dad | Is a | Person |
| Mom | Married to | Dad |
| I | Child of | Mom |
| I | Child of | Dad |
| We | Have | Tom |
| Tom | Is a | Dog |
| Dog | Is an | animal |

### How does your brain take this information? 

It looks something like this: 
This is a knowledge graph! Such as: 
- Your brain stores facts like this
- You understand relationships between things
- You can trace answers like:
  - Who is Tom? → Tom → is a → Dog
  - Who are my parents? → I → child of → Mom & Dad
  - What kind of creature is Tom? → Tom → is a → Dog → is a → Animal

### Visual Diagram for the example:
```
Mom ───── is a ─────▶ Person  
Dad ───── is a ─────▶ Person  
Mom ─── married to ─▶ Dad  
I   ─── child of ───▶ Mom  
I   ─── child of ───▶ Dad  
We  ───── have ─────▶ Tom  
Tom ───── is a ─────▶ Dog  
Dog ───── is a ─────▶ Animal
```

## 🧠 Why do we learn Knowledge Graphs?

### They Mirror How Humans Think 
Our brains naturally connect ideas:
 "Tom is a dog → dogs are animals → animals need food"
Knowledge graphs map this relational thinking in a structured way.
They help machines (and us) think like humans do — in webs, not just flat facts.
They help to resonate complex facts with relationships between them!

### They Make Reasoning Explainable
In AI, if an LLM gives you an answer, you don't always know why.
With a graph: We can identify name, entity, relationship
You can trace:
 "Tom → is a Dog → Dogs are Animals → Animals need food"
Every step is transparent and verifiable
That's called explainability, a mandatory factor for transparent AI.

## 🔍 Search Technologies Explained

### RAG (Retrieval Augmented Generation)
RAG: Retrieval + LLM, it's about what you do with the search results (give to LLM). If I ask any question about a particular document that my model is trained with, I shall be able to extract that particular information. It finds relevant parts by converting words into vectors similar words stay close, opposites far. These vectors go into a database. Then hybrid search finds the best matches and sends them to the LLM to generate your answer.

### Hybrid Search
Hybrid Search: Semantic Search (meaning) + Keyword Search (exact words), it's about how you search.

#### Keyword Search
Keyword Search: More focus to the keywords - Bow, TFIDF
Imagine you have a big box of letters from friends. You want to find all letters that mention "birthday" and "cake."
- You look through each letter and see if it has the words "birthday" and "cake."
- You pull out only the letters that mention both words.
So you look for letters that mention both "birthday" and "cake" — you pick only those letters with both words.

| Ref | Sentence | birthday | cake |
|-----|----------|----------|------|
| 1 | "Happy birthday! Hope you have fun." | 1 | 0 |
| 2 | "I baked a chocolate cake for you." | 0 | 1 |
| 3 | "Wishing you a happy birthday with a cake." | 1 | 1 |
| 4 | "See you soon!" | 0 | 0 |

**NB**: when we are doing Keyword search with Sparse matrix, we can get overfitting. 

Imagine you have 3 letters and 3 keywords:
Keywords: lion, roars, tiger

| Ref | lion | roars | tiger |
|-----|------|-------|-------|
| 1 | 1 | 1 | 0 |
| 2 | 0 | 1 | 0 |
| 3 | 0 | 0 | 1 |

What does this mean?
- Letter 1 talks about lion and roars
- Letter 2 only has roars
- Letter 3 only has tiger

Now, say you want to find letters that mention "lion":
Your search vector looks like: [1, 0, 0] (lion = 1, roars = 0, tiger = 0)

Matching:
- Letter 1: [1, 1, 0] → has lion (1), so match!
- Letter 2: [0, 1, 0] → no lion (0), no match
- Letter 3: [0, 0, 1] → no lion (0), no match

So only Letter 1 matches your keyword search!

**Why is this limited?**
If you search for "lion" ([1,0,0]), you won't find Letter 3 about "tiger" even though they're related animals.

This simple matrix is called a sparse matrix because most of the numbers are zeros, meaning most keywords don't appear in most letters. The models are having 0's and 1's and just at one place it will be 1 right? For each keyword in a document, the vector usually has a 1 if the keyword appears, and 0 if it doesn't. So, at any position in that vector, it's either a 0 or a 1, never more than one. It tends to overfit with respect to our training dataset!

#### Semantic Search
Semantic Search uses dense vectors and a similarity score to find results based on meaning, not exact words. For example, if I search for "lion," it gets converted into a vector like [........]. Like: The word "lion" is passed into a pretrained model, which converts it into a dense vector, a list of numbers that captures its meaning. Then the system checks in the vector database [.........] to find the most similar vectors, meaning similar ideas and returns the closest match.

To make performance better, we use hybrid search, which combines semantic search (meaning) and keyword search (exact words) for more accurate results.

## 🗄️ Database Technologies

### Graph Databases
Graph databases store data as nodes and edges, directly modeling relationships. This makes querying connections (like paths, patterns) fast and intuitive.
Unlike relational databases (tables with joins) or vector stores (meaning-based similarity), graph databases preserve both structure and context, making them ideal for reasoning over connected data.

#### Why Graph Database?
They store relationships in nodes, preserving relationships and contexts, you can quickly uncover patterns and find deeper insights without needing any joints. No complex joining.

#### Difference between RDBMS and Graph DB:

| RDBMS | Graph DB |
|-------|----------|
| Table | Graph |
| Insert Records (Rows) | Insert Nodes (circle) |
| Columns & Data | Properties & Values |
| Constraints -> Primary, foreign, candidate keys | Relationship - My dog's name is TOM |
| SQL Query | Cypher Query Language - declarative query language to represent the graph |
| Complex joins | No nested query joins |

#### Example Scenario:
You want to store this info: "Alice knows Bob, and Bob likes chocolate."

**1. Relational Database (SQL): MYSQL, SQL etc**
Remember trying to find "what Alice's friend likes" in traditional databases? You'd need complex joins and multiple tables! 
Stores in tables, using foreign keys + joins:

**Traditional Database (SQL):**
| ID | Name | Knows | Likes |
|----|------|-------|-------|
| 1 | Alice | Bob | |
| 2 | Bob | | Chocolate |

You need joins to find relationships like "What does Alice's friend like?"

**2. Graph Database:**
Stores data as nodes and relationships:
```
(Alice) —[KNOWS]→ (Bob) —[LIKES]→ (Chocolate)
```
Easy to ask: "What does Alice's friend like?" Without complex joins.

Graph databases store data as nodes and edges, directly modeling relationships. This makes querying connections (like paths, patterns) fast and intuitive. Unlike relational databases (tables with joins) or vector stores (meaning-based similarity), graph databases preserve both structure and context, making them ideal for reasoning over connected data.
