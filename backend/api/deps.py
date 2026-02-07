from fastapi import Depends, HTTPException, status, Path
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/sign-in/email")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.BETTER_AUTH_SECRET, algorithms=["HS256"])
        user_id: str = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        return {"user_id": str(user_id)}
    except JWTError as e:
        print(f"Debug Error: {str(e)}")
        raise credentials_exception


async def verify_user(
    user_id: str = Path(..., description="User ID from path"),
    current_user: dict = Depends(get_current_user)
) -> str:
    """
    Verify that the path user_id matches the JWT user_id.

    Returns:
        str: The verified user_id

    Raises:
        HTTPException 401: If JWT is invalid
        HTTPException 403: If path user_id doesn't match JWT user_id
    """
    jwt_user_id = str(current_user.get("user_id"))
    path_user_id = str(user_id)

    if jwt_user_id != path_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User ID mismatch",
        )

    return path_user_id