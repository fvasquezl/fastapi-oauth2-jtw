from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from app.core.config import settings
from sqlalchemy.orm import Session
from app.db.core import DBUser, NotFoundError
from typing import Optional

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

# fake_users_db = {
#     "johndoe": {
#         "username": "johndoe",
#         "full_name": "John Doe",
#         "email": "johndoe@example.com",
#         "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
#         "disabled": False,
#     }
# }


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserInDB(User):
    hashed_password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(username: str,session:Session)->DBUser:
    db_user = session.query(DBUser).filter(DBUser.username == username).first()

    if db_user in None:
        raise NotFoundError(f"user with id {username} not found.")
    return UserInDB(**db_user)


'''
Temp
'''
def create_db_user(user: UserInDB, session: Session) -> DBUser:
    db_user = DBUser(**user.model_dump(exclude_none=True))
    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user



def authenticate_user(username: str, password: str,session:Session)->DBUser:
    db_user = session.query(DBUser).filter(DBUser.username == username).first()
    if not db_user:
        return False
    if not verify_password(password, db_user.hashed_password):
        return False
    return db_user


def create_access_token(data: dict,expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)],session:Session)->DBUser:
    db_user = session.query(DBUser).filter(DBUser.username == username).first()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(db_user, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],session:Session
)->DBUser:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
