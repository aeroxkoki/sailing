"""
X¢Â’¡Y‹â¸åüë
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import oauth2_scheme, decode_access_token, verify_supabase_token
from app.db.database import get_db, get_supabase


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> dict:
    """
    ş(næü¶üÅ1’Ö—Y‹X¢Â
    
    e„koæü¶üâÇëLŸÅUŒ_›k
    æü¶üªÖ¸§¯È’ÔYˆFk	ôW~Y
    """
    try:
        payload = decode_access_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        
        # SSgæü¶üÅ1’DBK‰Ö—Y‹æ’ı 
        # ş(oâÃ¯Çü¿’ÔY
        user_data = {
            "id": user_id,
            "email": f"user_{user_id}@example.com",
            "is_active": True,
        }
        
        return user_data
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


def get_supabase_user(
    token: str = Depends(oauth2_scheme)
) -> dict:
    """
    Supabasen<’(Wfş(næü¶üÅ1’Ö—Y‹X¢Â
    """
    try:
        # SupabaseÈü¯ón<
        payload = verify_supabase_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate Supabase credentials",
            )
        
        # SupabaseK‰æü¶üÅ1’Ö—
        supabase = get_supabase()
        if supabase is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Supabase client not initialized",
            )
            
        # SnèoŸ›nSupabasen<¹Õk[f¿tLÅ
        user_response = supabase.auth.get_user(token)
        if user_response.error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=user_response.error.message,
            )
            
        return user_response.user
    except (JWTError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate Supabase credentials: {str(e)}",
        )
