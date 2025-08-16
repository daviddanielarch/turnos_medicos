# Turnos Médicos - Medical Appointment System

The main driver behind this system is the fact that sometimes we need to wait for a couple of months in order to get an appointment with our favorite doctor. Since waiting sucks, and it is pretty common for people to cancel their appointments, this system was designed with the idea to be able to get appointments sooner by grabbing appointments cancelled by other patients.

## 🏥 Project Overview

This system helps patients find and manage medical appointments at Sanatorio Allende in Córdoba, Argentina. It includes:

- **Automated Appointment Finder**: Uses Selenium for handling Allende's authentication
- **Django Backend API**: RESTful API with Auth0 authentication
- **React Native Mobile App**: Cross-platform mobile application for patients
- **Push Notifications**: Mobile push notifications for appointment updates

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Mobile App    │    │  Django Backend │    │  Automation     │
│  (React Native) │◄──►│     (API)       │◄──►│   (Selenium)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                     
         │                       │                     
         ▼                       ▼                     
┌─────────────────┐    ┌─────────────────┐  
│   Auth0 Auth    │    │  PostgreSQL DB  │  
└─────────────────┘    └─────────────────┘  
```

## 🚀 Features

### Core Functionality

- **Automated Appointment Monitoring**: Continuously checks for better appointment slots
- **Real-time Notifications**: Push notifications for appointment updates
- **Multi-platform Support**: Web API and mobile app
- **User Authentication**: Secure Auth0-based authentication
- **Patient Management**: Multiple patient profiles per user

### Mobile App Features

- **Cross-platform**: iOS and Android support via React Native/Expo
- **Real-time Updates**: Live appointment status updates
- **Push Notifications**: Instant alerts for appointment changes

### Backend Features

- **RESTful API**: Comprehensive API for all operations
- **Database Management**: PostgreSQL with Django ORM
- **Authentication**: JWT-based Auth0 integration
- **CORS Support**: Cross-origin resource sharing
- **Admin Interface**: Django admin for data management

## 📋 Prerequisites

### System Requirements

- **Python 3.8+**
- **Node.js 18+**
- **PostgreSQL 15+**
- **Docker & Docker Compose**
- **Chrome/Chromium** (for Selenium automation)

### External Services

- **Auth0 Account** (for authentication)
- **Expo Account** (for mobile app deployment)

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd turnos_medicos
```

### 2. Backend Setup

#### Install Python Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Database Setup

```bash
# Start PostgreSQL with Docker
docker-compose up -d postgres

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser
```

#### Environment Configuration

Create a `.env` file in the root directory:

```bash
# Database
PGDATABASE=liftoff
PGUSER=unicodeveloper
PGPASSWORD=your_password
PGHOST=localhost
PGPORT=5432

# Auth0 Configuration
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_CLIENT_ID=your-auth0-client-id
AUTH0_AUDIENCE=https://your-api-identifier

# CORS Configuration
CORS_ALLOW_ALL_ORIGINS=True
```

### 3. Mobile App Setup

#### Install Node.js Dependencies

```bash
cd mobile/allende
npm install
```

#### Environment Configuration

Create a `.env` file in `mobile/allende/`:

```bash
EXPO_PUBLIC_API_HOST=http://localhost:8000
```

### 4. Selenium Setup (for Automation)

#### Using Docker (Recommended)

```bash
# For x86 systems
make run-chrome-x86

# For ARM systems (M1/M2 Macs)
make run-chrome-arm
```

#### Manual Setup

Install Chrome/Chromium and ChromeDriver on your system.

## 🚀 Running the Application

### Backend Development Server

```bash
# Start the Django development server
python manage.py runserver

# The API will be available at http://localhost:8000
```

### Mobile App Development

```bash
# Start Expo development server
cd mobile/allende
make expo-start

# Or directly with npm
npm start
```

## 🧪 Testing

### Backend Tests

```bash
# Run all tests
make test
```

### Code Quality

```bash
# Format code
make format

# Run pre-commit hooks
make precommit-run

# Setup pre-commit (first time)
make precommit-setup
```

## 🐳 Docker

### Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

## 📈 Monitoring & Logging

- **Sentry Integration**: Error tracking and monitoring
- **Logging**: Comprehensive logging throughout the application

## 🚀 Deployments

- **Automated deployments** Deployments are performed automatically on merge to main.
- **Simple Infrastructure** Code runs on Railway
