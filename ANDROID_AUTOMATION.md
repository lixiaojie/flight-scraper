# Android App Automation for Linux Cloud Servers

This document describes the Android app automation system that enables containerized Android app testing on Linux cloud servers.

## Overview

The Android automation system provides:
- **Containerized Android Environment**: Deploy Android emulators in Docker containers
- **Automated App Testing**: Download, install, and test Android applications
- **Screenshot Capture**: Generate publicly accessible screenshots of app states
- **Resource Management**: Monitor and manage container resources
- **Scalable Architecture**: Support for multiple concurrent automation sessions

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API    │    │  Android        │
│   (React)       │◄──►│   (FastAPI)      │◄──►│  Containers     │
│                 │    │                  │    │  (Docker)       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User          │    │   PostgreSQL     │    │   Nginx         │
│   Interface     │    │   Database       │    │   (Screenshots) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Features

### 1. Containerized Android System
- **Docker-based**: Uses `budtmo/docker-android` images
- **Multiple Android Versions**: Support for API 30, 29, 28, etc.
- **Resource Allocation**: Configurable CPU, memory, and disk limits
- **Network Access**: ADB and VNC ports exposed for management

### 2. Automated App Testing
- **APK Download**: Automatic download from URLs or platform configuration
- **App Installation**: Automated installation via ADB
- **App Launch**: Programmatic app launching and navigation
- **Screenshot Capture**: High-quality screenshots of app states

### 3. Management Interface
- **Web Dashboard**: React-based management interface
- **Session Tracking**: Monitor automation sessions and their status
- **Container Management**: Start, stop, and monitor containers
- **Resource Monitoring**: Real-time resource usage tracking

## Quick Start

### 1. Deploy to Linux Cloud Server

```bash
# Clone the repository
git clone <repository-url>
cd flight-scraper

# Make deployment script executable
chmod +x deploy-android-automation.sh

# Run deployment (requires sudo)
./deploy-android-automation.sh
```

### 2. Access the Application

- **Frontend**: http://your-server:3000
- **Backend API**: http://your-server:8000
- **API Documentation**: http://your-server:8000/docs
- **Android VNC**: http://your-server:6080

### 3. Start Android Automation

1. Navigate to **Android Automation** in the web interface
2. Click **Start Automation**
3. Select a platform (e.g., 12306)
4. Configure wait time and screenshot options
5. Click **Start Automation**

## API Endpoints

### Automation Management

```bash
# Start automation session
POST /api/v1/android-automation/start
{
  "platform_id": 1,
  "wait_time": 30,
  "capture_screenshot": true
}

# Get session status
GET /api/v1/android-automation/sessions/{session_id}

# List all sessions
GET /api/v1/android-automation/sessions

# Cleanup session
DELETE /api/v1/android-automation/sessions/{session_id}
```

### Container Management

```bash
# List containers
GET /api/v1/android-automation/containers

# Get container resources
GET /api/v1/android-automation/containers/{container_id}/resources

# Start container
POST /api/v1/android-automation/containers/{container_id}/start

# Stop container
POST /api/v1/android-automation/containers/{container_id}/stop
```

### Health Check

```bash
# System health
GET /api/v1/android-automation/health
```

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@db:5432/flight_scraper

# Redis
REDIS_URL=redis://redis:6379

# Android Configuration
ANDROID_CONTAINER_IMAGE=budtmo/docker-android:api_30_x86
ANDROID_CONTAINER_CPU_LIMIT=2.0
ANDROID_CONTAINER_MEMORY_LIMIT=4g
ANDROID_SCREENSHOTS_DIR=/app/screenshots
ANDROID_DOWNLOADS_DIR=/app/downloads
```

### Docker Compose Configuration

The system uses `docker-compose-android.yml` with the following services:

- **backend**: FastAPI application
- **frontend**: React application
- **db**: PostgreSQL database
- **redis**: Redis for Celery
- **celery**: Background task worker
- **celery-beat**: Task scheduler
- **android-emulator**: Android container for testing
- **nginx**: Web server for screenshots

## Usage Examples

### 1. Test 12306 App

```bash
# Start automation for 12306 platform
curl -X POST http://localhost:8000/api/v1/android-automation/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "platform_id": 1,
    "wait_time": 30,
    "capture_screenshot": true
  }'
```

### 2. Monitor Container Resources

```bash
# Get container resource usage
curl http://localhost:8000/api/v1/android-automation/containers/CONTAINER_ID/resources
```

### 3. View Screenshots

Screenshots are automatically served via Nginx at:
```
http://your-server/screenshots/screenshot_SESSION_ID.png
```

## Troubleshooting

### Common Issues

1. **Container Won't Start**
   ```bash
   # Check Docker daemon
   sudo systemctl status docker
   
   # Check container logs
   docker logs CONTAINER_ID
   ```

2. **ADB Connection Issues**
   ```bash
   # Check ADB connection
   docker exec CONTAINER_NAME adb devices
   
   # Restart ADB server
   docker exec CONTAINER_NAME adb kill-server
   docker exec CONTAINER_NAME adb start-server
   ```

3. **Screenshot Capture Fails**
   ```bash
   # Check container status
   docker ps
   
   # Verify app installation
   docker exec CONTAINER_NAME adb shell pm list packages | grep APP_PACKAGE
   ```

### Logs and Monitoring

```bash
# View application logs
./logs.sh

# Monitor system resources
./monitor.sh

# Check service health
curl http://localhost:8000/api/v1/android-automation/health
```

## Security Considerations

1. **Container Isolation**: Each automation session runs in isolated containers
2. **Network Security**: Firewall rules restrict access to necessary ports
3. **Resource Limits**: CPU and memory limits prevent resource exhaustion
4. **Cleanup Procedures**: Automatic cleanup of containers and temporary files
5. **Access Control**: Authentication required for all API endpoints

## Performance Optimization

1. **Container Reuse**: Reuse existing containers when possible
2. **Resource Monitoring**: Monitor and adjust resource allocation
3. **Parallel Processing**: Support for multiple concurrent sessions
4. **Caching**: Cache downloaded APKs and screenshots
5. **Cleanup**: Regular cleanup of old sessions and containers

## Development

### Adding New Platforms

1. Add platform to database via Settings interface
2. Ensure APK download URL is configured
3. Test automation with new platform

### Customizing Android Images

```dockerfile
# Custom Android image
FROM budtmo/docker-android:api_30_x86

# Install additional packages
RUN apt-get update && apt-get install -y \
    additional-package

# Configure Android settings
ENV EMULATOR_DEVICE="Custom Device"
```

### Extending Automation Logic

The automation service can be extended in `backend/app/services/android_automation_service.py`:

```python
class AndroidAutomationService:
    def custom_automation_step(self, session, container):
        # Add custom automation logic
        pass
```

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review application logs
3. Check container status and resources
4. Verify network connectivity and firewall rules

## License

This project is licensed under the MIT License.
