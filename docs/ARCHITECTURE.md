# CineBook — Architecture Deep Dive

## System Architecture

```mermaid
graph TB
    subgraph "Presentation Layer"
        ST["🖥️ Streamlit Dashboard<br/>streamlit_app.py<br/>5 pages, 1040+ LOC"]
        FL["🔌 Flask REST API<br/>flask_api.py<br/>12 endpoints"]
    end

    subgraph "Service Layer"
        BS["booking_service.py<br/>• get_available_shows()<br/>• create_booking()<br/>• cancel_booking()"]
        AS["analytics_service.py<br/>• get_show_occupancy()<br/>• get_revenue_report()<br/>• get_seat_type_revenue()"]
    end

    subgraph "Data Access Layer"
        DB["db_connection.py<br/>• execute_query()<br/>• call_procedure()<br/>• execute_script()"]
        MD["models.py<br/>7 dataclasses with serde"]
    end

    subgraph "Database Layer"
        direction LR
        MY["MySQL 8.0<br/>Primary Engine<br/>• Native triggers<br/>• Native stored procedures"]
        SQ["SQLite<br/>Fallback Engine<br/>• Translated triggers<br/>• Python-emulated procedures"]
    end

    ST --> BS & AS
    FL --> BS & AS
    BS --> DB
    AS --> DB
    DB --> MD
    DB -->|"USE_MYSQL=True"| MY
    DB -->|"USE_MYSQL=False"| SQ

    style ST fill:#FF4B4B,stroke:#333,color:#fff
    style FL fill:#111,stroke:#666,color:#fff
    style MY fill:#4479A1,stroke:#333,color:#fff
    style SQ fill:#003B57,stroke:#333,color:#fff
    style BS fill:#6C63FF,stroke:#333,color:#fff
    style AS fill:#6C63FF,stroke:#333,color:#fff
```

## Database ER Diagram

```mermaid
erDiagram
    Movies ||--o{ Shows : "movie_id"
    Cinemas ||--o{ Shows : "cinema_id"
    Shows ||--o{ Seats : "show_id"
    Seats ||--o{ Bookings : "seat_id"
    Customers ||--o{ Bookings : "customer_id"
    Bookings ||--o{ Booking_Audit : "booking_id"

    Movies {
        int movie_id PK
        varchar title
        varchar genre
        int duration_min
        varchar language
        date release_date
        decimal rating
    }
    Cinemas {
        int cinema_id PK
        varchar name
        varchar location
        varchar city
        int total_halls
    }
    Shows {
        int show_id PK
        int movie_id FK
        int cinema_id FK
        date show_date
        time show_time
        int total_seats
        decimal ticket_price
    }
    Seats {
        int seat_id PK
        int show_id FK
        varchar seat_number
        enum seat_type
        decimal price_modifier
    }
    Customers {
        int customer_id PK
        varchar name
        varchar email
        varchar phone
    }
    Bookings {
        int booking_id PK
        int seat_id FK
        int customer_id FK
        decimal amount
        enum status
        varchar payment_ref
    }
    Booking_Audit {
        int audit_id PK
        int booking_id
        varchar action
        timestamp action_time
    }
```

## Data Flow: Booking a Ticket

```mermaid
sequenceDiagram
    participant U as User
    participant ST as Streamlit UI
    participant BS as booking_service
    participant DB as db_connection
    participant TR as BEFORE INSERT Trigger
    participant AU as AFTER INSERT Trigger

    U->>ST: Select show + seats + submit form
    ST->>BS: create_booking(seat_id, customer_id, amount)
    BS->>DB: INSERT INTO Bookings (seat_id, ...)
    DB->>TR: prevent_double_booking fires
    alt Seat already CONFIRMED
        TR-->>DB: SIGNAL SQLSTATE 45000 / RAISE(ABORT)
        DB-->>BS: Exception raised
        BS-->>ST: {success: false, error: "..."}
        ST-->>U: ❌ Seat taken error
    else Seat available
        TR-->>DB: INSERT allowed
        DB->>AU: log_booking_insert fires
        AU->>DB: INSERT INTO Booking_Audit
        DB-->>BS: booking_id returned
        BS-->>ST: {success: true, booking_id: N}
        ST-->>U: 🎉 Ticket card + balloons
    end
```

## Data Flow: Cancellation

```mermaid
sequenceDiagram
    participant U as User
    participant ST as Streamlit UI
    participant BS as booking_service
    participant DB as db_connection
    participant AU as AFTER UPDATE Trigger

    U->>ST: Select booking + click Cancel
    ST->>BS: cancel_booking(booking_id)
    BS->>DB: UPDATE Bookings SET status='CANCELLED'
    DB->>AU: log_booking_cancel fires
    AU->>DB: INSERT INTO Booking_Audit (old='CONFIRMED', new='CANCELLED')
    DB-->>BS: Success
    BS-->>ST: {success: true}
    ST-->>U: ✅ Cancelled + page refresh
```

## Data Flow: Analytics

```mermaid
sequenceDiagram
    participant U as Admin
    participant ST as Streamlit UI
    participant AS as analytics_service
    participant DB as db_connection
    participant SP as Stored Procedure / Emulation

    U->>ST: Open Analytics tab
    ST->>AS: get_show_occupancy(show_id)
    AS->>DB: call_procedure("get_show_occupancy", ...)
    alt MySQL
        DB->>SP: CALL get_show_occupancy(1)
        SP-->>DB: Result set
    else SQLite
        DB->>SP: Execute emulated SELECT query
        SP-->>DB: Result rows
    end
    DB-->>AS: List[Dict]
    AS-->>ST: Data for Plotly chart
    ST-->>U: Gauge chart + metrics
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Dual DB engine** | MySQL for production with triggers + SPs; SQLite fallback for zero-config demo |
| **BEFORE INSERT trigger** | Database-level enforcement prevents double-booking even with concurrent API calls |
| **Stored procedure emulation** | Python-level SELECT queries mirror MySQL SPs for SQLite compatibility |
| **Single-file Streamlit** | Keeps deployment simple; `if/elif` routing is adequate at 1000 LOC |
| **3NF strict** | No denormalized fields; all joins via FK — proves single-point-of-update |
| **Audit triggers** | Every booking change is logged automatically — no application-level logging needed |
