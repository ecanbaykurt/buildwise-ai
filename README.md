﻿# Buildwise AI - Multi-Agent RAG













```mermaid
erDiagram
  users ||--o{ conversations : has
  conversations ||--o{ chat_messages : has
  users {
    uuid id PK
    string email
    string name
    string phone
    timestamp created_at
  }
  conversations {
    uuid id PK
    uuid user_id FK
    timestamp created_at
  }
  chat_messages {
    uuid id PK
    uuid conversation_id FK
    string sender
    string message_text
    timestamp timestamp
  }
