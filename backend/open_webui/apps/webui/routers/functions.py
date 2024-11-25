import os
from pathlib import Path
from typing import Optional

from open_webui.apps.webui.models.functions import (
    FunctionForm,
    FunctionModel,
    FunctionResponse,
    Functions,
)
from open_webui.apps.webui.utils import load_function_module_by_id, replace_imports
from open_webui.config import CACHE_DIR
from open_webui.constants import ERROR_MESSAGES
from fastapi import APIRouter, Depends, HTTPException, Request, status
from open_webui.utils.utils import get_admin_user, get_verified_user

router = APIRouter()

############################
# GetFunctions
############################


@router.get("/", response_model=list[FunctionResponse])
async def get_functions(user=Depends(get_verified_user)):
    """
    Retrieve a list of all functions.

    Args:
        user: The verified user making the request.

    Returns:
        A list of FunctionResponse objects.
    """
    return Functions.get_functions()


############################
# ExportFunctions
############################


@router.get("/export", response_model=list[FunctionModel])
async def get_functions(user=Depends(get_admin_user)):
    """
    Export a list of all functions.

    Args:
        user: The admin user making the request.

    Returns:
        A list of FunctionModel objects.
    """
    return Functions.get_functions()


############################
# CreateNewFunction
############################


@router.post("/create", response_model=Optional[FunctionResponse])
async def create_new_function(
    request: Request, form_data: FunctionForm, user=Depends(get_admin_user)
):
    """
    Create a new function.

    Args:
        request: The HTTP request object.
        form_data: The form data for the new function.
        user: The admin user making the request.

    Returns:
        The created FunctionResponse object, or raises an HTTPException if an error occurs.
    """
    if not form_data.id.isidentifier():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only alphanumeric characters and underscores are allowed in the id",
        )

    form_data.id = form_data.id.lower()

    function = Functions.get_function_by_id(form_data.id)
    if function is None:
        try:
            form_data.content = replace_imports(form_data.content)
            function_module, function_type, frontmatter = load_function_module_by_id(
                form_data.id,
                content=form_data.content,
            )
            form_data.meta.manifest = frontmatter

            FUNCTIONS = request.app.state.FUNCTIONS
            FUNCTIONS[form_data.id] = function_module

            function = Functions.insert_new_function(user.id, function_type, form_data)

            function_cache_dir = Path(CACHE_DIR) / "functions" / form_data.id
            function_cache_dir.mkdir(parents=True, exist_ok=True)

            if function:
                return function
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ERROR_MESSAGES.DEFAULT("Error creating function"),
                )
        except Exception as e:
            print(e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT(e),
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.ID_TAKEN,
        )


############################
# GetFunctionById
############################


@router.get("/id/{id}", response_model=Optional[FunctionModel])
async def get_function_by_id(id: str, user=Depends(get_admin_user)):
    """
    Retrieve a function by its ID.

    Args:
        id: The ID of the function.
        user: The admin user making the request.

    Returns:
        The FunctionModel object, or raises an HTTPException if not found.
    """
    function = Functions.get_function_by_id(id)

    if function:
        return function
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )


############################
# ToggleFunctionById
############################


@router.post("/id/{id}/toggle", response_model=Optional[FunctionModel])
async def toggle_function_by_id(id: str, user=Depends(get_admin_user)):
    """
    Toggle the active status of a function by its ID.

    Args:
        id: The ID of the function.
        user: The admin user making the request.

    Returns:
        The updated FunctionModel object, or raises an HTTPException if an error occurs.
    """
    function = Functions.get_function_by_id(id)
    if function:
        function = Functions.update_function_by_id(
            id, {"is_active": not function.is_active}
        )

        if function:
            return function
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Error updating function"),
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )


############################
# ToggleGlobalById
############################


@router.post("/id/{id}/toggle/global", response_model=Optional[FunctionModel])
async def toggle_global_by_id(id: str, user=Depends(get_admin_user)):
    """
    Toggle the global status of a function by its ID.

    Args:
        id: The ID of the function.
        user: The admin user making the request.

    Returns:
        The updated FunctionModel object, or raises an HTTPException if an error occurs.
    """
    function = Functions.get_function_by_id(id)
    if function:
        function = Functions.update_function_by_id(
            id, {"is_global": not function.is_global}
        )

        if function:
            return function
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Error updating function"),
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )


############################
# UpdateFunctionById
############################


@router.post("/id/{id}/update", response_model=Optional[FunctionModel])
async def update_function_by_id(
    request: Request, id: str, form_data: FunctionForm, user=Depends(get_admin_user)
):
    """
    Update a function by its ID.

    Args:
        request: The HTTP request object.
        id: The ID of the function.
        form_data: The form data for the function.
        user: The admin user making the request.

    Returns:
        The updated FunctionModel object, or raises an HTTPException if an error occurs.
    """
    try:
        form_data.content = replace_imports(form_data.content)
        function_module, function_type, frontmatter = load_function_module_by_id(
            id, content=form_data.content
        )
        form_data.meta.manifest = frontmatter

        FUNCTIONS = request.app.state.FUNCTIONS
        FUNCTIONS[id] = function_module

        updated = {**form_data.model_dump(exclude={"id"}), "type": function_type}
        print(updated)

        function = Functions.update_function_by_id(id, updated)

        if function:
            return function
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Error updating function"),
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )


############################
# DeleteFunctionById
############################


@router.delete("/id/{id}/delete", response_model=bool)
async def delete_function_by_id(
    request: Request, id: str, user=Depends(get_admin_user)
):
    """
    Delete a function by its ID.

    Args:
        request: The HTTP request object.
        id: The ID of the function.
        user: The admin user making the request.

    Returns:
        True if the function was deleted, False otherwise.
    """
    result = Functions.delete_function_by_id(id)

    if result:
        FUNCTIONS = request.app.state.FUNCTIONS
        if id in FUNCTIONS:
            del FUNCTIONS[id]

    return result


############################
# GetFunctionValves
############################


@router.get("/id/{id}/valves", response_model=Optional[dict])
async def get_function_valves_by_id(id: str, user=Depends(get_admin_user)):
    """
    Retrieve the valves of a function by its ID.

    Args:
        id: The ID of the function.
        user: The admin user making the request.

    Returns:
        A dictionary of valves, or raises an HTTPException if an error occurs.
    """
    function = Functions.get_function_by_id(id)
    if function:
        try:
            valves = Functions.get_function_valves_by_id(id)
            return valves
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT(e),
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )


############################
# GetFunctionValvesSpec
############################


@router.get("/id/{id}/valves/spec", response_model=Optional[dict])
async def get_function_valves_spec_by_id(
    request: Request, id: str, user=Depends(get_admin_user)
):
    """
    Retrieve the specification of the valves of a function by its ID.

    Args:
        request: The HTTP request object.
        id: The ID of the function.
        user: The admin user making the request.

    Returns:
        A dictionary of the valves specification, or raises an HTTPException if not found.
    """
    function = Functions.get_function_by_id(id)
    if function:
        if id in request.app.state.FUNCTIONS:
            function_module = request.app.state.FUNCTIONS[id]
        else:
            function_module, function_type, frontmatter = load_function_module_by_id(id)
            request.app.state.FUNCTIONS[id] = function_module

        if hasattr(function_module, "Valves"):
            Valves = function_module.Valves
            return Valves.schema()
        return None
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )


############################
# UpdateFunctionValves
############################


@router.post("/id/{id}/valves/update", response_model=Optional[dict])
async def update_function_valves_by_id(
    request: Request, id: str, form_data: dict, user=Depends(get_admin_user)
):
    """
    Update the valves of a function by its ID.

    Args:
        request: The HTTP request object.
        id: The ID of the function.
        form_data: The form data for the valves.
        user: The admin user making the request.

    Returns:
        A dictionary of the updated valves, or raises an HTTPException if an error occurs.
    """
    function = Functions.get_function_by_id(id)
    if function:
        if id in request.app.state.FUNCTIONS:
            function_module = request.app.state.FUNCTIONS[id]
        else:
            function_module, function_type, frontmatter = load_function_module_by_id(id)
            request.app.state.FUNCTIONS[id] = function_module

        if hasattr(function_module, "Valves"):
            Valves = function_module.Valves

            try:
                form_data = {k: v for k, v in form_data.items() if v is not None}
                valves = Valves(**form_data)
                Functions.update_function_valves_by_id(id, valves.model_dump())
                return valves.model_dump()
            except Exception as e:
                print(e)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ERROR_MESSAGES.DEFAULT(e),
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ERROR_MESSAGES.NOT_FOUND,
            )

    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )


############################
# FunctionUserValves
############################


@router.get("/id/{id}/valves/user", response_model=Optional[dict])
async def get_function_user_valves_by_id(id: str, user=Depends(get_verified_user)):
    """
    Retrieve the user-specific valves of a function by its ID.

    Args:
        id: The ID of the function.
        user: The verified user making the request.

    Returns:
        A dictionary of user-specific valves, or raises an HTTPException if an error occurs.
    """
    function = Functions.get_function_by_id(id)
    if function:
        try:
            user_valves = Functions.get_user_valves_by_id_and_user_id(id, user.id)
            return user_valves
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT(e),
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )


@router.get("/id/{id}/valves/user/spec", response_model=Optional[dict])
async def get_function_user_valves_spec_by_id(
    request: Request, id: str, user=Depends(get_verified_user)
):
    """
    Retrieve the specification of the user-specific valves of a function by its ID.

    Args:
        request: The HTTP request object.
        id: The ID of the function.
        user: The verified user making the request.

    Returns:
        A dictionary of the user-specific valves specification, or raises an HTTPException if not found.
    """
    function = Functions.get_function_by_id(id)
    if function:
        if id in request.app.state.FUNCTIONS:
            function_module = request.app.state.FUNCTIONS[id]
        else:
            function_module, function_type, frontmatter = load_function_module_by_id(id)
            request.app.state.FUNCTIONS[id] = function_module

        if hasattr(function_module, "UserValves"):
            UserValves = function_module.UserValves
            return UserValves.schema()
        return None
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )


@router.post("/id/{id}/valves/user/update", response_model=Optional[dict])
async def update_function_user_valves_by_id(
    request: Request, id: str, form_data: dict, user=Depends(get_verified_user)
):
    """
    Update the user-specific valves of a function by its ID.

    Args:
        request: The HTTP request object.
        id: The ID of the function.
        form_data: The form data for the user-specific valves.
        user: The verified user making the request.

    Returns:
        A dictionary of the updated user-specific valves, or raises an HTTPException if an error occurs.
    """
    function = Functions.get_function_by_id(id)

    if function:
        if id in request.app.state.FUNCTIONS:
            function_module = request.app.state.FUNCTIONS[id]
        else:
            function_module, function_type, frontmatter = load_function_module_by_id(id)
            request.app.state.FUNCTIONS[id] = function_module

        if hasattr(function_module, "UserValves"):
            UserValves = function_module.UserValves

            try:
                form_data = {k: v for k, v in form_data.items() if v is not None}
                user_valves = UserValves(**form_data)
                Functions.update_user_valves_by_id_and_user_id(
                    id, user.id, user_valves.model_dump()
                )
                return user_valves.model_dump()
            except Exception as e:
                print(e)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ERROR_MESSAGES.DEFAULT(e),
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ERROR_MESSAGES.NOT_FOUND,
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )
