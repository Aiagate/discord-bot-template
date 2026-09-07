from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from flow_res import is_err
from pydantic import BaseModel

from app.application.mediator import ApplicationMediator
from app.presentation.api.dependencies import get_mediator
from app.presentation.api.error_mapping import http_status_for_error
from app.usecases.users.create_user import CreateUserCommand
from app.usecases.users.get_user import GetUserQuery

router = APIRouter(prefix="/users", tags=["users"])


class CreateUserRequest(BaseModel):
    display_name: str
    email: str


class CreateUserResponse(BaseModel):
    id: str


class UserResponse(BaseModel):
    id: str
    display_name: str
    email: str


@router.post("", response_model=CreateUserResponse)
async def create_user(
    request: CreateUserRequest,
    mediator: Annotated[ApplicationMediator, Depends(get_mediator)],
) -> CreateUserResponse:
    """Create a new user."""
    command = CreateUserCommand(display_name=request.display_name, email=request.email)

    result = await mediator.send_async(command)

    if is_err(result):
        raise HTTPException(
            status_code=http_status_for_error(result.error.type),
            detail=result.error.display_message,
        )

    user_id = result.unwrap().id
    return CreateUserResponse(id=user_id)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    mediator: Annotated[ApplicationMediator, Depends(get_mediator)],
) -> UserResponse:
    """Get a user by ID."""
    query = GetUserQuery(user_id=user_id)
    result = await mediator.send_async(query)

    if is_err(result):
        raise HTTPException(
            status_code=http_status_for_error(result.error.type),
            detail=result.error.display_message,
        )

    user_result = result.unwrap()

    return UserResponse(
        id=user_result.id,
        display_name=user_result.display_name,
        email=user_result.email,
    )
