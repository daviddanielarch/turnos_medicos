# Configuration Guide

This guide explains how to configure the hosts and environment variables for both the mobile app and Django backend.

## Mobile App Configuration

The mobile app (React Native/Expo) needs to know where your Django backend API is running.

### Method 1: Environment Variable (Recommended)

Create a `.env` file in the `mobile/allende/` directory:

```bash
# API Configuration
EXPO_PUBLIC_API_HOST=http://localhost:8000
```

### Method 2: App Configuration

Update the `mobile/allende/app.json` file:

```json
{
  "expo": {
    "extra": {
      "apiHost": "http://localhost:8000"
    }
  }
}
```

### Method 3: Default Fallback

If neither is configured, it defaults to `http://localhost:8000`.

## Django Backend Configuration

The Django backend has several configurable settings via environment variables.

### CORS Configuration

Configure which origins are allowed to access the API:

```bash
# Allow all origins (development only)
CORS_ALLOW_ALL_ORIGINS=True

# Or specify allowed origins (comma-separated)
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8081,http://localhost:19006,exp://localhost:19000
```

### Database Configuration

```bash
PGDATABASE=liftoff
PGUSER=unicodeveloper
PGPASSWORD=your_password
PGHOST=localhost
PGPORT=5432
```

### Selenium Configuration

```bash
SELENIUM_HOSTNAME=localhost
SELENIUM_PORT=4444
SELENIUM_IMPLICIT_WAIT=10
```

### Telegram Configuration

```bash
TELEGRAM_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

## API Endpoints

The Django backend provides the following API endpoints:

- `GET /api/doctors/` - Get all doctors with their specialties and locations
- `GET /api/appointment-types/?doctor_id=<id>` - Get appointment types for a specific doctor
- `POST /api/create-appointment/` - Create a new appointment search
- `GET /api/find-appointments/` - Get all active appointment searches
- `POST /api/update-appointment-status/` - Update the active status of an appointment search
- `GET /api/best-appointments/` - Get the best appointments found for each doctor

## Environment Variables Reference

### Mobile App

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `EXPO_PUBLIC_API_HOST` | Django API base URL | `http://localhost:8000` | `https://api.example.com` |

### Django Backend

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `CORS_ALLOW_ALL_ORIGINS` | Allow all CORS origins | `True` | `False` |
| `CORS_ALLOWED_ORIGINS` | Comma-separated allowed origins | `http://localhost:3000,http://localhost:8081,http://localhost:19006,exp://localhost:19000` | `https://app.example.com,https://mobile.example.com` |
| `PGDATABASE` | PostgreSQL database name | `liftoff` | `myapp_prod` |
| `PGUSER` | PostgreSQL username | `unicodeveloper` | `dbuser` |
| `PGPASSWORD` | PostgreSQL password | `` | `secure_password` |
| `PGHOST` | PostgreSQL host | `localhost` | `db.example.com` |
| `PGPORT` | PostgreSQL port | `5432` | `5432` |
| `SELENIUM_HOSTNAME` | Selenium server hostname | `localhost` | `selenium.example.com` |
| `SELENIUM_PORT` | Selenium server port | `4444` | `4444` |
| `SELENIUM_IMPLICIT_WAIT` | Selenium implicit wait time | `10` | `15` |
| `TELEGRAM_TOKEN` | Telegram bot token | `None` | `123456789:ABCdefGHIjklMNOpqrsTUVwxyz` |
| `TELEGRAM_CHAT_ID` | Telegram chat ID | `None` | `123456789` |

## Development vs Production

### Development

For local development, you typically want:

```bash
# Mobile app
EXPO_PUBLIC_API_HOST=http://localhost:8000

# Django backend
CORS_ALLOW_ALL_ORIGINS=True
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8081,http://localhost:19006,exp://localhost:19000
```

### Production

For production deployment:

```bash
# Mobile app
EXPO_PUBLIC_API_HOST=https://api.yourdomain.com

# Django backend
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=https://app.yourdomain.com,https://mobile.yourdomain.com
```

## Docker Configuration

If you're using Docker, you can set environment variables in your `docker-compose.yml`:

```yaml
services:
  web:
    environment:
      - CORS_ALLOW_ALL_ORIGINS=False
      - CORS_ALLOWED_ORIGINS=https://app.example.com
      - PGDATABASE=myapp_prod
      - PGUSER=dbuser
      - PGPASSWORD=secure_password
```

## Troubleshooting

### Mobile App Can't Connect to API

1. Check that `EXPO_PUBLIC_API_HOST` is set correctly
2. Verify the Django server is running on the specified host/port
3. Check CORS settings in Django if getting CORS errors
4. Ensure the API endpoints are accessible from the mobile app's network

### CORS Errors

1. Verify `CORS_ALLOWED_ORIGINS` includes your mobile app's origin
2. Check that `CORS_ALLOW_ALL_ORIGINS` is set appropriately for your environment
3. Ensure the Django CORS middleware is properly configured

### Database Connection Issues

1. Verify PostgreSQL is running and accessible
2. Check database credentials in environment variables
3. Ensure the database exists and is accessible to the configured user 