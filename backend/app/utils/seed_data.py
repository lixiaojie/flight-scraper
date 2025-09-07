"""
Seed data for initial setup
"""

from sqlalchemy.orm import Session
from app.models.platform import Platform, Account, PlatformType
from app.models.user import User
from app.core.security import get_password_hash
from app.core.database import SessionLocal


def create_sample_platforms():
    """Create sample platforms for testing"""
    db = SessionLocal()
    
    try:
        # Check if platforms already exist
        if db.query(Platform).count() > 0:
            print("Platforms already exist, skipping seed data creation")
            return
        
        # Create sample platforms
        platforms_data = [
            {
                'name': 'expedia',
                'display_name': 'Expedia',
                'platform_type': PlatformType.WEB,
                'base_url': 'https://www.expedia.com/Flights',
                'search_url_template': 'https://www.expedia.com/Flights-Search?leg1=from:{departure},to:{arrival},departure:{date}TANYT&passengers=children:0,adults:{travelers},seniors:0,infantinlap:Y&options=cabinclass:{cabin_class}',
                'is_active': True
            },
            {
                'name': 'kayak',
                'display_name': 'Kayak',
                'platform_type': PlatformType.WEB,
                'base_url': 'https://www.kayak.com/flights',
                'search_url_template': 'https://www.kayak.com/flights/{departure}-{arrival}/{date}',
                'is_active': True
            },
            {
                'name': 'skyscanner',
                'display_name': 'Skyscanner',
                'platform_type': PlatformType.WEB,
                'base_url': 'https://www.skyscanner.com/transport/flights',
                'search_url_template': 'https://www.skyscanner.com/transport/flights/{departure}/{arrival}/{date}',
                'is_active': True
            },
            {
                'name': 'google_flights',
                'display_name': 'Google Flights',
                'platform_type': PlatformType.WEB,
                'base_url': 'https://www.google.com/travel/flights',
                'search_url_template': 'https://www.google.com/travel/flights?q=Flights%20from%20{departure}%20to%20{arrival}%20on%20{date}',
                'is_active': True
            }
        ]
        
        for platform_data in platforms_data:
            platform = Platform(**platform_data)
            db.add(platform)
        
        db.commit()
        print(f"Created {len(platforms_data)} sample platforms")
        
    except Exception as e:
        print(f"Error creating sample platforms: {str(e)}")
        db.rollback()
    finally:
        db.close()


def create_sample_user():
    """Create a sample user for testing"""
    db = SessionLocal()
    
    try:
        # Check if users already exist
        if db.query(User).count() > 0:
            print("Users already exist, skipping user creation")
            return
        
        # Create sample user
        user = User(
            username='admin',
            email='admin@example.com',
            hashed_password=get_password_hash('admin123'),
            is_active=True,
            is_verified=True
        )
        
        db.add(user)
        db.commit()
        print("Created sample user: admin/admin123")
        
    except Exception as e:
        print(f"Error creating sample user: {str(e)}")
        db.rollback()
    finally:
        db.close()


def seed_all():
    """Seed all sample data"""
    print("Seeding sample data...")
    create_sample_user()
    create_sample_platforms()
    print("Sample data seeding completed!")


if __name__ == "__main__":
    seed_all()
