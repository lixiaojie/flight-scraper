"""
Platform service for managing target platforms and accounts
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models.platform import Platform, Account, PlatformType
from app.schemas.platform import PlatformCreate, PlatformUpdate, PlatformResponse, AccountCreate, AccountResponse
from app.core.security import encrypt_password, decrypt_password


class PlatformService:
    """Service for managing platforms and accounts"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_platforms(
        self,
        platform_type: Optional[PlatformType] = None,
        is_active: Optional[bool] = None
    ) -> List[PlatformResponse]:
        """Get platforms with optional filtering"""
        query = self.db.query(Platform)
        
        if platform_type:
            query = query.filter(Platform.platform_type == platform_type)
        
        if is_active is not None:
            query = query.filter(Platform.is_active == is_active)
        
        platforms = query.order_by(Platform.name).all()
        return [PlatformResponse.from_orm(platform) for platform in platforms]
    
    async def create_platform(self, platform_data: PlatformCreate) -> PlatformResponse:
        """Create a new platform"""
        platform = Platform(**platform_data.dict())
        self.db.add(platform)
        self.db.commit()
        self.db.refresh(platform)
        return PlatformResponse.from_orm(platform)
    
    async def get_platform_by_id(self, platform_id: int) -> Optional[PlatformResponse]:
        """Get a platform by ID"""
        platform = self.db.query(Platform).filter(Platform.id == platform_id).first()
        return PlatformResponse.from_orm(platform) if platform else None
    
    async def update_platform(self, platform_id: int, platform_data: PlatformUpdate) -> Optional[PlatformResponse]:
        """Update a platform"""
        platform = self.db.query(Platform).filter(Platform.id == platform_id).first()
        if not platform:
            return None
        
        update_data = platform_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(platform, field, value)
        
        platform.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(platform)
        return PlatformResponse.from_orm(platform)
    
    async def delete_platform(self, platform_id: int) -> bool:
        """Delete a platform"""
        platform = self.db.query(Platform).filter(Platform.id == platform_id).first()
        if not platform:
            return False
        
        self.db.delete(platform)
        self.db.commit()
        return True
    
    async def get_platform_accounts(self, platform_id: int) -> List[AccountResponse]:
        """Get accounts for a platform"""
        accounts = self.db.query(Account).filter(Account.platform_id == platform_id).all()
        return [AccountResponse.from_orm(account) for account in accounts]
    
    async def create_account(self, platform_id: int, account_data: AccountCreate) -> AccountResponse:
        """Create a new account for a platform"""
        # Encrypt password before storing
        encrypted_password = encrypt_password(account_data.password)
        
        account = Account(
            platform_id=platform_id,
            username=account_data.username,
            password=encrypted_password,
            email=account_data.email,
            max_queries_per_day=account_data.max_queries_per_day,
            is_active=account_data.is_active,
            is_verified=account_data.is_verified
        )
        
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return AccountResponse.from_orm(account)
    
    async def get_account_by_id(self, account_id: int) -> Optional[AccountResponse]:
        """Get an account by ID"""
        account = self.db.query(Account).filter(Account.id == account_id).first()
        return AccountResponse.from_orm(account) if account else None
    
    async def update_account(self, account_id: int, account_data: AccountCreate) -> Optional[AccountResponse]:
        """Update an account"""
        account = self.db.query(Account).filter(Account.id == account_id).first()
        if not account:
            return None
        
        # Encrypt password if provided
        if account_data.password:
            account.password = encrypt_password(account_data.password)
        
        account.username = account_data.username
        account.email = account_data.email
        account.max_queries_per_day = account_data.max_queries_per_day
        account.is_active = account_data.is_active
        account.is_verified = account_data.is_verified
        account.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(account)
        return AccountResponse.from_orm(account)
    
    async def delete_account(self, account_id: int) -> bool:
        """Delete an account"""
        account = self.db.query(Account).filter(Account.id == account_id).first()
        if not account:
            return False
        
        self.db.delete(account)
        self.db.commit()
        return True
