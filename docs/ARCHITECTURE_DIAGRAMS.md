# Architecture Diagrams & System Design

## Overview

This document provides detailed architecture diagrams and system design documentation for Cognie, the AI-powered productivity platform.

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  Web Browser (Next.js)  │  Mobile App  │  Desktop App  │  API Clients     │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              GATEWAY LAYER                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  Load Balancer (Nginx)  │  API Gateway  │  CDN (Static Assets)             │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            APPLICATION LAYER                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  FastAPI Backend  │  Background Workers  │  Job Scheduler  │  Webhooks     │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SERVICE LAYER                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  Auth Service  │  AI Service  │  Notion Service  │  Email Service         │
│  Task Service  │  Analytics   │  Payment Service │  Cache Service         │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  Supabase (PostgreSQL)  │  Redis Cache  │  File Storage  │  External APIs  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Detailed Component Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (Next.js)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │   Pages/        │  │  Components/    │  │  Contexts/      │              │
│  │                 │  │                 │  │                 │              │
│  │ • Dashboard     │  │ • Auth          │  │ • AuthContext   │              │
│  │ • Tasks         │  │ • Dashboard     │  │ • ThemeContext  │              │
│  │ • Goals         │  │ • Layout        │  │ • DataContext   │              │
│  │ • Schedule      │  │ • Payment       │  │ • Sidebar       │              │
│  │ • Analytics     │  │ • Sidebar       │  │ • Settings      │              │
│  │ • Settings      │  │ • Hero          │  │ • Hero          │              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │   Services/     │  │   Styles/       │  │   Public/       │              │
│  │                 │  │                 │  │                 │              │
│  │ • API Client    │  │ • Tailwind CSS  │  │ • Static Assets │              │
│  │ • Auth Service  │  │ • Global Styles │  │ • Images        │              │
│  │ • Data Service  │  │ • Components    │  │ • Icons         │              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND (FastAPI)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │   Routes/       │  │   Services/     │  │   Models/       │              │
│  │                 │  │                 │  │                 │              │
│  │ • Auth          │  │ • Auth Service  │  │ • User          │              │
│  │ • Tasks         │  │ • AI Service    │  │ • Task          │              │
│  │ • Goals         │  │ • Notion Service│  │ • Goal          │              │
│  │ • Schedule      │  │ • Email Service │  │ • Schedule      │              │
│  │ • Analytics     │  │ • Cache Service │  │ • Flashcard     │              │
│  │ • Notion        │  │ • Payment Service│  │ • Habit         │              │
│  │ • Stripe        │  │ • Background    │  │ • Notification  │              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │  Middleware/    │  │   Config/       │  │   Tests/        │              │
│  │                 │  │                 │  │                 │              │
│  │ • Auth          │  │ • Security      │  │ • Unit Tests    │              │
│  │ • Rate Limiting │  │ • Database      │  │ • Integration   │              │
│  │ • Logging       │  │ • Environment   │  │ • E2E Tests     │              │
│  │ • Error Handling│  │ • API Keys      │  │ • Performance   │              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │   Supabase      │  │   Redis Cache   │  │   File Storage  │              │
│  │  (PostgreSQL)   │  │                 │  │                 │              │
│  │                 │  │ • Sessions      │  │ • User Files    │              │
│  │ • Users         │  │ • Cache Data    │  │ • Exports       │              │
│  │ • Tasks         │  │ • Rate Limiting │  │ • Backups       │              │
│  │ • Goals         │  │ • Job Queue     │  │ • Logs          │              │
│  │ • Schedule      │  │ • Real-time     │  │                 │              │
│  │ • Flashcards    │  │   Subscriptions │  │                 │              │
│  │ • Habits        │  │                 │  │                 │              │
│  │ • Analytics     │  │                 │  │                 │              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Architecture

### Request Flow

```
1. Client Request
   ┌─────────────┐
   │   Browser   │
   └─────────────┘
           │
           ▼
2. Load Balancer
   ┌─────────────┐
   │   Nginx     │
   └─────────────┘
           │
           ▼
3. API Gateway
   ┌─────────────┐
   │  FastAPI    │
   └─────────────┘
           │
           ▼
4. Middleware Chain
   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
   │    CORS     │→│ Rate Limit  │→│   Auth      │
   └─────────────┘  └─────────────┘  └─────────────┘
           │
           ▼
5. Route Handler
   ┌─────────────┐
   │   Route     │
   └─────────────┘
           │
           ▼
6. Service Layer
   ┌─────────────┐
   │  Service    │
   └─────────────┘
           │
           ▼
7. Data Layer
   ┌─────────────┐  ┌─────────────┐
   │  Supabase   │  │   Redis     │
   └─────────────┘  └─────────────┘
           │
           ▼
8. Response
   ┌─────────────┐
   │   Client    │
   └─────────────┘
```

### Authentication Flow

```
1. User Login
   ┌─────────────┐
   │   Client    │
   └─────────────┘
           │
           ▼
2. Auth Service
   ┌─────────────┐
   │   Verify    │
   │ Credentials │
   └─────────────┘
           │
           ▼
3. Token Generation
   ┌─────────────┐
   │   Create    │
   │   JWT       │
   └─────────────┘
           │
           ▼
4. Session Storage
   ┌─────────────┐
   │   Redis     │
   └─────────────┘
           │
           ▼
5. Response
   ┌─────────────┐
   │   Client    │
   └─────────────┘
```

## Database Schema Architecture

### Entity Relationship Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Users       │    │     Tasks       │    │     Goals       │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ id (PK)         │    │ id (PK)         │    │ id (PK)         │
│ email           │    │ user_id (FK)    │    │ user_id (FK)    │
│ password_hash   │    │ title           │    │ title           │
│ first_name      │    │ description     │    │ description     │
│ last_name       │    │ status          │    │ due_date        │
│ role            │    │ priority        │    │ priority        │
│ is_active       │    │ due_date        │    │ status          │
│ created_at      │    │ created_at      │    │ progress        │
│ updated_at      │    │ updated_at      │    │ created_at      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Schedule       │    │  Flashcards     │    │    Habits       │
│    Blocks       │    │                 │    │                 │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ id (PK)         │    │ id (PK)         │    │ id (PK)         │
│ user_id (FK)    │    │ user_id (FK)    │    │ user_id (FK)    │
│ title           │    │ question        │    │ title           │
│ start_time      │    │ answer          │    │ description     │
│ end_time        │    │ tags            │    │ streak_count    │
│ context         │    │ deck_id         │    │ frequency       │
│ goal_id (FK)    │    │ next_review     │    │ created_at      │
│ created_at      │    │ created_at      │    │ updated_at      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Database Indexing Strategy

```
Primary Indexes:
- users(id)
- tasks(id, user_id)
- goals(id, user_id)
- schedule_blocks(id, user_id)
- flashcards(id, user_id)
- habits(id, user_id)

Secondary Indexes:
- users(email) - UNIQUE
- tasks(due_date, status)
- goals(due_date, priority)
- schedule_blocks(start_time, end_time)
- flashcards(next_review_date)
- notifications(send_time)

Composite Indexes:
- tasks(user_id, status, priority)
- goals(user_id, status, due_date)
- schedule_blocks(user_id, start_time)
```

## Security Architecture

### Security Layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SECURITY LAYERS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │   Network       │  │   Application   │  │     Data        │              │
│  │   Security      │  │   Security      │  │   Security      │              │
│  │                 │  │                 │  │                 │              │
│  │ • HTTPS/TLS     │  │ • JWT Auth      │  │ • Encryption    │              │
│  │ • Firewall      │  │ • Rate Limiting │  │ • Row Level     │              │
│  │ • DDoS          │  │ • Input         │  │   Security      │              │
│  │   Protection    │  │   Validation    │  │ • Audit Logging │              │
│  │ • WAF           │  │ • CORS          │  │ • Backup        │              │
│  │                 │  │ • XSS/CSRF      │  │   Encryption    │              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Authentication Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │    │   Gateway   │    │   Service   │    │  Database   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       │ 1. Login Request  │                   │                   │
       │─────────────────→│                   │                   │
       │                   │                   │                   │
       │                   │ 2. Forward        │                   │
       │                   │─────────────────→│                   │
       │                   │                   │                   │
       │                   │                   │ 3. Verify User   │
       │                   │                   │─────────────────→│
       │                   │                   │                   │
       │                   │                   │ 4. User Data     │
       │                   │                   │←─────────────────│
       │                   │                   │                   │
       │                   │ 5. Generate JWT   │                   │
       │                   │←─────────────────│                   │
       │                   │                   │                   │
       │ 6. JWT Response   │                   │                   │
       │←─────────────────│                   │                   │
       │                   │                   │                   │
```

## Performance Architecture

### Caching Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CACHING LAYERS                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │   Browser       │  │   CDN           │  │   Application   │              │
│  │   Cache         │  │   Cache         │  │   Cache         │              │
│  │                 │  │                 │  │                 │              │
│  │ • Static Assets │  │ • Images        │  │ • User Data     │              │
│  │ • API Responses │  │ • CSS/JS        │  │ • Session Data  │              │
│  │ • Local Storage │  │ • Fonts         │  │ • Query Results │              │
│  │ • Session       │  │ • Documents     │  │ • AI Responses  │              │
│  │   Storage       │  │                 │  │ • Rate Limiting │              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Load Balancing Strategy

```
┌─────────────┐
│   Clients   │
└─────────────┘
       │
       ▼
┌─────────────┐
│ Load        │
│ Balancer    │
│ (Nginx)     │
└─────────────┘
       │
       ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ Backend     │  │ Backend     │  │ Backend     │
│ Instance 1  │  │ Instance 2  │  │ Instance 3  │
└─────────────┘  └─────────────┘  └─────────────┘
       │               │               │
       └───────────────┼───────────────┘
                       ▼
              ┌─────────────┐
              │   Shared    │
              │   Storage   │
              └─────────────┘
```

## Deployment Architecture

### Production Environment

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRODUCTION ENVIRONMENT                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │   Domain        │  │   SSL/TLS       │  │   CDN           │              │
│  │   (Cloudflare)  │  │   Certificate   │  │   (Cloudflare)  │              │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              LOAD BALANCER                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │   Nginx         │  │   Rate Limiting │  │   SSL           │              │
│  │   Reverse Proxy │  │   & Security    │  │   Termination   │              │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            APPLICATION SERVERS                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │   Frontend      │  │   Backend       │  │   Background    │              │
│  │   (Next.js)     │  │   (FastAPI)     │  │   Workers       │              │
│  │   Port: 3000    │  │   Port: 8000    │  │   (Celery)      │              │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA SERVICES                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │   Supabase      │  │   Redis         │  │   File Storage  │              │
│  │   (PostgreSQL)  │  │   (Cache)       │  │   (S3/B2)       │              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Development Environment

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DEVELOPMENT ENVIRONMENT                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │   Local         │  │   Local         │  │   Local         │              │
│  │   Frontend      │  │   Backend       │  │   Database      │              │
│  │   (Next.js)     │  │   (FastAPI)     │  │   (Supabase)    │              │
│  │   localhost:3000│  │   localhost:8000│  │   (Cloud)       │              │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL SERVICES                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │   OpenAI        │  │   Notion        │  │   Stripe        │              │
│  │   (GPT-4)       │  │   (API)         │  │   (Payments)    │              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Monitoring & Observability

### Monitoring Stack

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MONITORING & OBSERVABILITY                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │   Application   │  │   Infrastructure│  │   Business      │              │
│  │   Monitoring    │  │   Monitoring    │  │   Metrics       │              │
│  │                 │  │                 │  │                 │              │
│  │ • Response Time │  │ • CPU Usage     │  │ • User Growth   │              │
│  │ • Error Rates   │  │ • Memory Usage  │  │ • Revenue       │              │
│  │ • Throughput    │  │ • Disk Usage    │  │ • Feature Usage │              │
│  │ • Availability  │  │ • Network       │  │ • Retention     │              │
│  │ • Performance   │  │ • Load Average  │  │ • Conversion    │              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │   Logging       │  │   Tracing       │  │   Alerting      │              │
│  │                 │  │                 │  │                 │              │
│  │ • Application   │  │ • Request       │  │ • Email         │              │
│  │   Logs          │  │   Tracing       │  │ • SMS           │              │
│  │ • Access Logs   │  │ • Performance   │  │ • Slack         │              │
│  │ • Error Logs    │  │   Profiling     │  │ • PagerDuty     │              │
│  │ • Audit Logs    │  │ • Distributed   │  │ • Webhooks      │              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Scalability Architecture

### Horizontal Scaling

```
┌─────────────┐
│   Traffic   │
└─────────────┘
       │
       ▼
┌─────────────┐
│ Auto        │
│ Scaling     │
│ Group       │
└─────────────┘
       │
       ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ Instance 1  │  │ Instance 2  │  │ Instance 3  │  │ Instance N  │
│ (CPU: 2)    │  │ (CPU: 2)    │  │ (CPU: 2)    │  │ (CPU: 2)    │
│ (RAM: 4GB)  │  │ (RAM: 4GB)  │  │ (RAM: 4GB)  │  │ (RAM: 4GB)  │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
       │               │               │               │
       └───────────────┼───────────────┼───────────────┘
                       ▼
              ┌─────────────┐
              │   Shared    │
              │   Services  │
              └─────────────┘
```

### Database Scaling

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATABASE SCALING                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │   Read          │  │   Write         │  │   Analytics     │              │
│  │   Replicas      │  │   Primary       │  │   Database      │              │
│  │                 │  │                 │  │                 │              │
│  │ • Replica 1     │  │ • Primary DB    │  │ • Analytics DB  │              │
│  │ • Replica 2     │  │ • Writes Only   │  │ • Read Only     │              │
│  │ • Replica 3     │  │ • ACID          │  │ • Aggregations  │              │
│  │ • Read Only     │  │ • Consistency   │  │ • Reporting     │              │
│  │ • Load Balance  │  │                 │  │ • Data Mining   │              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Disaster Recovery

### Backup Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BACKUP STRATEGY                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │   Database      │  │   File          │  │   Configuration │              │
│  │   Backups       │  │   Backups       │  │   Backups       │              │
│  │                 │  │                 │  │                 │              │
│  │ • Daily Full    │  │ • User Files    │  │ • Environment   │              │
│  │ • Hourly        │  │ • Exports       │  │   Variables     │              │
│  │   Incremental   │  │ • Logs          │  │ • Config Files  │              │
│  │ • Point-in-time │  │ • Backups       │  │ • SSL Certs     │              │
│  │   Recovery      │  │ • Archives      │  │ • API Keys      │              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Recovery Procedures

```
1. Database Recovery
   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
   │   Backup    │→│   Restore   │→│   Verify    │
   │   Storage   │  │   Process   │  │   Data      │
   └─────────────┘  └─────────────┘  └─────────────┘

2. Application Recovery
   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
   │   Deploy    │→│   Health    │→│   Traffic   │
   │   New       │  │   Check     │  │   Switch    │
   │   Version   │  │             │  │             │
   └─────────────┘  └─────────────┘  └─────────────┘

3. Full System Recovery
   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
   │   Identify  │→│   Restore   │→│   Validate  │
   │   Issue     │  │   Services  │  │   System    │
   └─────────────┘  └─────────────┘  └─────────────┘
```

## Conclusion

This architecture provides:

- **Scalability**: Horizontal scaling with load balancing
- **Reliability**: Redundant services and disaster recovery
- **Security**: Multi-layer security with encryption
- **Performance**: Caching and optimization strategies
- **Observability**: Comprehensive monitoring and logging
- **Maintainability**: Modular design with clear separation of concerns

The architecture is designed to support Cognie's growth from a small application to a large-scale platform serving thousands of users. 