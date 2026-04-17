@echo off
REM Solarware Development Bootstrap Script for Windows

echo.
echo 🌞 Solarware Development Setup
echo ===============================
echo.

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker not found. Install from: https://www.docker.com/products/docker-desktop
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose not found. Install via Docker Desktop or manually.
    exit /b 1
)

echo ✅ Docker and Docker Compose found
echo.

REM Create .env if not exists
if not exist .env (
    echo 📝 Creating .env from template...
    copy .env.template .env
    echo ✅ .env created. Edit as needed.
) else (
    echo ✅ .env already exists
)

echo.
echo 📦 Starting services with docker-compose...
echo.

REM Start services
docker-compose up -d

echo.
echo ✅ Services started!
echo.
echo 📋 Next steps:
echo    1. Backend API: http://localhost:8000
echo    2. Frontend: http://localhost:3000 (or http://localhost:5173)
echo    3. API Docs: http://localhost:8000/docs
echo    4. Database: localhost:5432 (user: solarware, password: solarware_dev_password)
echo.
echo 📊 View logs:
echo    docker-compose logs -f backend
echo    docker-compose logs -f frontend
echo.
echo 🛑 Stop services:
echo    docker-compose down
echo.
echo 💡 To run tests:
echo    docker-compose exec backend pytest
echo.
