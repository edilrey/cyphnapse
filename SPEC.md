Below is a **preliminary design specification**, not the final architecture. I have kept unresolved decisions explicit so later testing can change them without forcing the implementation into an early design.

# Graph Memory Layer

## Preliminary Design Specification v0.1

### 1. Purpose

Graph Memory Layer is an open-source, local-first **graph memory augmentation layer for AI agents**.

Its primary purpose is to represent and retrieve information where the main value comes from:

- relationships between entities
- multi-hop connections
- temporal changes
- provenance and evidence
- contradictions
- entity identity
- domain-specific structure
- traversal across related information

It is **not intended to replace existing semantic or conversational memory systems**.

It should work independently, while also integrating with systems such as Mnemosyne and Hermes Agent.

---

# 2. Core Design Principle

> **Use the representation that best preserves the structure of the information.**

Semantic memory is useful for:

```text
"What did we discuss about X?"

"Find memories similar to this."

"What did I say about this project?"
```

Graph memory is useful for:

```text
"What companies are connected to X?"

"Who controls X?"

"Who controlled X in 2019?"

"What changed in this relationship?"

"What evidence supports this relationship?"

"What evidence contradicts it?"

"How are A and B connected?"
```

The two systems can represent the same underlying information.

Duplication is acceptable in the initial design.

---

# 3. Initial Architecture

```text
                         AI Agent
                            │
             ┌──────────────┴──────────────┐
             │                             │
       Semantic Memory                Graph Memory
        e.g. Mnemosyne                  Layer
             │                             │
       text / semantic               structured graph
        retrieval                     traversal
             │                             │
             └──────────────┬──────────────┘
                            │
                         Agent
```

Graph Memory itself:

```text
                    Graph Memory Layer
                            │
                 ┌──────────┴──────────┐
                 │                     │
             Graph Core             Ontology
                 │                     │
             GraphQLite          Domain schemas
                 │                     │
                 └──────────┬──────────┘
                            │
                          SQLite
```

Initial technology target:

```text
SQLite
  +
GraphQLite
  +
Graph Memory Core
```

The system should remain local-first.

---

# 4. Standalone Requirement

Graph Memory must be useful without:

- Mnemosyne
- Hermes Agent
- cloud services
- external vector databases
- external graph databases

The core should expose its own API.

Potential API categories:

```text
Entity operations
Relationship operations
Evidence operations
Event operations
Ontology operations
Traversal
Temporal queries
Identity resolution
Conflict inspection
Graph management
```

Agent integrations should sit above the core.

```text
Graph Core
    │
    ├── Python API
    │
    ├── CLI
    │
    └── Agent integration
          ├── Hermes
          ├── Mnemosyne
          └── future providers
```

---

# 5. Multiple Graphs

Graph Memory should support multiple independent graphs.

A user could maintain:

```text
Corporate Intelligence
Medieval History
PhD Research
Personal Project
Software Architecture
```

without forcing them into one universal graph.

Example:

```text
Graph A
Corporate Intelligence

Company
Person
Family
Government
Ownership
Acquisition
Supplier
```

```text
Graph B
Medieval History

Person
Dynasty
Kingdom
Battle
Treaty
Place
Manuscript
```

```text
Graph C
Bioinformatics

Gene
Protein
Disease
Experiment
Researcher
Publication
```

Graphs do not need to connect.

---

# 6. Cross-Graph Relationships

Graphs can be connected when the agent determines that a meaningful relationship exists.

Example:

```text
Corporate Graph

Person #1842
      │
      └── different_from ──► Person #731
                               ▲
                               │
                        Historical Graph
```

More commonly:

```text
Graph A                          Graph B

Person A                         Person B
    │                                │
    └────────── same_as ─────────────┘
```

The important principle is:

> **Connecting graphs must not require merging the original nodes.**

This preserves the independent domain representations.

---

# 7. Identity Resolution

Identity is a first-class concern.

The system must not treat:

```text
same name
```

as:

```text
same entity
```

Identity reasoning can use:

- name
- date information
- location
- occupation
- organization
- relationships
- events
- family relationships
- temporal consistency
- source evidence
- graph neighborhood

Example:

```text
Corporate Graph

John Smith
born: 1978
location: Manila
CEO
active: 2005-present
```

```text
Medieval Graph

John Smith
born: ~1320
location: England
nobleman
active: 1340-1370
```

The graph can represent:

```text
John Smith #1
      │
      └── different_from ──►
                              John Smith #2
```

Identity assertions should support at least:

```text
same_as
possibly_same_as
different_from
```

They should retain supporting evidence rather than immediately merging nodes.

---

# 8. Domain-Specific Ontologies

The graph engine should not enforce one universal domain ontology.

The core provides generic graph capabilities.

A domain can define its own:

```text
node types
relationship types
properties
events
constraints
```

Example corporate ontology:

```text
Company
Person
Family
Government
Organization
Acquisition
Ownership
BoardPosition
PoliticalAssociation
Supplier
```

Example:

```text
Person ──controls──► Company
Company ──supplies──► Company
Company ──acquired──► Company
Person ──member_of──► Family
```

A research ontology could instead contain:

```text
Gene
Protein
Disease
Researcher
Publication
Experiment
Dataset
```

The graph engine should not need domain-specific knowledge to perform basic graph operations.

---

# 9. Agent-Driven Graph Construction

The graph should **not automatically store every conversation**.

The default promotion model is:

```text
Conversation
     ↓
Candidate information
     ↓
Persistent structural information?
     ↓
Candidate for graph promotion
     ↓
Agent evaluation
     ├── promote
     ├── reject
     └── modify
```

The agent can also explicitly promote information:

```text
Agent
  ↓
"This relationship is important."
  ↓
Graph Memory
```

Therefore:

> Automatic detection identifies potentially valuable structural information. The agent retains the ability to accept, reject, or explicitly create graph information.

This is deliberately different from:

```text
conversation → automatic graph insertion
```

---

# 10. Evidence Model

The graph should preserve the distinction between:

```text
Evidence
Claim
Memory
```

An observation from a conversation or external source should not automatically become established truth.

Conceptually:

```text
Source
   ↓
Evidence
   ↓
Claim
   ↓
Agent evaluation
   ↓
Graph representation
```

A relationship should be explainable.

Example:

```text
Person A
    │
    └── controls → Company B
                       │
                       ├── evidence → Filing X
                       ├── evidence → Report Y
                       └── observed_at → 2026-08-20
```

The system should support contradictory evidence.

```text
Claim A:
Person A controls Company B

Supporting:
    Source 1
    Source 2

Contradicting:
    Source 3
```

The system should not silently hide the contradiction.

---

# 11. Temporal Graph

Relationships are not necessarily permanent.

Instead of:

```text
Person A ──owns──► Company B
```

the underlying representation should be able to capture:

```text
owns
valid_from: 2020
valid_until: 2025
```

This allows questions such as:

```text
Who owns Company B now?

Who owned Company B in 2022?

When did ownership change?

What relationships existed before the acquisition?

What changed after the acquisition?
```

Historical truth should remain recoverable.

An old relationship should not simply be overwritten because it is no longer current.

---

# 12. Current State vs Historical State

The graph should conceptually distinguish:

```text
Historical truth
```

from:

```text
Current truth
```

Example:

```text
2020 ─────────── 2025 ─────────── 2026

A owns B
██████████████

                         A no longer owns B
                         █████████████████
```

A query for 2022 should return the first relationship.

A query for 2026 should return the second state.

A query without a temporal condition should be able to identify the latest known state.

---

# 13. Contradiction Handling

When new evidence conflicts with existing memory:

```text
Existing:
A owns B

New evidence:
A sold B
```

Graph Memory should expose the conflict.

The preferred agent workflow is:

```text
Existing graph
      ↓
conflict detected
      ↓
Agent evaluates
      ↓
external verification if necessary
      ↓
new evidence
      ↓
agent decides
      ↓
graph update
```

The graph layer should provide the information required for this decision.

It should not silently decide that the newest piece of information is automatically correct.

---

# 14. External Verification Loop

Graph Memory can become a starting point for further investigation.

```text
Graph Memory
     ↓
uncertain / stale / conflicting
     ↓
Agent
     ↓
web search
web extraction
government database
filing
other external tool
     ↓
new evidence
     ↓
Agent evaluation
     ↓
Graph update
```

This creates a useful feedback loop:

```text
Memory
  ↓
detect uncertainty
  ↓
investigate
  ↓
new evidence
  ↓
update memory
```

The graph therefore becomes both:

**memory** and **an investigation starting point**.

---

# 15. Graph Traversal

Traversal is one of the main reasons to have the graph layer.

The agent should not need to repeatedly request individual documents or memories when the required context is structurally connected.

Conceptually:

```text
Company A
    ↓
subsidiary
    ↓
Company B
    ↓
director
    ↓
Person C
    ↓
family
    ↓
Family D
    ↓
Company E
```

The agent can request:

```text
traverse from Company A
depth = 5
relationship filters = ...
```

The graph layer performs the traversal locally and returns the useful structure.

Traversal should support both:

### High-level query

```text
"Find companies connected to Company A within 4 hops."
```

### Controlled traversal

```text
start = Company A
direction = outgoing
relationship = ownership
depth = 3
```

This preserves your earlier requirement for **hybrid agent tools**.

---

# 16. Optional Deep Traversal

Deep traversal should be available, but it should not always run.

The agent decides when the task benefits from it.

For simple questions:

```text
Who owns Company A?
```

A shallow query may be enough.

For complex investigation:

```text
Find indirect relationships between Company A
and Organization B and explain the connection.
```

The agent can request deeper traversal.

This avoids turning every memory lookup into a large graph exploration.

---

# 17. Token-Efficient Results

Graph traversal can produce many nodes.

Therefore Graph Memory should support compact result representations.

TOON is a candidate format for this.

Conceptually:

```text
nodes:
  id | type | name
  1  | company | Company A
  2  | person  | Person B
  3  | company | Company C

edges:
  source | relation | target
  1      | controls | 2
  2      | owns     | 3
```

The exact serialization should be tested against:

- JSON
- TOON
- compact text
- structured tool output

The goal is:

> **Reduce unnecessary token consumption while preserving enough structure for the agent to reason over the result.**

TOON should therefore remain an implementation option until benchmark testing confirms its value.

---

# 18. Relationship-Centric Queries

The first graph query capabilities should focus on questions where graph structure provides clear value.

Examples:

```text
neighbors(entity)

relationships(entity)

traverse(entity, depth)

find_path(entity_a, entity_b)

related_entities(entity)

history(entity)

relationship_history(entity_a, entity_b)

evidence(relationship)

conflicts(entity)

identity_candidates(entity)
```

Higher-level queries can later be built on these primitives.

---

# 19. Heterogeneous Data

The long-term goal is not only to store conversation-derived relationships.

The graph should be capable of connecting heterogeneous information such as:

```text
Conversation
Documents
Web pages
Government records
Company filings
Research papers
Historical sources
Structured datasets
Agent observations
```

Conceptually:

```text
             Heterogeneous Sources
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
   Documents      Databases        Web
       │              │              │
       └──────────────┼──────────────┘
                      ▼
                 Evidence
                      │
                      ▼
                  Graph Model
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
       Entities   Relations     Events
```

This is the part of the design inspired by the general idea behind ontology-based systems such as Palantir's Ontology: different underlying data can be represented through a common semantic model.

The project should take **design inspiration**, not attempt to reproduce Palantir's proprietary implementation.

---

# 20. Relationship to Mnemosyne

Mnemosyne remains useful for information better represented as semantic or conversational memory.

Graph Memory handles information where structure matters.

They can coexist:

```text
Hermes
 │
 ├── Mnemosyne
 │      └── semantic memory
 │
 └── Graph Memory
        └── structured memory
```

They may contain duplicated representations.

For example:

```text
Mnemosyne:

"We discussed that Company A acquired Company B
in 2022."


Graph:

Company A
    │
    └── acquired
          │
          ▼
       Company B
          │
          ├── date → 2022
          └── evidence → memory/document
```

There is no requirement for a canonical owner in v0.1.

Synchronization can be investigated later.

---

# 21. Hermes Integration

Hermes should be the first agent integration.

The plugin should expose graph-specific tools rather than attempting to replace the agent's existing memory.

Possible initial tool family:

```text
graph_search
graph_get
graph_traverse
graph_path
graph_history
graph_evidence
graph_conflicts
graph_promote
graph_reject
```

The exact tool set should be determined after testing tool-call behavior.

---

# 22. Open Architecture

The project should have clear separation between:

```text
Graph engine
Ontology
Persistence
Evidence
Agent interface
Provider adapters
```

Potential architecture:

```text
                    Graph Memory API
                           │
                 ┌─────────┴─────────┐
                 │                   │
             Graph Core          Ontology
                 │                   │
                 └─────────┬─────────┘
                           │
                      Persistence
                           │
                    SQLite/GraphQLite
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
     Hermes            Mnemosyne          Other agents
```

This keeps the core independent from any specific agent framework.

---

# 23. Preliminary Core Data Model

This remains intentionally provisional.

A useful initial conceptual model is:

```text
Graph
 ├── Node
 ├── Edge
 ├── Property
 ├── Evidence
 ├── Event
 ├── Claim
 └── Schema
```

However, **Claim versus Edge**, and **Event versus temporal Edge**, are still design questions.

We should not finalize those based only on theoretical reasoning.

Testing should determine which representation produces better:

- queries
- traversal
- updates
- provenance
- temporal reasoning
- agent usability
- SQLite performance

---

# 24. Non-Goals for v0.1

The initial project should not attempt to:

- replace semantic memory
- replace RAG
- become a general-purpose search engine
- automatically ingest every conversation
- automatically determine truth
- automatically merge entities
- create one universal ontology
- synchronize every memory provider
- reproduce Gotham/Foundry
- require cloud infrastructure
- solve every OSINT problem

These boundaries are important.

---

# 25. Preliminary Development Strategy

### Stage 1: Graph core

Build:

```text
SQLite
GraphQLite
Graph
Node
Edge
Properties
basic traversal
```

### Stage 2: Temporal and evidence model

Add:

```text
Evidence
Source
timestamps
valid_from
valid_until
historical relationships
```

### Stage 3: Agent interface

Create:

```text
search
traverse
path
history
evidence
```

### Stage 4: Promotion workflow

Add:

```text
candidate
promote
reject
explicit promotion
```

### Stage 5: Hermes plugin

Expose the graph as an optional memory capability.

### Stage 6: Multiple graphs

Support:

```text
graph.create()
graph.list()
graph.switch()
```

with independent schemas.

### Stage 7: Cross-graph identity

Support:

```text
same_as
possibly_same_as
different_from
```

without forced node merging.

### Stage 8: Mnemosyne integration

Test:

```text
Mnemosyne → Graph
Graph → Mnemosyne
Graph ↔ Mnemosyne
```

and measure which integration patterns are actually useful.

### Stage 9: Automated graph candidate generation

Only after the manual/agent-driven workflow works well:

```text
conversation
    ↓
candidate extraction
    ↓
agent evaluation
    ↓
promotion
```

---

# 26. Design Philosophy

The current project philosophy can be summarized as:

> **Do not make the graph remember everything. Make it remember structure.**

And:

> **Do not make the graph decide what is true. Make it preserve evidence, relationships, temporal state, and uncertainty so the agent can reason about what is currently trustworthy.**

And:

> **Do not force every domain into one ontology. Let graphs represent different domains independently and provide mechanisms for connecting them when evidence shows that they intersect.**

And finally:

> **Do not make Graph Memory compete with existing memory systems. Give agents another representation when semantic memory is not enough.**

---

## Decisions currently settled

| Area                          | Current decision            |
| ----------------------------- | --------------------------- |
| Primary role                  | Graph memory augmentation   |
| Standalone                    | Required                    |
| Hermes                        | First integration           |
| Mnemosyne                     | Optional integration        |
| Semantic/RAG                  | Complementary               |
| Multiple graphs               | Supported                   |
| Cross-graph links             | Supported                   |
| Automatic node merging        | No                          |
| Identity reasoning            | Required                    |
| Temporal relationships        | Required                    |
| Evidence/provenance           | Required                    |
| Contradictions                | Must be representable       |
| Agent graph promotion         | Supported                   |
| Automatic candidate detection | Default candidate mechanism |
| Agent rejection               | Supported                   |
| Agent explicit promotion      | Supported                   |
| Duplicate representations     | Allowed                     |
| Universal ontology            | No                          |
| Domain-specific ontology      | Yes                         |
| Deep traversal                | Optional                    |
| TOON                          | Candidate for testing       |
| Cloud dependency              | No                          |
| Final schema                  | Not yet fixed               |

## Decisions deliberately left open

The next development-spec grilling should focus on:

1. **Exact Node/Edge/Claim/Event model**
2. **How temporal relationships are represented**
3. **How evidence attaches to relationships**
4. **How an ontology is defined and stored**
5. **How multiple graphs are isolated**
6. **How cross-graph links are represented**
7. **What automatic candidate detection looks like**
8. **How graph queries are exposed to the agent**
9. **What the compact tool-result protocol should be**
10. **How entity resolution works without dangerous automatic merging**

This is the point where I would stop adding architecture and start turning the specification into **testable invariants and implementation experiments**. That will let the later design decisions come from measurements instead of from trying to predict the perfect graph architecture in advance.
