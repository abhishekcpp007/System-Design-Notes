---
title: "Database Fundamentals"
part: 1
chapter: 4
difficulty: "Beginner"
---

# Chapter 4: Database Fundamentals

> *"Every system design interview comes down to: how do you store and retrieve data efficiently?"*

Databases are at the heart of every system. This chapter covers everything you need to know before diving into system design.

---

## 4.1 SQL vs NoSQL

The most fundamental database decision. Let's understand both deeply.

### Relational Databases (SQL)

Data organized in **tables** with **rows** and **columns**. Relationships between tables via foreign keys.

```mermaid
erDiagram
    USERS {
        int id PK
        string name
        string email
        timestamp created_at
    }
    ORDERS {
        int id PK
        int user_id FK
        decimal total
        string status
        timestamp created_at
    }
    ORDER_ITEMS {
        int id PK
        int order_id FK
        int product_id FK
        int quantity
        decimal price
    }
    PRODUCTS {
        int id PK
        string name
        decimal price
        int stock
    }
    
    USERS ||--o{ ORDERS : places
    ORDERS ||--o{ ORDER_ITEMS : contains
    PRODUCTS ||--o{ ORDER_ITEMS : "is in"
```

**Popular SQL databases**: PostgreSQL, MySQL, SQLite, Oracle, SQL Server

### NoSQL Databases

"Not Only SQL" — designed for specific access patterns:

```mermaid
graph TD
    subgraph "Document Store"
        D1["MongoDB, CouchDB"]
        D2["{ 'name': 'Alice',<br/>  'orders': [...],<br/>  'address': {...} }"]
    end
    
    subgraph "Key-Value Store"
        KV1["Redis, DynamoDB"]
        KV2["user:123 → { blob of data }"]
    end
    
    subgraph "Column-Family"
        CF1["Cassandra, HBase"]
        CF2["Row Key → { col1: v1, col2: v2 }"]
    end
    
    subgraph "Graph Database"
        G1["Neo4j, Amazon Neptune"]
        G2["(Alice)--[FRIENDS]--(Bob)"]
    end
```

### SQL vs NoSQL Comparison:

| Feature | SQL | NoSQL |
|---------|-----|-------|
| **Schema** | Strict, predefined | Flexible, schema-less |
| **Relationships** | Joins, foreign keys | Denormalized, embedded |
| **Scaling** | Vertical (bigger machine) | Horizontal (more machines) |
| **Transactions** | Full ACID | Varies (eventual consistency common) |
| **Query Language** | SQL (standardized) | Custom per database |
| **Best For** | Complex queries, relationships | High write throughput, flexible schema |

### When to Use What:

```mermaid
flowchart TD
    A[Choosing a Database] --> B{Need complex joins<br/>and transactions?}
    B -->|Yes| C[SQL<br/>PostgreSQL, MySQL]
    B -->|No| D{Data structure?}
    D -->|"JSON-like documents"| E[Document DB<br/>MongoDB]
    D -->|"Simple key→value"| F[Key-Value<br/>Redis, DynamoDB]
    D -->|"Relationships/graphs"| G[Graph DB<br/>Neo4j]
    D -->|"Time-series / analytics"| H[Column Store<br/>Cassandra, ClickHouse]
    D -->|"Full-text search"| I[Search Engine<br/>Elasticsearch]
    
    style C fill:#4ecdc4,color:#fff
    style E fill:#ff6b6b,color:#fff
    style F fill:#45b7d1,color:#fff
    style G fill:#96ceb4,color:#fff
    style H fill:#dda0dd,color:#000
    style I fill:#ffa07a,color:#000
```

---

## 4.2 ACID Properties

ACID is what makes relational databases reliable. Every letter matters:

### Atomicity — All or Nothing

A transaction either completes entirely or has no effect.

```mermaid
sequenceDiagram
    participant App
    participant DB

    Note over App,DB: Transfer $100 from Alice to Bob
    App->>DB: BEGIN TRANSACTION
    App->>DB: UPDATE accounts SET balance = balance - 100 WHERE user = 'Alice'
    App->>DB: UPDATE accounts SET balance = balance + 100 WHERE user = 'Bob'
    
    alt Success
        App->>DB: COMMIT
        Note over DB: Both changes saved ✅
    else Failure (crash, error)
        App->>DB: ROLLBACK
        Note over DB: Both changes undone ✅<br/>No partial state
    end
```

### Consistency — Valid State to Valid State

Database moves from one valid state to another. All rules (constraints, foreign keys) are enforced.

### Isolation — Transactions Don't Interfere

Concurrent transactions behave as if they ran sequentially.

**Isolation Levels** (from weakest to strongest):

| Level | Dirty Read | Non-repeatable Read | Phantom Read | Performance |
|-------|-----------|--------------------|--------------|-----------:|
| Read Uncommitted | ✅ Possible | ✅ Possible | ✅ Possible | Fastest |
| **Read Committed** | ❌ Prevented | ✅ Possible | ✅ Possible | Fast |
| **Repeatable Read** | ❌ Prevented | ❌ Prevented | ✅ Possible | Medium |
| **Serializable** | ❌ Prevented | ❌ Prevented | ❌ Prevented | Slowest |

```mermaid
graph LR
    A["Read Uncommitted<br/>🏎️ Fast, Unsafe"] --> B["Read Committed<br/>🚗 Default in PostgreSQL"]
    B --> C["Repeatable Read<br/>🚌 Default in MySQL"]
    C --> D["Serializable<br/>🐌 Safest, Slowest"]
    
    style A fill:#ff6b6b,color:#fff
    style D fill:#4ecdc4,color:#fff
```

**Dirty Read**: Reading uncommitted changes from another transaction.
**Non-repeatable Read**: Reading same row twice gives different results (another transaction modified it).
**Phantom Read**: Re-executing a query returns new rows (another transaction inserted rows).

### Durability — Committed = Permanent

Once committed, data survives crashes. Achieved through:
- Write-Ahead Log (WAL) — write log to disk before applying changes
- Checkpointing — periodically write all changes to disk

---

## 4.3 Indexes — Making Queries Fast

Without an index, the database scans every row (O(n)). With an index, it jumps to the right row (O(log n)).

### B-Tree Index (Default):

```mermaid
graph TD
    Root["[30, 60]"]
    Root --> L1["[10, 20]"]
    Root --> L2["[40, 50]"]
    Root --> L3["[70, 80, 90]"]
    
    L1 --> D1["Data: rows with id 1-10"]
    L1 --> D2["Data: rows with id 11-20"]
    L1 --> D3["Data: rows with id 21-29"]
    
    L2 --> D4["Data: rows with id 31-40"]
    L2 --> D5["Data: rows with id 41-50"]
    L2 --> D6["Data: rows with id 51-59"]
    
    L3 --> D7["Data: rows with id 61-70"]
    L3 --> D8["Data: rows with id 71-80"]
    L3 --> D9["Data: rows with id 81-90"]
    L3 --> D10["Data: rows with id 91+"]

    style Root fill:#ff6b6b,color:#fff
    style L1 fill:#4ecdc4,color:#fff
    style L2 fill:#4ecdc4,color:#fff
    style L3 fill:#4ecdc4,color:#fff
```

**Finding id = 45**:
1. Start at root: 45 > 30 and 45 < 60 → go middle
2. At [40, 50]: 45 > 40 and 45 < 50 → go middle
3. Read data page → found!

**Only 3 steps** instead of scanning all rows!

### Index Types:

| Index Type | Use Case | Example |
|-----------|----------|---------|
| **B-Tree** (default) | Equality & range queries | `WHERE age > 25` |
| **Hash** | Exact equality only | `WHERE email = 'alice@example.com'` |
| **Composite** | Multi-column queries | `WHERE country = 'US' AND city = 'SF'` |
| **Full-text** | Text search | `WHERE content LIKE '%system design%'` |
| **GIN/GiST** | JSON, arrays, spatial | `WHERE tags @> '["postgres"]'` |

### The Cost of Indexes:

```mermaid
graph LR
    subgraph "Without Index"
        R1["Read: O(n) SLOW ❌"]
        W1["Write: O(1) FAST ✅"]
    end
    
    subgraph "With Index"
        R2["Read: O(log n) FAST ✅"]
        W2["Write: O(log n) SLOWER<br/>(must update index too)"]
    end
```

**Rule of thumb**: 
- Index columns used in WHERE, JOIN, ORDER BY
- Don't over-index (each index slows writes and uses storage)
- Composite index order matters: `(country, city)` helps `WHERE country = ?` but NOT `WHERE city = ?`

### Explain Query Plans:

```sql
-- Always check if your index is being used!
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'alice@example.com';

-- Good: "Index Scan using idx_users_email"
-- Bad: "Seq Scan on users" (full table scan!)
```

---

## 4.4 Normalization vs Denormalization

### Normalization — Eliminate Redundancy

Break data into related tables to avoid duplication:

```mermaid
graph LR
    subgraph "Unnormalized (Bad)"
        T1["Orders Table<br/>order_id | user_name | user_email | product_name | product_price<br/>1 | Alice | alice@email.com | Laptop | 999<br/>2 | Alice | alice@email.com | Mouse | 29"]
    end
    
    subgraph "Normalized (Good)"
        Users["Users<br/>id | name | email<br/>1 | Alice | alice@email.com"]
        Products["Products<br/>id | name | price<br/>1 | Laptop | 999<br/>2 | Mouse | 29"]
        Orders2["Orders<br/>id | user_id | product_id<br/>1 | 1 | 1<br/>2 | 1 | 2"]
    end
```

**Benefits**: No duplicate data, easier updates, less storage.
**Cost**: Need JOINs to reconstruct data → slower reads.

### Denormalization — Optimize for Reads

Intentionally duplicate data for faster reads:

```sql
-- Normalized: requires JOIN (slower)
SELECT u.name, o.total 
FROM orders o JOIN users u ON o.user_id = u.id;

-- Denormalized: no JOIN needed (faster)
SELECT user_name, total FROM orders;
-- (user_name is duplicated in orders table)
```

### When to Use Which:

| Approach | When | Example |
|----------|------|---------|
| **Normalize** | Write-heavy, data integrity critical | Banking, ERP |
| **Denormalize** | Read-heavy, speed critical | Social media feeds, analytics |
| **Hybrid** | Most real systems | Normalized DB + denormalized cache |

---

## 4.5 Transactions and Concurrency Control

### What is a Transaction?

A group of operations that execute as a single unit:

```sql
BEGIN TRANSACTION;
    UPDATE accounts SET balance = balance - 100 WHERE id = 1;  -- Debit Alice
    UPDATE accounts SET balance = balance + 100 WHERE id = 2;  -- Credit Bob
COMMIT;  -- Both succeed or both fail
```

### Concurrency Control Mechanisms:

```mermaid
graph TD
    A[Concurrency Control] --> B[Pessimistic<br/>Lock before access]
    A --> C[Optimistic<br/>Detect conflicts after]
    
    B --> B1["Shared Lock (Read Lock)<br/>Multiple readers allowed"]
    B --> B2["Exclusive Lock (Write Lock)<br/>Only one writer, no readers"]
    
    C --> C1["Version number check<br/>UPDATE ... WHERE version = 5"]
    C --> C2["Timestamp ordering<br/>Older transaction wins"]
```

### Pessimistic Locking:

```sql
-- Thread 1: Lock the row before modifying
SELECT * FROM products WHERE id = 1 FOR UPDATE;  -- Acquires row lock
UPDATE products SET stock = stock - 1 WHERE id = 1;
COMMIT;  -- Releases lock

-- Thread 2 waits until Thread 1 commits
```

### Optimistic Locking:

```sql
-- Thread 1: Read current version
SELECT stock, version FROM products WHERE id = 1;
-- stock = 10, version = 5

-- Thread 1: Update only if version hasn't changed
UPDATE products 
SET stock = 9, version = 6 
WHERE id = 1 AND version = 5;
-- If 0 rows affected → someone else modified it → retry!
```

**When to use**:
- **Pessimistic**: High contention (many writers to same row) — banking
- **Optimistic**: Low contention (conflicts are rare) — e-commerce product pages

---

## 4.6 Types of NoSQL Databases (Deep Dive)

### Key-Value Stores

**What**: Simple key → value mapping. Think of it as a giant hash map.

| Database | Persistence | Best For |
|----------|------------|---------|
| **Redis** | In-memory (optional persistence) | Cache, sessions, leaderboards |
| **Memcached** | In-memory only | Simple caching |
| **DynamoDB** | Persistent, fully managed | Serverless, auto-scaling |

```python
# Redis example
import redis
r = redis.Redis()

r.set("user:123", '{"name": "Alice", "email": "alice@example.com"}')
r.get("user:123")  # Returns the JSON string
r.expire("user:123", 3600)  # TTL: 1 hour
```

### Document Stores

**What**: Store JSON-like documents. Each document can have different fields.

```json
// MongoDB document - no fixed schema!
{
  "_id": "user_123",
  "name": "Alice",
  "email": "alice@example.com",
  "addresses": [
    {"street": "123 Main St", "city": "SF", "state": "CA"},
    {"street": "456 Oak Ave", "city": "NYC", "state": "NY"}
  ],
  "preferences": {
    "theme": "dark",
    "notifications": true
  }
}
```

### Column-Family Stores

**What**: Data organized by columns rather than rows. Excellent for analytics.

```mermaid
graph TD
    subgraph "Row-Oriented (SQL)"
        R1["Row 1: Alice | 25 | SF | Engineer"]
        R2["Row 2: Bob | 30 | NYC | Designer"]
        R3["Row 3: Charlie | 28 | LA | Manager"]
    end
    
    subgraph "Column-Oriented (Cassandra)"
        C1["Names: Alice | Bob | Charlie"]
        C2["Ages: 25 | 30 | 28"]
        C3["Cities: SF | NYC | LA"]
        C4["Roles: Engineer | Designer | Manager"]
    end
```

**Why column-oriented is better for analytics**:
- Query `SELECT AVG(age) FROM users` only reads the age column
- Row-oriented must read ALL columns of ALL rows (wasted I/O)
- Column data compresses better (similar values together)

### Graph Databases

**What**: Data modeled as nodes and edges. Perfect for relationship-heavy data.

```mermaid
graph LR
    Alice((Alice)) -->|FRIENDS| Bob((Bob))
    Alice -->|FRIENDS| Charlie((Charlie))
    Bob -->|FOLLOWS| Alice
    Charlie -->|WORKS_AT| Google((Google))
    Alice -->|WORKS_AT| Meta((Meta))
    Bob -->|WORKS_AT| Google
    
    style Alice fill:#ff6b6b,color:#fff
    style Bob fill:#4ecdc4,color:#fff
    style Charlie fill:#45b7d1,color:#fff
    style Google fill:#ffd93d,color:#000
    style Meta fill:#6c5ce7,color:#fff
```

**Use cases**: Social networks, recommendation engines, fraud detection, knowledge graphs

---

## 4.7 Database Internals — How Storage Works

### B-Tree vs LSM-Tree

The two fundamental storage engine approaches:

```mermaid
graph TD
    subgraph "B-Tree (PostgreSQL, MySQL InnoDB)"
        BT1["Read-optimized"]
        BT2["Update data in-place"]
        BT3["Good for: read-heavy workloads"]
    end
    
    subgraph "LSM-Tree (Cassandra, RocksDB, LevelDB)"
        LSM1["Write-optimized"]
        LSM2["Append to sorted files (SSTables)"]
        LSM3["Good for: write-heavy workloads"]
    end
```

### LSM-Tree Write Path:

```mermaid
sequenceDiagram
    participant App
    participant WAL as WAL (Disk)
    participant MT as MemTable (RAM)
    participant L0 as Level 0 (Disk)
    participant L1 as Level 1 (Disk)

    App->>WAL: 1. Write to WAL (durability)
    App->>MT: 2. Write to MemTable (fast, in-memory)
    
    Note over MT: When MemTable is full...
    MT->>L0: 3. Flush to disk as SSTable
    
    Note over L0,L1: Background compaction
    L0->>L1: 4. Merge & compact SSTables
```

**Key tradeoff**:
- **B-Tree**: Fast reads (data in-place), slower writes (random I/O)
- **LSM-Tree**: Fast writes (sequential I/O), slower reads (may check multiple levels), write amplification

---

## 4.8 SQL Query Fundamentals

### JOINs Visualized:

```mermaid
graph TD
    subgraph "INNER JOIN"
        IJ["Only matching rows from both tables"]
    end
    
    subgraph "LEFT JOIN"
        LJ["All rows from LEFT table<br/>+ matching from right<br/>NULL if no match"]
    end
    
    subgraph "RIGHT JOIN"
        RJ["All rows from RIGHT table<br/>+ matching from left<br/>NULL if no match"]
    end
    
    subgraph "FULL OUTER JOIN"
        FOJ["All rows from BOTH tables<br/>NULL where no match"]
    end
```

### Common SQL Patterns for System Design:

```sql
-- Pagination (offset-based)
SELECT * FROM posts ORDER BY created_at DESC LIMIT 20 OFFSET 40;
-- Problem: OFFSET 1000000 is SLOW (scans and discards rows)

-- Pagination (cursor-based — MUCH better)
SELECT * FROM posts 
WHERE created_at < '2024-01-15T10:30:00' 
ORDER BY created_at DESC 
LIMIT 20;

-- Aggregation
SELECT country, COUNT(*) as user_count 
FROM users 
GROUP BY country 
HAVING COUNT(*) > 1000
ORDER BY user_count DESC;

-- Subquery
SELECT * FROM users 
WHERE id IN (SELECT user_id FROM orders WHERE total > 100);

-- Window function (advanced)
SELECT name, salary, 
       RANK() OVER (PARTITION BY department ORDER BY salary DESC) as dept_rank
FROM employees;
```

---

## Key Takeaways

| Concept | System Design Impact |
|---------|---------------------|
| SQL vs NoSQL | Choose based on data relationships and access patterns |
| ACID | Required for financial, inventory — may sacrifice for performance |
| Indexes | Difference between 10ms and 10s queries |
| Normalization/Denormalization | Tradeoff between write and read performance |
| Locking strategies | Affect concurrent user handling |
| Storage engines | B-Tree for reads, LSM-Tree for writes |
| Cursor pagination | Required for infinite scroll at scale |

---

## Practice Questions

1. **Design**: You're building a social media feed. Would you normalize (users table + posts table + follows table) or denormalize (pre-computed feed per user)? What are the tradeoffs?

2. **Index**: A table has 100 million rows. The query `SELECT * FROM orders WHERE user_id = 123 AND status = 'pending' ORDER BY created_at DESC` is slow. What index would you create?

3. **NoSQL Choice**: For each use case, pick the best database type and explain:
   - User session storage
   - Product catalog with varying attributes
   - Social graph (friends of friends)
   - Real-time analytics on billions of events

4. **Transactions**: Two users simultaneously try to buy the last item in stock. How do you prevent overselling? Compare pessimistic vs optimistic approaches.

5. **Storage Engine**: You're building a logging system that writes 100,000 log entries per second and rarely reads them. Would you choose a B-Tree or LSM-Tree based storage engine? Why?

---

*Previous: [← Operating System Basics](./ch03-operating-system-basics.md) | Next: [OOP Principles →](../part2-lld/ch05-oop-principles.md)*
