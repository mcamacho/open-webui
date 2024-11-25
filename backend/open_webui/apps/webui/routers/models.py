from typing import Optional

from open_webui.apps.webui.models.models import (
    ModelForm,
    ModelModel,
    ModelResponse,
    ModelUserResponse,
    Models,
)
from open_webui.constants import ERROR_MESSAGES
from fastapi import APIRouter, Depends, HTTPException, Request, status


from open_webui.utils.utils import get_admin_user, get_verified_user
from open_webui.utils.access_control import has_access, has_permission


router = APIRouter()


###########################
# GetModels
###########################


@router.get("/", response_model=list[ModelUserResponse])
async def get_models(id: Optional[str] = None, user=Depends(get_verified_user)):
    """
    Retrieve a list of models accessible to the user.

    Args:
        id (Optional[str]): Optional model ID to filter by.
        user: The current authenticated user.

    Returns:
        list[ModelUserResponse]: List of models accessible to the user.
    """
    if user.role == "admin":
        return Models.get_models()
    else:
        return Models.get_models_by_user_id(user.id)


###########################
# GetBaseModels
###########################


@router.get("/base", response_model=list[ModelResponse])
async def get_base_models(user=Depends(get_admin_user)):
    """
    Retrieve a list of base models.

    Args:
        user: The current authenticated admin user.

    Returns:
        list[ModelResponse]: List of base models.
    """
    return Models.get_base_models()


############################
# CreateNewModel
############################


@router.post("/create", response_model=Optional[ModelModel])
async def create_new_model(
    request: Request,
    form_data: ModelForm,
    user=Depends(get_verified_user),
):
    """
    Create a new model.

    Args:
        request: The HTTP request object.
        form_data (ModelForm): The form data for the new model.
        user: The current authenticated user.

    Returns:
        Optional[ModelModel]: The created model, or None if creation failed.

    Raises:
        HTTPException: If the user is not authorized or the model ID is already taken.
    """
    if user.role != "admin" and not has_permission(
        user.id, "workspace.models", request.app.state.config.USER_PERMISSIONS
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )

    model = Models.get_model_by_id(form_data.id)
    if model:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.MODEL_ID_TAKEN,
        )

    else:
        model = Models.insert_new_model(form_data, user.id)
        if model:
            return model
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ERROR_MESSAGES.DEFAULT(),
            )


###########################
# GetModelById
###########################


# Note: We're not using the typical url path param here, but instead using a query parameter to allow '/' in the id
@router.get("/model", response_model=Optional[ModelResponse])
async def get_model_by_id(id: str, user=Depends(get_verified_user)):
    """
    Retrieve a model by its ID.

    Args:
        id (str): The ID of the model.
        user: The current authenticated user.

    Returns:
        Optional[ModelResponse]: The model, or None if not found.

    Raises:
        HTTPException: If the model is not found or the user is not authorized to access it.
    """
    model = Models.get_model_by_id(id)
    if model:
        if (
            user.role == "admin"
            or model.user_id == user.id
            or has_access(user.id, "read", model.access_control)
        ):
            return model
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )


############################
# ToggelModelById
############################


@router.post("/model/toggle", response_model=Optional[ModelResponse])
async def toggle_model_by_id(id: str, user=Depends(get_verified_user)):
    """
    Toggle the active status of a model by its ID.

    Args:
        id (str): The ID of the model.
        user: The current authenticated user.

    Returns:
        Optional[ModelResponse]: The updated model, or None if not found.

    Raises:
        HTTPException: If the model is not found, the user is not authorized, or there is an error updating the model.
    """
    model = Models.get_model_by_id(id)
    if model:
        if (
            user.role == "admin"
            or model.user_id == user.id
            or has_access(user.id, "write", model.access_control)
        ):
            model = Models.toggle_model_by_id(id)

            if model:
                return model
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ERROR_MESSAGES.DEFAULT("Error updating function"),
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ERROR_MESSAGES.UNAUTHORIZED,
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )


############################
# UpdateModelById
############################


@router.post("/model/update", response_model=Optional[ModelModel])
async def update_model_by_id(
    id: str,
    form_data: ModelForm,
    user=Depends(get_verified_user),
):
    """
    Update a model by its ID.

    Args:
        id (str): The ID of the model.
        form_data (ModelForm): The updated form data for the model.
        user: The current authenticated user.

    Returns:
        Optional[ModelModel]: The updated model, or None if not found.

    Raises:
        HTTPException: If the model is not found.
    """
    model = Models.get_model_by_id(id)

    if not model:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    model = Models.update_model_by_id(id, form_data)
    return model


############################
# DeleteModelById
############################


@router.delete("/model/delete", response_model=bool)
async def delete_model_by_id(id: str, user=Depends(get_verified_user)):
    """
    Delete a model by its ID.

    Args:
        id (str): The ID of the model.
        user: The current authenticated user.

    Returns:
        bool: True if the model was successfully deleted, False otherwise.

    Raises:
        HTTPException: If the model is not found or the user is not authorized to delete it.
    """
    model = Models.get_model_by_id(id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    if model.user_id != user.id and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )

    result = Models.delete_model_by_id(id)
    return result


@router.delete("/delete/all", response_model=bool)
async def delete_all_models(user=Depends(get_admin_user)):
    """
    Delete all models.

    Args:
        user: The current authenticated admin user.

    Returns:
        bool: True if all models were successfully deleted, False otherwise.
    """
    result = Models.delete_all_models()
    return result
