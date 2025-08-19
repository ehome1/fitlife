# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Application Startup
```bash
# Quick start (recommended)
python start.py

# Start with dependency installation
python start.py --install

# Alternative startup methods
python app.py                    # Direct Flask app start
python quick_start.py            # Alternative launcher
```

### Database Operations
```bash
# Initialize database
python init_db.py

# Migrate database (production)
python migrate_database.py

# Database schema fixes
python migrate_production_db.py
```

### Testing
```bash
# Core functionality tests
python test_app.py               # Basic app functionality
python test_admin_login.py       # Admin system test
python test_dashboard.py         # Dashboard functionality
python test_meal_system.py       # Meal logging system
python test_exercise_api.py      # Exercise tracking

# Specific feature tests
python test_natural_language_parsing.py  # AI food parsing
python test_unified_analysis.py          # AI analysis features
python test_full_flow.py                # End-to-end workflow
```

### Linting and Code Quality
No specific linting configuration found. Use standard Python tools:
```bash
python -m py_compile app.py      # Syntax check
```

## Architecture Overview

### Core Application Structure
- **Main App**: `app.py` - Single-file Flask application with all routes, models, and AI integration
- **Database**: SQLAlchemy ORM with SQLite (dev) / PostgreSQL (production) auto-detection
- **Templates**: Jinja2 templates in `templates/` with responsive Bootstrap 5 design
- **AI Integration**: Google Gemini API for nutrition and exercise analysis

### Database Models
The application uses a unified model structure in `app.py`:

- **User**: Core user authentication with Flask-Login
- **UserProfile**: Physical stats (height, weight, age, gender, activity_level, BMR)
- **FitnessGoal**: User-defined fitness objectives with target tracking
- **ExerciseLog**: Exercise tracking with AI analysis integration
- **MealLog**: Nutrition logging with natural language parsing
- **AdminUser**: Separate admin authentication system
- **PromptTemplate**: AI prompt management for admin users

### Key Architecture Patterns

**Dual Database Support**: 
- Development: SQLite (`fitness_app.db`)
- Production: PostgreSQL (detected via `DATABASE_URL` or `VERCEL` env vars)
- Auto-migration with `ensure_database_schema()` function

**AI Integration Architecture**:
- `call_gemini_meal_analysis()`: Natural language food parsing and nutrition analysis
- `call_gemini_exercise_analysis()`: Exercise analysis and recommendations  
- `get_gemini_model()`: Centralized Gemini API configuration
- Fallback systems for when API is unavailable

**Dual User Systems**:
- Regular users: Standard authentication via `User` model
- Admin users: Separate `AdminUser` model with role-based access
- Combined login loader handles both user types

**Template Architecture**:
- `base.html`: Core layout with Bootstrap 5 and Chart.js
- User templates: `dashboard.html`, `meal_log_new.html`, `exercise_log.html`
- Admin templates: `admin/base.html`, `admin/dashboard.html`, `admin/prompts.html`

## Critical Configuration

### Environment Variables
```bash
GEMINI_API_KEY=your_gemini_api_key     # Required for AI features
DATABASE_URL=postgresql://...          # Production database (optional)
SECRET_KEY=your_secret_key            # Flask session security
VERCEL=1                              # Production environment flag
```

### Database Schema Auto-Repair
The app includes automatic schema migration for compatibility:
- `ensure_database_schema()` runs at startup
- Adds missing columns: `food_description`, `amount`, `unit`, `meal_score`
- Handles SQLite → PostgreSQL differences

### AI System Configuration
- **Gemini Model**: `gemini-2.5-flash` (configured in `get_gemini_model()`)
- **Caching**: Memory cache for AI results (`ai_analysis_cache`)
- **Fallback**: Local calculations when AI unavailable

## Key Routes and Functionality

### User Routes
- `/` - Landing page (redirects to dashboard if logged in)
- `/register`, `/login` - User authentication
- `/dashboard` - Main user interface with daily stats
- `/meal-log` - Nutrition tracking with AI analysis
- `/exercise-log` - Exercise tracking with AI analysis
- `/progress` - Data visualization and trends

### Admin Routes  
- `/admin/login` - Admin authentication (admin/admin123)
- `/admin` - Admin dashboard
- `/admin/users` - User management
- `/admin/prompts` - AI prompt template management

### API Endpoints
- `/api/meal-analysis/<int:meal_id>` - Get saved meal analysis
- `/api/meal/<int:meal_id>` - DELETE meal records
- `/test-ai` - AI system testing endpoint
- `/health` - Application health check

## Development Notes

### Port Configuration
Default port is 5001 (not 5000 to avoid macOS AirPlay conflicts). Auto-detection prevents port conflicts.

### Frontend Architecture
- **Real-time Updates**: JavaScript handles DOM updates for deletions/additions
- **AI Analysis Display**: Streaming-style UI for analysis results
- **Responsive Design**: Bootstrap 5 with custom CSS gradients and animations
- **Chart Integration**: Chart.js for progress visualization

### Database Compatibility Layer
The app handles schema differences between development and production:
- Compatibility properties in models (e.g., `meal_date` → `date`)
- Automatic field migration on startup
- Graceful fallbacks for missing fields

### Testing Strategy
Multiple test files cover different aspects:
- Unit tests for individual features
- Integration tests for full workflows  
- Admin functionality validation
- AI system testing with fallbacks

The codebase is designed for easy deployment to Vercel with minimal configuration changes.