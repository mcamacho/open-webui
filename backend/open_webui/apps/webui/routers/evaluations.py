from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel

from open_webui.apps.webui.models.users import Users, UserModel
from open_webui.apps.webui.models.feedbacks import (
    FeedbackModel,
    FeedbackResponse,
    FeedbackForm,
    Feedbacks,
)

from open_webui.constants import ERROR_MESSAGES
from open_webui.utils.utils import get_admin_user, get_verified_user

router = APIRouter()


############################
# GetConfig
############################


@router.get("/config")
async def get_config(request: Request, user=Depends(get_admin_user)):
    """
    Get the evaluation configuration.

    Args:
        request (Request): The HTTP request object.
        user: The authenticated admin user.

    Returns:
        dict: The evaluation configuration.
    """
    return {
        "ENABLE_EVALUATION_ARENA_MODELS": request.app.state.config.ENABLE_EVALUATION_ARENA_MODELS,
        "EVALUATION_ARENA_MODELS": request.app.state.config.EVALUATION_ARENA_MODELS,
    }


############################
# UpdateConfig
############################


class UpdateConfigForm(BaseModel):
    """
    Form for updating the evaluation configuration.

    Attributes:
        ENABLE_EVALUATION_ARENA_MODELS (Optional[bool]): Whether to enable evaluation arena models.
        EVALUATION_ARENA_MODELS (Optional[list[dict]]): The list of evaluation arena models.
    """
    ENABLE_EVALUATION_ARENA_MODELS: Optional[bool] = None
    EVALUATION_ARENA_MODELS: Optional[list[dict]] = None


@router.post("/config")
async def update_config(
    request: Request,
    form_data: UpdateConfigForm,
    user=Depends(get_admin_user),
):
    """
    Update the evaluation configuration.

    Args:
        request (Request): The HTTP request object.
        form_data (UpdateConfigForm): The form data containing the updated configuration.
        user: The authenticated admin user.

    Returns:
        dict: The updated evaluation configuration.
    """
    config = request.app.state.config
    if form_data.ENABLE_EVALUATION_ARENA_MODELS is not None:
        config.ENABLE_EVALUATION_ARENA_MODELS = form_data.ENABLE_EVALUATION_ARENA_MODELS
    if form_data.EVALUATION_ARENA_MODELS is not None:
        config.EVALUATION_ARENA_MODELS = form_data.EVALUATION_ARENA_MODELS
    return {
        "ENABLE_EVALUATION_ARENA_MODELS": config.ENABLE_EVALUATION_ARENA_MODELS,
        "EVALUATION_ARENA_MODELS": config.EVALUATION_ARENA_MODELS,
    }


class FeedbackUserResponse(FeedbackResponse):
    """
    Response model for feedback with user information.

    Attributes:
        user (Optional[UserModel]): The user information.
    """
    user: Optional[UserModel] = None


@router.get("/feedbacks/all", response_model=list[FeedbackUserResponse])
async def get_all_feedbacks(user=Depends(get_admin_user)):
    """
    Get all feedbacks with user information.

    Args:
        user: The authenticated admin user.

    Returns:
        list[FeedbackUserResponse]: The list of feedbacks with user information.
    """
    feedbacks = Feedbacks.get_all_feedbacks()
    return [
        FeedbackUserResponse(
            **feedback.model_dump(), user=Users.get_user_by_id(feedback.user_id)
        )
        for feedback in feedbacks
    ]


@router.delete("/feedbacks/all")
async def delete_all_feedbacks(user=Depends(get_admin_user)):
    """
    Delete all feedbacks.

    Args:
        user: The authenticated admin user.

    Returns:
        bool: True if the feedbacks were successfully deleted, False otherwise.
    """
    success = Feedbacks.delete_all_feedbacks()
    return success


@router.get("/feedbacks/all/export", response_model=list[FeedbackModel])
async def get_all_feedbacks(user=Depends(get_admin_user)):
    """
    Export all feedbacks.

    Args:
        user: The authenticated admin user.

    Returns:
        list[FeedbackModel]: The list of all feedbacks.
    """
    feedbacks = Feedbacks.get_all_feedbacks()
    return [
        FeedbackModel(
            **feedback.model_dump(), user=Users.get_user_by_id(feedback.user_id)
        )
        for feedback in feedbacks
    ]


@router.get("/feedbacks/user", response_model=list[FeedbackUserResponse])
async def get_feedbacks(user=Depends(get_verified_user)):
    """
    Get feedbacks for the authenticated user.

    Args:
        user: The authenticated user.

    Returns:
        list[FeedbackUserResponse]: The list of feedbacks for the authenticated user.
    """
    feedbacks = Feedbacks.get_feedbacks_by_user_id(user.id)
    return feedbacks


@router.delete("/feedbacks", response_model=bool)
async def delete_feedbacks(user=Depends(get_verified_user)):
    """
    Delete feedbacks for the authenticated user.

    Args:
        user: The authenticated user.

    Returns:
        bool: True if the feedbacks were successfully deleted, False otherwise.
    """
    success = Feedbacks.delete_feedbacks_by_user_id(user.id)
    return success


@router.post("/feedback", response_model=FeedbackModel)
async def create_feedback(
    request: Request,
    form_data: FeedbackForm,
    user=Depends(get_verified_user),
):
    """
    Create a new feedback.

    Args:
        request (Request): The HTTP request object.
        form_data (FeedbackForm): The form data containing the feedback details.
        user: The authenticated user.

    Returns:
        FeedbackModel: The created feedback.
    """
    feedback = Feedbacks.insert_new_feedback(user_id=user.id, form_data=form_data)
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(),
        )

    return feedback


@router.get("/feedback/{id}", response_model=FeedbackModel)
async def get_feedback_by_id(id: str, user=Depends(get_verified_user)):
    """
    Get feedback by ID.

    Args:
        id (str): The ID of the feedback.
        user: The authenticated user.

    Returns:
        FeedbackModel: The feedback with the specified ID.
    """
    feedback = Feedbacks.get_feedback_by_id_and_user_id(id=id, user_id=user.id)

    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=ERROR_MESSAGES.NOT_FOUND
        )

    return feedback


@router.post("/feedback/{id}", response_model=FeedbackModel)
async def update_feedback_by_id(
    id: str, form_data: FeedbackForm, user=Depends(get_verified_user)
):
    """
    Update feedback by ID.

    Args:
        id (str): The ID of the feedback.
        form_data (FeedbackForm): The form data containing the updated feedback details.
        user: The authenticated user.

    Returns:
        FeedbackModel: The updated feedback.
    """
    feedback = Feedbacks.update_feedback_by_id_and_user_id(
        id=id, user_id=user.id, form_data=form_data
    )

    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=ERROR_MESSAGES.NOT_FOUND
        )

    return feedback


@router.delete("/feedback/{id}")
async def delete_feedback_by_id(id: str, user=Depends(get_verified_user)):
    """
    Delete feedback by ID.

    Args:
        id (str): The ID of the feedback.
        user: The authenticated user.

    Returns:
        bool: True if the feedback was successfully deleted, False otherwise.
    """
    if user.role == "admin":
        success = Feedbacks.delete_feedback_by_id(id=id)
    else:
        success = Feedbacks.delete_feedback_by_id_and_user_id(id=id, user_id=user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=ERROR_MESSAGES.NOT_FOUND
        )

    return success
