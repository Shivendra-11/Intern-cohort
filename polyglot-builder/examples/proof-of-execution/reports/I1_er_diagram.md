# I1 Report — fixture-repo

## entities

2 entities scanned: Task, TaskStore

## primary_keys

- **Task**: ['id']
- **TaskStore**: ['id']

## relationships

- Task → TaskStore (relates_to)

## sources

- `app/store.py:9` — Task
- `app/store.py:16` — TaskStore

## mermaid_diagram

```mermaid
erDiagram
    Task {
        int id PK
        str title
        bool done
    }
    TaskStore {
        string id PK
    }
    Task }o--o{ TaskStore : "relates_to"
```
