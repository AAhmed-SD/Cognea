# Exam Paper Upload and Processing System

## Overview

The Exam Paper Upload and Processing System is a comprehensive solution that allows users to upload exam papers (PDF or images) and automatically extract questions, generate AI solutions, and organize them into collections. This system leverages our hybrid AI infrastructure to provide cost-effective and high-quality question processing.

## Features

### 🎯 Core Features
- **File Upload**: Support for PDF, JPG, PNG, and TIFF files up to 10MB
- **OCR Processing**: Text extraction from images using Google Vision API with Tesseract fallback
- **PDF Processing**: Text extraction from PDF files using PyPDF2
- **AI Question Extraction**: Intelligent question identification and parsing
- **AI Solution Generation**: Step-by-step solutions and hints for each question
- **Difficulty Assessment**: Automatic difficulty rating (1-5 scale)
- **Topic Classification**: AI-powered topic identification
- **User Collections**: Organize questions into custom collections
- **Sharing System**: Share collections with others via secure links
- **Legal Protection**: Built-in compliance and upload agreement tracking

### 🔧 Technical Features
- **Hybrid AI Integration**: Uses cost-optimized AI routing
- **Database Storage**: PostgreSQL with Supabase for data persistence
- **Row Level Security**: Secure data access with RLS policies
- **Rate Limiting**: Upload limits to prevent abuse
- **Error Handling**: Comprehensive error handling and logging
- **Testing**: Full test suite with mocked dependencies

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Routes     │    │   Services      │
│   (React)       │◄──►│   (FastAPI)      │◄──►│   (Python)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   Database       │    │   AI Providers  │
                       │   (PostgreSQL)   │    │   (Hybrid AI)   │
                       └──────────────────┘    └─────────────────┘
```

## Setup Instructions

### 1. Database Migration

Run the migration to create all necessary tables:

```bash
# Apply the migration
psql -d your_database -f migrations/add_exam_paper_tables.sql
```

### 2. Install Dependencies

Add the required Python packages:

```bash
pip install PyPDF2==3.0.1 google-cloud-vision==3.4.4 pytesseract==0.3.10 Pillow==10.0.1 aiofiles==23.2.1
```

### 3. Environment Configuration

Set up the following environment variables:

```bash
# Google Cloud Vision API (optional, for better OCR)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/credentials.json

# Tesseract OCR (fallback)
# Install tesseract-ocr on your system
# Ubuntu: sudo apt-get install tesseract-ocr
# macOS: brew install tesseract
# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
```

### 4. File Storage Setup

Create the uploads directory:

```bash
mkdir -p uploads
chmod 755 uploads
```

## API Reference

### File Upload

#### POST `/api/exam-papers/upload`

Upload and process an exam paper file.

**Request:**
```http
POST /api/exam-papers/upload
Content-Type: multipart/form-data
Authorization: Bearer <token>

file: <file>
```

**Response:**
```json
{
  "message": "Exam paper processed successfully",
  "paper_id": "uuid",
  "questions_count": 15,
  "preview_questions": [
    {
      "id": "uuid",
      "question_text": "What is 2+2?",
      "question_number": 1,
      "marks": 2,
      "topic": "Mathematics",
      "difficulty": 1,
      "ai_solution": "Step-by-step solution...",
      "ai_hints": "1. Think about basic addition...",
      "confidence_score": 0.9
    }
  ]
}
```

### Papers Management

#### GET `/api/exam-papers/papers`

Get user's uploaded papers.

**Response:**
```json
{
  "papers": [
    {
      "id": "uuid",
      "file_name": "math_exam.pdf",
      "file_size": 2048576,
      "processing_status": "completed",
      "extracted_questions_count": 15,
      "upload_date": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1
}
```

#### GET `/api/exam-papers/papers/{paper_id}/questions`

Get questions from a specific paper.

**Response:**
```json
{
  "questions": [
    {
      "id": "uuid",
      "question_text": "What is 2+2?",
      "question_number": 1,
      "marks": 2,
      "topic": "Mathematics",
      "difficulty": 1,
      "ai_solution": "Step-by-step solution...",
      "ai_hints": "1. Think about basic addition...",
      "confidence_score": 0.9,
      "needs_review": false
    }
  ],
  "total": 15
}
```

### Collections Management

#### POST `/api/exam-papers/collections`

Create a new collection.

**Request:**
```http
POST /api/exam-papers/collections
Content-Type: multipart/form-data
Authorization: Bearer <token>

name: "Math Practice"
description: "Collection of math questions"
is_public: false
```

#### GET `/api/exam-papers/collections`

Get user's collections.

#### POST `/api/exam-papers/collections/{collection_id}/questions`

Add questions to a collection.

**Request:**
```json
{
  "question_ids": ["uuid1", "uuid2", "uuid3"]
}
```

### Sharing

#### POST `/api/exam-papers/collections/{collection_id}/share`

Create a shareable link.

**Response:**
```json
{
  "message": "Share link created successfully",
  "share_data": {
    "share_id": "uuid",
    "share_link": "/shared-collection/uuid",
    "expires_at": null
  }
}
```

#### GET `/api/exam-papers/shared/{share_id}`

Access a shared collection.

## Frontend Usage

### Upload Interface

The frontend provides a user-friendly interface for uploading exam papers:

```jsx
import React, { useState } from 'react';

const ExamPaperUpload = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);

  const handleUpload = async () => {
    const formData = new FormData();
    formData.append('file', selectedFile);

    const response = await fetch('/api/exam-papers/upload', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${user.token}`
      },
      body: formData
    });

    const result = await response.json();
    console.log('Upload result:', result);
  };

  return (
    <div>
      <input
        type="file"
        accept=".pdf,.jpg,.jpeg,.png,.tiff"
        onChange={(e) => setSelectedFile(e.target.files[0])}
      />
      <button onClick={handleUpload} disabled={uploading}>
        {uploading ? 'Processing...' : 'Upload & Process'}
      </button>
    </div>
  );
};
```

### Collections Interface

Manage question collections:

```jsx
const CollectionsManager = () => {
  const [collections, setCollections] = useState([]);

  const createCollection = async (name, description, isPublic) => {
    const formData = new FormData();
    formData.append('name', name);
    formData.append('description', description);
    formData.append('is_public', isPublic);

    const response = await fetch('/api/exam-papers/collections', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${user.token}`
      },
      body: formData
    });

    const result = await response.json();
    // Refresh collections list
  };

  return (
    <div>
      {/* Collection management UI */}
    </div>
  );
};
```

## AI Processing Pipeline

### 1. Text Extraction

The system first extracts text from the uploaded file:

- **PDF**: Uses PyPDF2 to extract text from each page
- **Images**: Uses Google Vision API with Tesseract fallback

### 2. Question Extraction

AI processes the extracted text to identify questions:

```python
# Example AI prompt for question extraction
extraction_prompt = f"""
Extract all questions from this exam paper text. For each question, provide:
1. Question text (complete and clear)
2. Question number (if available)
3. Marks available (if specified)
4. Answer (if provided in the text)
5. Topic/subject area (infer from content)

Format your response as a JSON array with this structure:
[
    {{
        "question_text": "Complete question text here",
        "question_number": 1,
        "marks": 3,
        "answer_text": "Answer if provided",
        "topic": "Inferred topic",
        "confidence_score": 0.9
    }}
]

Exam paper text:
{text_content[:8000]}

Return only valid JSON array.
"""
```

### 3. Question Enhancement

Each extracted question is enhanced with:

- **Difficulty Assessment**: AI rates difficulty on 1-5 scale
- **Topic Refinement**: Better topic classification
- **AI Solutions**: Step-by-step solutions
- **AI Hints**: Helpful hints for students

### 4. Model Selection

The hybrid AI system selects the optimal model for each task:

- **Question Extraction**: DeepSeek API (good balance of cost/quality)
- **Solution Generation**: Claude API (excellent reasoning)
- **Difficulty Assessment**: Llama (cost-effective)

## Database Schema

### Core Tables

#### `uploaded_papers`
Stores information about uploaded exam papers.

```sql
CREATE TABLE uploaded_papers (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id),
    file_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    processing_status VARCHAR(50) DEFAULT 'processing',
    extracted_questions_count INTEGER DEFAULT 0,
    ai_enhanced BOOLEAN DEFAULT FALSE,
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### `extracted_questions`
Stores individual questions extracted from papers.

```sql
CREATE TABLE extracted_questions (
    id UUID PRIMARY KEY,
    paper_id UUID NOT NULL REFERENCES uploaded_papers(id),
    question_text TEXT NOT NULL,
    answer_text TEXT,
    question_number INTEGER,
    marks INTEGER DEFAULT 1,
    topic VARCHAR(100),
    difficulty INTEGER DEFAULT 2,
    ai_solution TEXT,
    ai_hints TEXT,
    confidence_score DECIMAL(3,2) DEFAULT 0.8,
    needs_review BOOLEAN DEFAULT FALSE
);
```

#### `user_question_collections`
Stores user-created question collections.

```sql
CREATE TABLE user_question_collections (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    questions_count INTEGER DEFAULT 0
);
```

## Security and Compliance

### Legal Protection

The system includes built-in legal protection:

1. **Upload Agreements**: Users must agree to terms before uploading
2. **Rate Limiting**: Prevents abuse with daily upload limits
3. **Content Ownership**: Users confirm they own or have permission to use content
4. **Personal Use Only**: Clear terms about educational use only

### Row Level Security

All tables have RLS policies ensuring users can only access their own data:

```sql
-- Example RLS policy
CREATE POLICY "Users can view their own uploaded papers" ON uploaded_papers
    FOR SELECT USING (auth.uid() = user_id);
```

### File Security

- Files are stored in user-specific directories
- File type validation prevents malicious uploads
- File size limits prevent abuse
- Automatic cleanup of temporary files

## Testing

Run the comprehensive test suite:

```bash
# Run all exam paper system tests
pytest tests/test_exam_paper_system.py -v

# Run specific test categories
pytest tests/test_exam_paper_system.py::TestExamPaperProcessor -v
pytest tests/test_exam_paper_system.py::TestUserCollectionsService -v
```

## Performance Considerations

### Optimization Strategies

1. **Async Processing**: All operations are asynchronous for better performance
2. **Caching**: Redis caching for frequently accessed data
3. **Batch Processing**: Process multiple questions in batches
4. **Cost Optimization**: Hybrid AI system minimizes costs while maintaining quality

### Monitoring

Monitor system performance with:

- **Upload Success Rate**: Track successful vs failed uploads
- **Processing Time**: Monitor AI processing duration
- **Cost Tracking**: Track AI usage costs per user
- **Error Rates**: Monitor and alert on processing errors

## Troubleshooting

### Common Issues

1. **OCR Not Working**
   - Check Google Vision API credentials
   - Verify Tesseract installation
   - Ensure image quality is sufficient

2. **AI Processing Fails**
   - Check hybrid AI service configuration
   - Verify API keys for all providers
   - Check rate limits and quotas

3. **Database Errors**
   - Verify migration has been applied
   - Check RLS policies
   - Ensure proper user authentication

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('services.exam_paper_processor').setLevel(logging.DEBUG)
```

## Future Enhancements

### Planned Features

1. **Batch Upload**: Upload multiple files at once
2. **Question Templates**: Pre-defined question formats
3. **Export Options**: Export to various formats (PDF, Word, etc.)
4. **Collaborative Editing**: Multiple users can edit collections
5. **Advanced Analytics**: Question difficulty analysis and trends
6. **Mobile App**: Native mobile application
7. **Integration APIs**: Connect with other educational platforms

### Performance Improvements

1. **Streaming Processing**: Process large files in chunks
2. **Background Jobs**: Move processing to background workers
3. **CDN Integration**: Faster file delivery
4. **Machine Learning**: Improve question extraction accuracy over time

## Support

For technical support or questions about the exam paper system:

1. Check the troubleshooting section above
2. Review the test files for usage examples
3. Examine the API documentation
4. Contact the development team

## License

This system is part of the Cognie AI platform and follows the same licensing terms. 