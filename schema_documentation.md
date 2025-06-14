# Cognie Platform Schema Documentation

## Overview
This document outlines the database schema for the Cognie platform, including all tables, relationships, and features. The schema is designed to support a comprehensive personal development and productivity platform with AI-powered insights.

## Core Features

### 1. Diary / Journal System
- **Tables**: `journal_entries`, `journal_versions`
- **Features**:
  - Encrypted journal entries (optional)
  - Version history tracking
  - Mood and sentiment analysis
  - Tag-based organization
  - Search functionality

### 2. Habits & Routines
- **Tables**: `habits`, `habit_logs`
- **Features**:
  - Streak tracking with freeze protection
  - Multiple reminders per habit
  - Energy level tagging
  - Impact scoring
  - Mood correlation

### 3. Mood & Emotion Tracking
- **Tables**: `mood_logs`, `mood_prompts`
- **Features**:
  - Emoji-based mood logging
  - Voice memo and image attachments
  - AI-powered pattern detection
  - Daily/weekly reflection prompts
  - Sentiment analysis

### 4. Analytics & Insights
- **Tables**: `analytics_reports`
- **Features**:
  - Goal-specific reports
  - Time tracking visualization
  - Trend analysis
  - AI-generated insights
  - Export capabilities

### 5. User Preferences & Profile
- **Tables**: `users`, `feature_preferences`
- **Features**:
  - Energy curve templates
  - Custom scheduling rules
  - Smart planning modes
  - Feature toggles
  - GDPR compliance

### 6. Resource Management
- **Tables**: `resources`, `resource_engagements`
- **Features**:
  - Trust level verification
  - Engagement tracking
  - Community feedback
  - Difficulty levels
  - Topic tagging

### 7. Fitness Integration
- **Tables**: `fitness_logs`
- **Features**:
  - Activity tracking
  - Sleep monitoring
  - Step counting
  - External service integration
  - Productivity correlation

### 8. Sync & Integration
- **Tables**: `sync_logs`
- **Features**:
  - Multi-directional sync
  - Conflict resolution
  - Error logging
  - Service status tracking
  - Webhook support

### 9. Data Management
- **Tables**: `data_exports`
- **Features**:
  - Multiple export formats
  - Selective data export
  - GDPR compliance
  - Data portability
  - Export history

## Security Features

### Row Level Security (RLS)
All tables implement RLS policies ensuring users can only access their own data. Each table has policies for:
- SELECT (view)
- INSERT (create)
- UPDATE (modify)
- DELETE (remove)

### Data Encryption
- Optional encryption for sensitive data
- User-controlled encryption keys
- Secure storage of encryption preferences

## Performance Optimizations

### Indexes
- User ID indexes for all tables
- GIN indexes for array fields (tags)
- Composite indexes for common queries
- Timestamp indexes for temporal queries

### Triggers
- Automatic `updated_at` timestamp management
- Version control for journal entries
- Audit logging capabilities

## Data Types

### Enums
- `priority_level`: low, medium, high
- `mood_type`: very_happy, happy, neutral, sad, very_sad
- `energy_level`: low, medium, high
- `sync_direction`: push, pull, both
- `sync_status`: pending, success, failed, conflict
- `feature_mode`: focus, relax, study, work, custom
- `resource_type`: article, video, book, course, tool
- `resource_trust_level`: verified, peer_reviewed, community, unverified
- `data_export_format`: csv, json, pdf

### JSON Fields
- User preferences
- Energy curves
- Scheduling rules
- Analytics data
- Reminder configurations

## Future Considerations

### Scalability
- Partitioning strategy for large tables
- Archival policies for historical data
- Caching recommendations

### Extensibility
- Plugin architecture support
- Custom field definitions
- Integration hooks

### Monitoring
- Performance metrics
- Usage statistics
- Error tracking

## Implementation Notes

### Required Extensions
- `uuid-ossp`: For UUID generation
- `pgcrypto`: For encryption support

### Migration Strategy
1. Create new tables
2. Enable RLS
3. Create indexes
4. Set up triggers
5. Migrate existing data

### Backup Considerations
- Regular backups of encrypted data
- Export format compatibility
- Recovery procedures 