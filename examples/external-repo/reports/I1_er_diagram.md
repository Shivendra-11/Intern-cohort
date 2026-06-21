# I1 — ER diagram (external repo)

Source: `/tmp/ext-eval-repo/backend` — scanned with `polyglot_eval.repo_scanner` (AST, no model calls).

**22 entities · 0 inferred relationships.**

## Entities (with source citations)

| Entity | Source file | Line | Columns |
| --- | --- | --- | --- |
| `UserBase` | app/models.py | 14 | email:EmailStr, is_active:bool, is_superuser:bool, full_name:str \| None |
| `UserCreate` | app/models.py | 22 | password:str |
| `UserRegister` | app/models.py | 26 | email:EmailStr, password:str, full_name:str \| None |
| `UserUpdate` | app/models.py | 33 | email:EmailStr \| None, password:str \| None |
| `UserUpdateMe` | app/models.py | 38 | full_name:str \| None, email:EmailStr \| None |
| `UpdatePassword` | app/models.py | 43 | current_password:str, new_password:str |
| `User` | app/models.py | 49 | id:uuid.UUID(PK), hashed_password:str, created_at:datetime \| None, items:list['Item'] |
| `UserPublic` | app/models.py | 60 | id:uuid.UUID(PK), created_at:datetime \| None |
| `UsersPublic` | app/models.py | 65 | data:list[UserPublic], count:int |
| `ItemBase` | app/models.py | 71 | title:str, description:str \| None |
| `ItemCreate` | app/models.py | 77 | id:string(PK) |
| `ItemUpdate` | app/models.py | 82 | title:str \| None |
| `Item` | app/models.py | 87 | id:uuid.UUID(PK), created_at:datetime \| None, owner_id:uuid.UUID(FK), owner:User \| None |
| `ItemPublic` | app/models.py | 100 | id:uuid.UUID(PK), owner_id:uuid.UUID(FK), created_at:datetime \| None |
| `ItemsPublic` | app/models.py | 106 | data:list[ItemPublic], count:int |
| `Message` | app/models.py | 112 | message:str |
| `Token` | app/models.py | 117 | access_token:str, token_type:str |
| `TokenPayload` | app/models.py | 123 | sub:str \| None |
| `NewPassword` | app/models.py | 127 | token:str, new_password:str |
| `EmailData` | app/utils.py | 20 | html_content:str, subject:str |
| `Settings` | app/core/config.py | 26 | model_config:string, API_V1_STR:str, SECRET_KEY:str, ACCESS_TOKEN_EXPIRE_MINUTES:int, FRONTEND_HOST:str, ENVIRONMENT:Literal['local', 'staging', 'production'], BACKEND_CORS_ORIGINS:Annotated[list[AnyUrl] \| str, BeforeValidator(parse_cors)], PROJECT_NAME:str, SENTRY_DSN:HttpUrl \| None, POSTGRES_SERVER:str, POSTGRES_PORT:int, POSTGRES_USER:str |
| `PrivateUserCreate` | app/api/routes/private.py | 16 | email:str, password:str, full_name:str, is_verified:bool |

## Inferred relationships

_No cross-entity relationships inferred._

## Mermaid ER diagram

```mermaid
erDiagram
    UserBase {
        EmailStr email
        bool is_active
        bool is_superuser
        str | None full_name
    }
    UserCreate {
        str password
    }
    UserRegister {
        EmailStr email
        str password
        str | None full_name
    }
    UserUpdate {
        EmailStr | None email
        str | None password
    }
    UserUpdateMe {
        str | None full_name
        EmailStr | None email
    }
    UpdatePassword {
        str current_password
        str new_password
    }
    User {
        uuid.UUID id PK
        str hashed_password
        datetime | None created_at
        list['Item'] items
    }
    UserPublic {
        uuid.UUID id PK
        datetime | None created_at
    }
    UsersPublic {
        list[UserPublic] data
        int count
    }
    ItemBase {
        str title
        str | None description
    }
    ItemCreate {
        string id PK
    }
    ItemUpdate {
        str | None title
    }
    Item {
        uuid.UUID id PK
        datetime | None created_at
        uuid.UUID owner_id FK
        User | None owner
    }
    ItemPublic {
        uuid.UUID id PK
        uuid.UUID owner_id FK
        datetime | None created_at
    }
    ItemsPublic {
        list[ItemPublic] data
        int count
    }
    Message {
        str message
    }
    Token {
        str access_token
        str token_type
    }
    TokenPayload {
        str | None sub
    }
    NewPassword {
        str token
        str new_password
    }
    EmailData {
        str html_content
        str subject
    }
    Settings {
        string model_config
        str API_V1_STR
        str SECRET_KEY
        int ACCESS_TOKEN_EXPIRE_MINUTES
        str FRONTEND_HOST
        Literal['local', 'staging', 'production'] ENVIRONMENT
        Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)] BACKEND_CORS_ORIGINS
        str PROJECT_NAME
    }
    PrivateUserCreate {
        str email
        str password
        str full_name
        bool is_verified
    }
```
