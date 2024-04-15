from typing import Annotated
from fastapi import APIRouter, Depends,HTTPException, Request
from app.db.core import NotFoundError, get_db
from app.db.user import (
    User,
    UserInDB,
    create_db_user,
    # get_current_active_user
    
)
from sqlalchemy.orm import Session


router = APIRouter(
    prefix="/users",
)


@router.post("/")
def create_user(
    request: Request, user: UserInDB, db: Session = Depends(get_db)
) -> User:
    db_user = create_db_user(user, db)
    return User(**db_user.__dict__)


# @router.get("/me/", response_model=User)
# async def read_users_me(
#     current_user: Annotated[User, Depends(get_current_active_user)],
# ):
#     return current_user


# @router.get("/me/items/")
# async def read_own_items(
#     current_user: Annotated[User, Depends(get_current_active_user)],
# ):
#     return [{"item_id": "Foo", "owner": current_user.username}]
