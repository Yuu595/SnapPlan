"""Mock token authentication and role-based authorization."""
from fastapi import Header

from .errors import ApiError, UNAUTHORIZED

# Predefined mock users. No login or password storage in this assignment.
USERS = {
    "user-a-token": {"id": "user-a", "name": "Regular user A", "role": "user"},
    "user-b-token": {"id": "user-b", "name": "Regular user B", "role": "user"},
    "admin-token": {"id": "admin", "name": "Administrator", "role": "admin"},
}


def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    """Authentication: who is making the request? Missing/invalid token -> 401."""
    headers = {"WWW-Authenticate": "Bearer"}
    if not authorization:
        raise ApiError(401, UNAUTHORIZED,
                       "Authentication required. Send the header 'Authorization: Bearer <token>'.",
                       headers=headers)
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise ApiError(401, UNAUTHORIZED,
                       "Authorization header must use the format 'Bearer <token>'.", headers=headers)
    user = USERS.get(parts[1])
    if user is None:
        raise ApiError(401, UNAUTHORIZED, "The token is invalid or has expired.", headers=headers)
    return user
