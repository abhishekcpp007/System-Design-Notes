# System Design: From Zero to Hero

> A comprehensive guide covering Low-Level Design (LLD) and High-Level Design (HLD) — from fundamentals to interview mastery.

**23 chapters** · **6 parts** · **115+ practice questions** · **Mermaid diagrams** · **Python & Java code**

---

## Table of Contents

### Part 1: Foundations

Build the CS fundamentals that every system design decision rests on.

| # | Chapter | Topics | Time |
|---|---|---|---|
| 01 | [How Computers Work](part1-foundations/ch01-how-computers-work.md) | CPU, RAM, Disk, Network, memory hierarchy, latency numbers, back-of-envelope estimation | 45 min |
| 02 | [Networking Fundamentals](part1-foundations/ch02-networking-fundamentals.md) | OSI model, TCP/UDP, DNS, HTTP/1.1/2/3, REST vs gRPC vs GraphQL, WebSockets | 60 min |
| 03 | [Operating System Basics](part1-foundations/ch03-operating-system-basics.md) | Processes, threads, concurrency, locks, memory management, I/O models (epoll), file systems | 60 min |
| 04 | [Database Fundamentals](part1-foundations/ch04-database-fundamentals.md) | SQL vs NoSQL, ACID, indexes (B-Tree), normalization, transactions, storage engines (LSM-Tree) | 60 min |

### Part 2: Low-Level Design (LLD)

Object-oriented design, patterns, and real interview problems with full code solutions.

| # | Chapter | Topics | Time |
|---|---|---|---|
| 05 | [OOP Principles](part2-lld/ch05-oop-principles.md) | 4 pillars, UML class diagrams, composition vs inheritance, interfaces vs abstract classes, enums & state machines | 50 min |
| 06 | [SOLID Principles](part2-lld/ch06-solid-principles.md) | SRP, OCP, LSP, ISP, DIP — each with violation examples and refactored solutions | 55 min |
| 07 | [Design Patterns](part2-lld/ch07-design-patterns.md) | Singleton, Factory, Builder, Adapter, Decorator, Proxy, Strategy, Observer, Command, State, Chain of Responsibility | 65 min |
| 08 | [LLD Case Studies I](part2-lld/ch08-lld-case-studies-1.md) | Parking Lot, Library Management System, Tic-Tac-Toe (with O(1) win checker) | 70 min |
| 09 | [LLD Case Studies II](part2-lld/ch09-lld-case-studies-2.md) | Elevator System (LOOK scheduler), Vending Machine (State pattern), Snake & Ladder, Hotel Booking | 70 min |

### Part 3: High-Level Design (HLD) — Building Blocks

The components and patterns you'll combine in every system design.

| # | Chapter | Topics | Time |
|---|---|---|---|
| 10 | [Scalability & Performance](part3-hld/ch10-scalability-and-performance.md) | Vertical vs horizontal scaling, stateless design, SLA/SLO/SLI, Amdahl's Law, capacity planning | 60 min |
| 11 | [Load Balancing, Caching & CDN](part3-hld/ch11-load-balancing-caching-cdn.md) | L4/L7 LB, algorithms, cache strategies (aside/through/behind), eviction, thundering herd, CDN architecture | 65 min |
| 12 | [Database Scaling](part3-hld/ch12-database-scaling.md) | Replication (single/multi-leader), sharding, consistent hashing with virtual nodes, NewSQL | 60 min |
| 13 | [Message Queues & Async Processing](part3-hld/ch13-message-queues-async.md) | Queue vs pub/sub, delivery guarantees, Kafka deep dive, DLQ, Saga pattern, backpressure | 60 min |
| 14 | [Microservices & API Design](part3-hld/ch14-microservices-api-design.md) | Monolith vs microservices, DDD, REST/gRPC/GraphQL, API Gateway, rate limiting, circuit breaker | 65 min |

### Part 4: HLD Case Studies

Complete system designs for the most common interview questions.

| # | Chapter | System | Key Concepts |
|---|---|---|---|
| 15 | [URL Shortener & Pastebin](part4-hld-case-studies/ch15-url-shortener.md) | URL Shortener | Base62 encoding, key generation service, 301 vs 302, Bloom filters |
| 16 | [Twitter & News Feed](part4-hld-case-studies/ch16-twitter-news-feed.md) | Twitter | Fan-out on write vs read, hybrid approach, Snowflake IDs, trending |
| 17 | [WhatsApp & Chat System](part4-hld-case-studies/ch17-whatsapp-chat-system.md) | WhatsApp | WebSockets, message ordering, E2E encryption, presence, group chat |
| 18 | [YouTube & Netflix](part4-hld-case-studies/ch18-youtube-netflix.md) | Video Platform | Transcoding pipeline, adaptive bitrate (HLS/DASH), CDN, recommendations |
| 19 | [Uber & Location Services](part4-hld-case-studies/ch19-uber-location-services.md) | Uber | Geospatial indexing (Geohash/QuadTree/S2), driver matching, surge pricing |

### Part 5: Advanced Topics

Deep distributed systems knowledge for senior/staff-level interviews.

| # | Chapter | Topics | Time |
|---|---|---|---|
| 20 | [Distributed Systems Fundamentals](part5-advanced/ch20-distributed-systems.md) | CAP/PACELC, consistency spectrum, Lamport/vector/hybrid clocks, 2PC, Saga, quorum, fencing tokens | 70 min |
| 21 | [Consensus & Consistency Protocols](part5-advanced/ch21-consensus-and-consistency.md) | Leader election, Paxos, Raft, gossip/SWIM, CRDTs (G-Counter, OR-Set), TrueTime, tunable consistency | 75 min |
| 22 | [Event Sourcing, CQRS & Stream Processing](part5-advanced/ch22-event-sourcing-cqrs.md) | Event stores, CQRS projections, Kafka Streams, CDC, Outbox pattern, windowing, schema evolution | 70 min |

### Part 6: Interview Preparation

The framework and practice to tie it all together.

| # | Chapter | Topics | Time |
|---|---|---|---|
| 23 | [Interview Framework & Mock Interviews](part6-interview-prep/ch23-interview-framework.md) | 4-step HLD framework, LLD framework, mock walkthroughs, common mistakes, study plans, cheat sheets | 60 min |

---

## How to Use This Book

### For Interview Prep

```
Week 1:  Part 1 (Foundations) + Part 2 Ch 5-6 (OOP, SOLID)
Week 2:  Part 2 Ch 7-9 (Patterns, LLD Cases)
Week 3:  Part 3 (HLD Building Blocks)
Week 4:  Part 4 (HLD Case Studies) + Part 6 (Framework)
Week 5+: Part 5 (Advanced) + practice problems
```

### For Learning System Design

Read linearly. Each chapter builds on the previous. The book progresses from:
- **"What is a thread?"** → **"Design WhatsApp"** → **"Implement Raft consensus"**

### For Reference

Jump to any chapter. Each is self-contained with prerequisites listed in the frontmatter.

---

## What Each Chapter Includes

- **YAML frontmatter** with prerequisites and estimated reading time
- **Mermaid diagrams** (3-5 per chapter) for visual learners
- **Python & Java code** — working implementations, not pseudocode
- **Key takeaways table** summarizing the chapter
- **5 practice questions** ranging from conceptual to design problems
- **Navigation links** to previous/next chapters

---

## Quick Reference

| I need to... | Go to... |
|---|---|
| Review CS fundamentals before interviews | Part 1 (Ch 1-4) |
| Practice LLD/OOP interview problems | Part 2 (Ch 8-9) |
| Understand caching strategies | Ch 11 |
| Learn database sharding | Ch 12 |
| Design a specific system (Twitter, Uber, etc.) | Part 4 (Ch 15-19) |
| Understand consensus protocols | Ch 21 |
| Get an interview framework + cheat sheets | Ch 23 |

---

*Total estimated reading time: ~16 hours*
