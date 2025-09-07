"""
Platform management API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.platform import Platform, Account, PlatformType
from app.schemas.platform import PlatformCreate, PlatformUpdate, PlatformResponse, AccountCreate, AccountResponse
from app.services.platform_service import PlatformService

router = APIRouter()


@router.get("/", response_model=List[PlatformResponse])
async def get_platforms(
    platform_type: Optional[PlatformType] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get list of platforms"""
    
    try:
        platform_service = PlatformService(db)
        platforms = await platform_service.get_platforms(
            platform_type=platform_type,
            is_active=is_active
        )
        return platforms
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching platforms: {str(e)}")


@router.post("/", response_model=PlatformResponse)
async def create_platform(
    platform_data: PlatformCreate,
    db: Session = Depends(get_db)
):
    """Create a new platform"""
    
    try:
        platform_service = PlatformService(db)
        platform = await platform_service.create_platform(platform_data)
        return platform
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating platform: {str(e)}")


@router.get("/{platform_id}", response_model=PlatformResponse)
async def get_platform(
    platform_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific platform by ID"""
    
    try:
        platform_service = PlatformService(db)
        platform = await platform_service.get_platform_by_id(platform_id)
        
        if not platform:
            raise HTTPException(status_code=404, detail="Platform not found")
            
        return platform
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching platform: {str(e)}")


@router.put("/{platform_id}", response_model=PlatformResponse)
async def update_platform(
    platform_id: int,
    platform_data: PlatformUpdate,
    db: Session = Depends(get_db)
):
    """Update a platform"""
    
    try:
        platform_service = PlatformService(db)
        platform = await platform_service.update_platform(platform_id, platform_data)
        
        if not platform:
            raise HTTPException(status_code=404, detail="Platform not found")
            
        return platform
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error updating platform: {str(e)}")


@router.delete("/{platform_id}")
async def delete_platform(
    platform_id: int,
    db: Session = Depends(get_db)
):
    """Delete a platform"""
    
    try:
        platform_service = PlatformService(db)
        success = await platform_service.delete_platform(platform_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Platform not found")
            
        return {"message": "Platform deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting platform: {str(e)}")


# Account endpoints
@router.get("/{platform_id}/accounts", response_model=List[AccountResponse])
async def get_platform_accounts(
    platform_id: int,
    db: Session = Depends(get_db)
):
    """Get accounts for a platform"""
    
    try:
        platform_service = PlatformService(db)
        accounts = await platform_service.get_platform_accounts(platform_id)
        return accounts
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching accounts: {str(e)}")


@router.post("/{platform_id}/accounts", response_model=AccountResponse)
async def create_account(
    platform_id: int,
    account_data: AccountCreate,
    db: Session = Depends(get_db)
):
    """Create a new account for a platform"""
    
    try:
        platform_service = PlatformService(db)
        account = await platform_service.create_account(platform_id, account_data)
        return account
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating account: {str(e)}")


@router.get("/accounts/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific account by ID"""
    
    try:
        platform_service = PlatformService(db)
        account = await platform_service.get_account_by_id(account_id)
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
            
        return account
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching account: {str(e)}")


@router.put("/accounts/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: int,
    account_data: AccountCreate,  # Reuse for updates
    db: Session = Depends(get_db)
):
    """Update an account"""
    
    try:
        platform_service = PlatformService(db)
        account = await platform_service.update_account(account_id, account_data)
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
            
        return account
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error updating account: {str(e)}")


@router.delete("/accounts/{account_id}")
async def delete_account(
    account_id: int,
    db: Session = Depends(get_db)
):
    """Delete an account"""
    
    try:
        platform_service = PlatformService(db)
        success = await platform_service.delete_account(account_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Account not found")
            
        return {"message": "Account deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting account: {str(e)}")
