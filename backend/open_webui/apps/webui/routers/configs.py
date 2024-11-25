from open_webui.config import BannerModel
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from open_webui.utils.utils import get_admin_user, get_verified_user


from open_webui.config import get_config, save_config

router = APIRouter()


############################
# ImportConfig
############################


class ImportConfigForm(BaseModel):
    """
    Represents the form data for importing configuration.

    Attributes:
        config (dict): The configuration data to be imported.
    """
    config: dict


@router.post("/import", response_model=dict)
async def import_config(form_data: ImportConfigForm, user=Depends(get_admin_user)):
    """
    Import configuration data.

    Args:
        form_data (ImportConfigForm): The form data containing the configuration to be imported.
        user: The authenticated admin user.

    Returns:
        dict: The imported configuration data.
    """
    save_config(form_data.config)
    return get_config()


############################
# ExportConfig
############################


@router.get("/export", response_model=dict)
async def export_config(user=Depends(get_admin_user)):
    """
    Export the current configuration data.

    Args:
        user: The authenticated admin user.

    Returns:
        dict: The current configuration data.
    """
    return get_config()


class SetDefaultModelsForm(BaseModel):
    """
    Represents the form data for setting default models.

    Attributes:
        models (str): The default models to be set.
    """
    models: str


class PromptSuggestion(BaseModel):
    """
    Represents a prompt suggestion.

    Attributes:
        title (list[str]): The title of the prompt suggestion.
        content (str): The content of the prompt suggestion.
    """
    title: list[str]
    content: str


class SetDefaultSuggestionsForm(BaseModel):
    """
    Represents the form data for setting default prompt suggestions.

    Attributes:
        suggestions (list[PromptSuggestion]): The list of prompt suggestions to be set.
    """
    suggestions: list[PromptSuggestion]


############################
# SetDefaultModels
############################


@router.post("/default/models", response_model=str)
async def set_global_default_models(
    request: Request, form_data: SetDefaultModelsForm, user=Depends(get_admin_user)
):
    """
    Set the global default models.

    Args:
        request (Request): The request object.
        form_data (SetDefaultModelsForm): The form data containing the default models to be set.
        user: The authenticated admin user.

    Returns:
        str: The set default models.
    """
    request.app.state.config.DEFAULT_MODELS = form_data.models
    return request.app.state.config.DEFAULT_MODELS


@router.post("/default/suggestions", response_model=list[PromptSuggestion])
async def set_global_default_suggestions(
    request: Request,
    form_data: SetDefaultSuggestionsForm,
    user=Depends(get_admin_user),
):
    """
    Set the global default prompt suggestions.

    Args:
        request (Request): The request object.
        form_data (SetDefaultSuggestionsForm): The form data containing the default prompt suggestions to be set.
        user: The authenticated admin user.

    Returns:
        list[PromptSuggestion]: The set default prompt suggestions.
    """
    data = form_data.model_dump()
    request.app.state.config.DEFAULT_PROMPT_SUGGESTIONS = data["suggestions"]
    return request.app.state.config.DEFAULT_PROMPT_SUGGESTIONS


############################
# SetBanners
############################


class SetBannersForm(BaseModel):
    """
    Represents the form data for setting banners.

    Attributes:
        banners (list[BannerModel]): The list of banners to be set.
    """
    banners: list[BannerModel]


@router.post("/banners", response_model=list[BannerModel])
async def set_banners(
    request: Request,
    form_data: SetBannersForm,
    user=Depends(get_admin_user),
):
    """
    Set the banners.

    Args:
        request (Request): The request object.
        form_data (SetBannersForm): The form data containing the banners to be set.
        user: The authenticated admin user.

    Returns:
        list[BannerModel]: The set banners.
    """
    data = form_data.model_dump()
    request.app.state.config.BANNERS = data["banners"]
    return request.app.state.config.BANNERS


@router.get("/banners", response_model=list[BannerModel])
async def get_banners(
    request: Request,
    user=Depends(get_verified_user),
):
    """
    Get the current banners.

    Args:
        request (Request): The request object.
        user: The authenticated verified user.

    Returns:
        list[BannerModel]: The current banners.
    """
    return request.app.state.config.BANNERS
