import logging
from typing import Optional

from open_webui.apps.webui.models.auths import Auths
from open_webui.apps.webui.models.chats import Chats
from open_webui.apps.webui.models.users import (
    UserModel,
    UserRoleUpdateForm,
    Users,
    UserSettings,
    UserUpdateForm,
)
from open_webui.constants import ERROR_MESSAGES
from open_webui.env import SRC_LOG_LEVELS
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from open_webui.utils.utils import get_admin_user, get_password_hash, get_verified_user

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])

router = APIRouter()

############################
# GetUsers
############################


@router.get("/", response_model=list[UserModel])
async def get_users(skip: int = 0, limit: int = 50, user=Depends(get_admin_user)):
    """
    Retrieve a list of users.

    Args:
        skip (int): The number of users to skip.
        limit (int): The maximum number of users to return.
        user: The authenticated admin user.

    Returns:
        list[UserModel]: A list of user models.
    """
    return Users.get_users(skip, limit)


############################
# User Groups
############################


@router.get("/groups")
async def get_user_groups(user=Depends(get_verified_user)):
    """
    Retrieve the groups of the authenticated user.

    Args:
        user: The authenticated user.

    Returns:
        list: A list of user groups.
    """
    return Users.get_user_groups(user.id)


############################
# User Permissions
############################


@router.get("/permissions")
async def get_user_permissisions(user=Depends(get_verified_user)):
    """
    Retrieve the permissions of the authenticated user.

    Args:
        user: The authenticated user.

    Returns:
        list: A list of user permissions.
    """
    return Users.get_user_groups(user.id)


############################
# User Default Permissions
############################
class WorkspacePermissions(BaseModel):
    """
    Represents the workspace permissions for a user.

    Attributes:
        models (bool): Permission to access models.
        knowledge (bool): Permission to access knowledge.
        prompts (bool): Permission to access prompts.
        tools (bool): Permission to access tools.
    """
    models: bool
    knowledge: bool
    prompts: bool
    tools: bool


class ChatPermissions(BaseModel):
    """
    Represents the chat permissions for a user.

    Attributes:
        file_upload (bool): Permission to upload files.
        delete (bool): Permission to delete messages.
        edit (bool): Permission to edit messages.
        temporary (bool): Permission to create temporary messages.
    """
    file_upload: bool
    delete: bool
    edit: bool
    temporary: bool


class UserPermissions(BaseModel):
    """
    Represents the permissions for a user.

    Attributes:
        workspace (WorkspacePermissions): The workspace permissions.
        chat (ChatPermissions): The chat permissions.
    """
    workspace: WorkspacePermissions
    chat: ChatPermissions


@router.get("/default/permissions")
async def get_user_permissions(request: Request, user=Depends(get_admin_user)):
    """
    Retrieve the default user permissions.

    Args:
        request (Request): The request object.
        user: The authenticated admin user.

    Returns:
        dict: The default user permissions.
    """
    return request.app.state.config.USER_PERMISSIONS


@router.post("/default/permissions")
async def update_user_permissions(
    request: Request, form_data: UserPermissions, user=Depends(get_admin_user)
):
    """
    Update the default user permissions.

    Args:
        request (Request): The request object.
        form_data (UserPermissions): The form data containing the updated permissions.
        user: The authenticated admin user.

    Returns:
        dict: The updated user permissions.
    """
    request.app.state.config.USER_PERMISSIONS = form_data.model_dump()
    return request.app.state.config.USER_PERMISSIONS


############################
# UpdateUserRole
############################


@router.post("/update/role", response_model=Optional[UserModel])
async def update_user_role(form_data: UserRoleUpdateForm, user=Depends(get_admin_user)):
    """
    Update the role of a user.

    Args:
        form_data (UserRoleUpdateForm): The form data containing the user ID and new role.
        user: The authenticated admin user.

    Returns:
        Optional[UserModel]: The updated user model, or None if the update was not successful.
    """
    if user.id != form_data.id and form_data.id != Users.get_first_user().id:
        return Users.update_user_role_by_id(form_data.id, form_data.role)

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=ERROR_MESSAGES.ACTION_PROHIBITED,
    )


############################
# GetUserSettingsBySessionUser
############################


@router.get("/user/settings", response_model=Optional[UserSettings])
async def get_user_settings_by_session_user(user=Depends(get_verified_user)):
    """
    Retrieve the settings of the authenticated user.

    Args:
        user: The authenticated user.

    Returns:
        Optional[UserSettings]: The user settings, or None if the user was not found.
    """
    user = Users.get_user_by_id(user.id)
    if user:
        return user.settings
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.USER_NOT_FOUND,
        )


############################
# UpdateUserSettingsBySessionUser
############################


@router.post("/user/settings/update", response_model=UserSettings)
async def update_user_settings_by_session_user(
    form_data: UserSettings, user=Depends(get_verified_user)
):
    """
    Update the settings of the authenticated user.

    Args:
        form_data (UserSettings): The form data containing the updated settings.
        user: The authenticated user.

    Returns:
        UserSettings: The updated user settings.
    """
    user = Users.update_user_by_id(user.id, {"settings": form_data.model_dump()})
    if user:
        return user.settings
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.USER_NOT_FOUND,
        )


############################
# GetUserInfoBySessionUser
############################


@router.get("/user/info", response_model=Optional[dict])
async def get_user_info_by_session_user(user=Depends(get_verified_user)):
    """
    Retrieve the information of the authenticated user.

    Args:
        user: The authenticated user.

    Returns:
        Optional[dict]: The user information, or None if the user was not found.
    """
    user = Users.get_user_by_id(user.id)
    if user:
        return user.info
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.USER_NOT_FOUND,
        )


############################
# UpdateUserInfoBySessionUser
############################


@router.post("/user/info/update", response_model=Optional[dict])
async def update_user_info_by_session_user(
    form_data: dict, user=Depends(get_verified_user)
):
    """
    Update the information of the authenticated user.

    Args:
        form_data (dict): The form data containing the updated information.
        user: The authenticated user.

    Returns:
        Optional[dict]: The updated user information, or None if the update was not successful.
    """
    user = Users.get_user_by_id(user.id)
    if user:
        if user.info is None:
            user.info = {}

        user = Users.update_user_by_id(user.id, {"info": {**user.info, **form_data}})
        if user:
            return user.info
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.USER_NOT_FOUND,
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.USER_NOT_FOUND,
        )


############################
# GetUserById
############################


class UserResponse(BaseModel):
    """
    Represents the response for a user.

    Attributes:
        name (str): The name of the user.
        profile_image_url (str): The URL of the user's profile image.
    """
    name: str
    profile_image_url: str


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: str, user=Depends(get_verified_user)):
    """
    Retrieve a user by their ID.

    Args:
        user_id (str): The ID of the user to retrieve.
        user: The authenticated user.

    Returns:
        UserResponse: The user response containing the user's name and profile image URL.
    """
    # Check if user_id is a shared chat
    # If it is, get the user_id from the chat
    if user_id.startswith("shared-"):
        chat_id = user_id.replace("shared-", "")
        chat = Chats.get_chat_by_id(chat_id)
        if chat:
            user_id = chat.user_id
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.USER_NOT_FOUND,
            )

    user = Users.get_user_by_id(user_id)

    if user:
        return UserResponse(name=user.name, profile_image_url=user.profile_image_url)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.USER_NOT_FOUND,
        )


############################
# UpdateUserById
############################


@router.post("/{user_id}/update", response_model=Optional[UserModel])
async def update_user_by_id(
    user_id: str,
    form_data: UserUpdateForm,
    session_user=Depends(get_admin_user),
):
    """
    Update a user by their ID.

    Args:
        user_id (str): The ID of the user to update.
        form_data (UserUpdateForm): The form data containing the updated user information.
        session_user: The authenticated admin user.

    Returns:
        Optional[UserModel]: The updated user model, or None if the update was not successful.
    """
    user = Users.get_user_by_id(user_id)

    if user:
        if form_data.email.lower() != user.email:
            email_user = Users.get_user_by_email(form_data.email.lower())
            if email_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ERROR_MESSAGES.EMAIL_TAKEN,
                )

        if form_data.password:
            hashed = get_password_hash(form_data.password)
            log.debug(f"hashed: {hashed}")
            Auths.update_user_password_by_id(user_id, hashed)

        Auths.update_email_by_id(user_id, form_data.email.lower())
        updated_user = Users.update_user_by_id(
            user_id,
            {
                "name": form_data.name,
                "email": form_data.email.lower(),
                "profile_image_url": form_data.profile_image_url,
            },
        )

        if updated_user:
            return updated_user

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(),
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=ERROR_MESSAGES.USER_NOT_FOUND,
    )


############################
# DeleteUserById
############################


@router.delete("/{user_id}", response_model=bool)
async def delete_user_by_id(user_id: str, user=Depends(get_admin_user)):
    """
    Delete a user by their ID.

    Args:
        user_id (str): The ID of the user to delete.
        user: The authenticated admin user.

    Returns:
        bool: True if the user was successfully deleted, False otherwise.
    """
    if user.id != user_id:
        result = Auths.delete_auth_by_id(user_id)

        if result:
            return True

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_MESSAGES.DELETE_USER_ERROR,
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=ERROR_MESSAGES.ACTION_PROHIBITED,
    )
