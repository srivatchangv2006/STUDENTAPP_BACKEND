# Student Learning Platform Backend

A Django-based backend for the student learning platform with quiz generation, user management, and posts functionality.

## Project Structure

```
studentapp_backend/
├── accounts/         # User authentication and management
├── quiz/            # Quiz generation and management
├── posts/           # User posts and discussions
├── media/           # Media file storage
└── studentapp_backend/  # Main project settings
```

## Available Endpoints

### Authentication & User Management (`/api/accounts/`)
- `POST /api/accounts/users/` - Register new user
- `POST /api/token/` - Get JWT token (login)
- `POST /api/token/refresh/` - Refresh JWT token
### Quiz System (`/api/quiz/`)
- `POST /quiz/stories/create/` - Create a new story/passage
- `POST /quiz/attempts/create/` - Start a new quiz attempt
- `POST /quiz/attempts/{attempt_id}/submit/` - Submit quiz answers
- `GET /quiz/attempts/{pk}/` - Get quiz attempt details
- `GET /quiz/history/` - Get user's quiz history
- `POST /quiz/stories/{story_id}/regenerate/` - Regenerate quiz for a story
- `GET /quiz/points/` - Get user's points
- `GET /quiz/leaderboard/` - Get quiz leaderboard 

### Posts System (`/api/posts/`)
- `GET /posts/` - List all posts
- `POST /posts/` - Create new post
- `GET /posts/{id}/` - Get single post
- `PUT /posts/{id}/` - Update post
- `DELETE /posts/{id}/` - Delete post

## Features Implemented

### User Management
- Custom User model
- JWT Authentication
- Profile management

### Quiz System
- Story/passage creation
- AI-powered quiz generation
- Quiz attempts tracking
- Quiz history

### Posts System
- CRUD operations for posts
- User-specific post management
- Post listing and filtering

## Database
- Using SQLite3 for development
- Models implemented:
  - Custom User model
  - Quiz models (Story, Question, Attempt)
  - Post model

## Environment Variables
Required environment variables in `.env`:
- `SECRET_KEY` - Django secret key
- `GEMINI_API_KEY` - Google Gemini API key for quiz generation

## API Security
- JWT Authentication required for most endpoints
- Permission classes implemented for secure access
- Token refresh mechanism

## Media Handling
- Media files stored in `/media` directory
- Support for user profile pictures and post attachments 
