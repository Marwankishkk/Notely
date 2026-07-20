from fastapi import Depends, HTTPException, status

from core.config import settings
from core.jwt import get_current_user


async def get_current_admin(current_user=Depends(get_current_user)):
    if current_user.email.lower() not in settings.admin_emails:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
