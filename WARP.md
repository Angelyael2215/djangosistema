# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

OrticorpSystem is a Django 5.2.6 web application project. Currently, this is a fresh Django installation with only the default configuration and no custom applications.

### Architecture

- **Framework**: Django 5.2.6
- **Database**: SQLite3 (development default)
- **Project Structure**: Standard Django project layout
  - `OrticorpSystem/` - Main project package containing settings, URLs, and WSGI/ASGI configuration
  - `manage.py` - Django's command-line utility for administrative tasks

### Key Configuration

- **Settings Module**: `OrticorpSystem.settings`
- **Root URL Configuration**: `OrticorpSystem.urls`
- **Database**: SQLite3 database file will be created as `db.sqlite3` in the project root
- **Static Files**: Served from `/static/` URL path
- **Template Engine**: Django Templates (default configuration)
- **Authentication**: Django's built-in authentication system

## Development Setup

### Environment Setup
Since Django is not currently installed in the active Python environment, you'll need to:

```powershell
# Install Django (recommended: use a virtual environment first)
pip install django

# Or install from requirements file if one exists
pip install -r requirements.txt
```

### Database Management
```powershell
# Create and apply initial migrations
python manage.py migrate

# Create a superuser for admin access
python manage.py createsuperuser

# Make migrations for model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

### Development Server
```powershell
# Run the development server (default: http://127.0.0.1:8000/)
python manage.py runserver

# Run on specific port
python manage.py runserver 8080

# Run on all interfaces
python manage.py runserver 0.0.0.0:8000
```

### Django Management Commands
```powershell
# Create a new Django app
python manage.py startapp app_name

# Check for common issues
python manage.py check

# Open Django shell
python manage.py shell

# Collect static files (for production)
python manage.py collectstatic

# Show available management commands
python manage.py help
```

### Testing
```powershell
# Run all tests
python manage.py test

# Run tests for specific app
python manage.py test app_name

# Run tests with verbose output
python manage.py test --verbosity=2

# Run specific test class or method
python manage.py test app_name.tests.TestClassName
python manage.py test app_name.tests.TestClassName.test_method_name
```

## Current Project Status

This appears to be a fresh Django project with:
- Default Django configuration
- No custom applications yet
- Default SQLite database configuration
- Standard Django project structure
- DEBUG mode enabled (development setting)

## Next Development Steps

When expanding this project, consider:

1. **Environment Setup**: Create a virtual environment and requirements.txt file
2. **App Creation**: Create Django apps using `python manage.py startapp app_name`
3. **Database Configuration**: Configure production database settings in settings.py
4. **Static/Media Files**: Configure static and media file handling
5. **Templates**: Set up template directories and base templates
6. **Authentication**: Configure user authentication and authorization
7. **Testing**: Set up test structure and CI/CD pipeline

## File Structure

```
DjangoOrticorpSistem/
├── OrticorpSystem/
│   ├── __init__.py
│   ├── settings.py      # Main Django settings
│   ├── urls.py          # Root URL configuration
│   ├── wsgi.py          # WSGI configuration for deployment
│   └── asgi.py          # ASGI configuration for async support
├── manage.py            # Django management utility
└── db.sqlite3           # SQLite database (created after first migration)
```

## Security Notes

- The current `SECRET_KEY` in settings.py is for development only
- `DEBUG = True` should be set to `False` in production
- `ALLOWED_HOSTS` needs to be configured for production deployment
- Consider using environment variables for sensitive configuration