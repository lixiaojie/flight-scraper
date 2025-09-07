"""
Celery tasks for flight scraping operations
"""

import asyncio
from typing import List, Dict, Any
from celery import current_task
from sqlalchemy.orm import Session
from app.core.celery import celery_app
from app.core.database import SessionLocal
from app.models.task import Task, TaskStatus
from app.models.platform import Platform
from app.models.flight_data import FlightData
# from app.automation.web_scraper import WebScraper
# from app.services.data_processor import DataProcessor
from loguru import logger


@celery_app.task(bind=True)
def scrape_flight_task(self, task_id: int, platform_ids: List[int]):
    """
    Main Celery task for scraping flights from multiple platforms
    
    Args:
        task_id: ID of the task to execute
        platform_ids: List of platform IDs to scrape from
    """
    db = SessionLocal()
    try:
        # Get task from database
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            logger.error(f"Task {task_id} not found")
            return {"error": "Task not found"}
        
        # Update task status to running
        task.status = TaskStatus.RUNNING
        task.started_at = db.query(Task).filter(Task.id == task_id).first().created_at
        db.commit()
        
        # Update Celery task progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': len(platform_ids), 'status': 'Starting scraping...'}
        )
        
        all_flights = []
        successful_platforms = 0
        
        for i, platform_id in enumerate(platform_ids):
            try:
                # Get platform
                platform = db.query(Platform).filter(Platform.id == platform_id).first()
                if not platform or not platform.is_active:
                    logger.warning(f"Platform {platform_id} not found or inactive")
                    continue
                
                # Update progress
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i + 1,
                        'total': len(platform_ids),
                        'status': f'Scraping {platform.name}...'
                    }
                )
                
                # TODO: Implement actual scraping when selenium is available
                # For now, create mock data
                mock_flights = [
                    {
                        "task_id": task_id,
                        "platform_name": platform.name,
                        "departure_city": task.departure_city,
                        "arrival_city": task.arrival_city,
                        "departure_time": "2024-01-15 10:00:00",
                        "arrival_time": "2024-01-15 14:00:00",
                        "price": 299.99,
                        "airline": "Mock Airlines",
                        "flight_number": "MA123",
                        "cabin_class": task.cabin_class,
                        "currency": "USD"
                    }
                ]
                
                # Save mock data to database
                for flight_data in mock_flights:
                    flight = FlightData(**flight_data)
                    db.add(flight)
                
                all_flights.extend(mock_flights)
                successful_platforms += 1
                
                logger.info(f"Successfully created mock data for {platform.name}")
                
                # Add delay between platforms to avoid rate limiting
                if i < len(platform_ids) - 1:
                    import time
                    import random
                    delay = random.randint(5, 15)  # Random delay between 5-15 seconds
                    time.sleep(delay)
                
            except Exception as e:
                logger.error(f"Error scraping platform {platform_id}: {str(e)}")
                continue
        
        # Update task status
        if successful_platforms > 0:
            task.status = TaskStatus.COMPLETED
            task.completed_at = db.query(Task).filter(Task.id == task_id).first().created_at
        else:
            task.status = TaskStatus.FAILED
            task.error_message = "No platforms were successfully scraped"
        
        db.commit()
        
        # Return results
        return {
            'task_id': task_id,
            'total_flights': len(all_flights),
            'successful_platforms': successful_platforms,
            'total_platforms': len(platform_ids),
            'flights': all_flights[:10]  # Return first 10 flights as sample
        }
        
    except Exception as e:
        logger.error(f"Error in scrape_flight_task: {str(e)}")
        
        # Update task status to failed
        if 'task' in locals():
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            db.commit()
        
        return {"error": str(e)}
    
    finally:
        db.close()


@celery_app.task
def cleanup_old_tasks():
    """Clean up old completed tasks and their data"""
    db = SessionLocal()
    try:
        from datetime import datetime, timedelta
        
        # Delete tasks older than 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        old_tasks = db.query(Task).filter(
            Task.status.in_([TaskStatus.COMPLETED, TaskStatus.FAILED]),
            Task.completed_at < cutoff_date
        ).all()
        
        for task in old_tasks:
            # Delete associated flight data
            db.query(FlightData).filter(FlightData.task_id == task.id).delete()
            # Delete task
            db.delete(task)
        
        db.commit()
        logger.info(f"Cleaned up {len(old_tasks)} old tasks")
        
        return {"cleaned_tasks": len(old_tasks)}
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_tasks: {str(e)}")
        return {"error": str(e)}
    
    finally:
        db.close()


@celery_app.task
def update_task_status():
    """Update status of running tasks that may have timed out"""
    db = SessionLocal()
    try:
        from datetime import datetime, timedelta
        
        # Find tasks that have been running for more than 2 hours
        timeout_threshold = datetime.utcnow() - timedelta(hours=2)
        
        timeout_tasks = db.query(Task).filter(
            Task.status == TaskStatus.RUNNING,
            Task.started_at < timeout_threshold
        ).all()
        
        for task in timeout_tasks:
            task.status = TaskStatus.FAILED
            task.error_message = "Task timed out after 2 hours"
            task.completed_at = datetime.utcnow()
        
        db.commit()
        logger.info(f"Updated {len(timeout_tasks)} timed out tasks")
        
        return {"updated_tasks": len(timeout_tasks)}
        
    except Exception as e:
        logger.error(f"Error in update_task_status: {str(e)}")
        return {"error": str(e)}
    
    finally:
        db.close()


@celery_app.task
def test_scraping_platform(platform_id: int):
    """Test scraping a single platform to verify it's working"""
    db = SessionLocal()
    try:
        platform = db.query(Platform).filter(Platform.id == platform_id).first()
        if not platform:
            return {"error": "Platform not found"}
        
        # Create a test task
        test_task = Task(
            name="Test Scraping",
            departure_city="New York",
            arrival_city="Los Angeles",
            travel_date=datetime.utcnow() + timedelta(days=30),
            num_travelers=1,
            cabin_class="economy",
            status=TaskStatus.PENDING
        )
        db.add(test_task)
        db.commit()
        
        # TODO: Test actual scraping when selenium is available
        # For now, return mock success
        result = {"success": True, "data": [], "error_message": None}
        
        # Clean up test task
        db.delete(test_task)
        db.commit()
        
        return {
            "platform": platform.name,
            "success": result["success"],
            "flights_found": 0,  # Mock data
            "error": result["error_message"]
        }
        
    except Exception as e:
        logger.error(f"Error in test_scraping_platform: {str(e)}")
        return {"error": str(e)}
    
    finally:
        db.close()
