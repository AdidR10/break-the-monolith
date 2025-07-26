from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import pika
import json
import logging
import sys
import os
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))
from shared.rabbitmq_config import rabbitmq

logger = logging.getLogger(__name__)

# Schemas
class NotificationCreate(BaseModel):
    user_id: str
    title: str
    message: str
    type: str = "info"  # info, success, warning, error
    ride_id: Optional[str] = None

class NotificationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    message: str
    type: str
    ride_id: Optional[str]
    sent_at: datetime
    status: str

app = FastAPI(title="RickshawX Notification Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for demo (use Redis/Database in production)
notifications_store = []

class NotificationHandler:
    def __init__(self):
        self.email_notifications = []
        self.push_notifications = []
    
    def send_email(self, notification: dict):
        """Mock email sending"""
        logger.info(f"Sending email to user {notification['user_id']}: {notification['title']}")
        self.email_notifications.append({
            **notification,
            "sent_at": datetime.utcnow(),
            "status": "sent"
        })
    
    def send_push(self, notification: dict):
        """Mock push notification"""
        logger.info(f"Sending push to user {notification['user_id']}: {notification['title']}")
        self.push_notifications.append({
            **notification,
            "sent_at": datetime.utcnow(),
            "status": "sent"
        })

notification_handler = NotificationHandler()

def setup_rabbitmq_consumers():
    """Setup RabbitMQ consumers for different notification types"""
    try:
        rabbitmq.connect()
        
        # Consume ride notifications
        def process_ride_notification(ch, method, properties, body):
            try:
                message = json.loads(body)
                notification = {
                    "id": str(message.get("ride_id", "")),
                    "user_id": message.get("rider_id", ""),
                    "title": f"Ride {message.get('status', '').replace('_', ' ').title()}",
                    "message": f"Your ride status: {message.get('status', '')}",
                    "type": "info",
                    "ride_id": message.get("ride_id")
                }
                
                # Send both email and push
                notification_handler.send_email(notification)
                notification_handler.send_push(notification)
                
                # Also notify driver if present
                if message.get("driver_id"):
                    driver_notification = {
                        **notification,
                        "user_id": message.get("driver_id"),
                        "title": f"Ride {message.get('status', '').replace('_', ' ').title()} - Driver",
                    }
                    notification_handler.send_email(driver_notification)
                    notification_handler.send_push(driver_notification)
                
                ch.basic_ack(delivery_tag=method.delivery_tag)
                
            except Exception as e:
                logger.error(f"Error processing ride notification: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        
        # Setup consumers
        rabbitmq.channel.basic_consume(
            queue='ride.requested',
            on_message_callback=process_ride_notification
        )
        rabbitmq.channel.basic_consume(
            queue='ride.accepted',
            on_message_callback=process_ride_notification
        )
        rabbitmq.channel.basic_consume(
            queue='ride.completed',
            on_message_callback=process_ride_notification
        )
        rabbitmq.channel.basic_consume(
            queue='ride.cancelled',
            on_message_callback=process_ride_notification
        )
        
    except Exception as e:
        logger.error(f"Failed to setup RabbitMQ consumers: {e}")

@app.on_event("startup")
async def startup():
    setup_rabbitmq_consumers()

@app.post("/api/v1/notifications", response_model=NotificationResponse)
async def send_notification(notification: NotificationCreate):
    """Send notification manually"""
    notification_dict = {
        "id": f"notif_{len(notifications_store) + 1}",
        **notification.dict(),
        "sent_at": datetime.utcnow(),
        "status": "sent"
    }
    
    # Send via different channels
    notification_handler.send_email(notification_dict)
    notification_handler.send_push(notification_dict)
    
    notifications_store.append(notification_dict)
    return notification_dict

@app.get("/api/v1/notifications/{user_id}", response_model=List[NotificationResponse])
async def get_user_notifications(user_id: str):
    """Get notifications for user"""
    user_notifications = [
        notif for notif in notifications_store 
        if notif["user_id"] == user_id
    ]
    return user_notifications

@app.get("/api/v1/notifications/stats")
async def get_notification_stats():
    """Get notification statistics"""
    return {
        "total_notifications": len(notifications_store),
        "emails_sent": len(notification_handler.email_notifications),
        "push_notifications_sent": len(notification_handler.push_notifications),
        "recent_notifications": notifications_store[-10:] if notifications_store else []
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "notification-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004) 