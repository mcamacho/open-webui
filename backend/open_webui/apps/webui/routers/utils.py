import black
import markdown

from open_webui.apps.webui.models.chats import ChatTitleMessagesForm
from open_webui.config import DATA_DIR, ENABLE_ADMIN_EXPORT
from open_webui.constants import ERROR_MESSAGES
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from starlette.responses import FileResponse
from open_webui.utils.misc import get_gravatar_url
from open_webui.utils.pdf_generator import PDFGenerator
from open_webui.utils.utils import get_admin_user

router = APIRouter()


@router.get("/gravatar")
async def get_gravatar(
    email: str,
):
    """
    Get the Gravatar URL for the given email.

    Args:
        email (str): The email address to get the Gravatar for.

    Returns:
        str: The Gravatar URL.
    """
    return get_gravatar_url(email)


class CodeFormatRequest(BaseModel):
    code: str


@router.post("/code/format")
async def format_code(request: CodeFormatRequest):
    """
    Format the given code using the Black formatter.

    Args:
        request (CodeFormatRequest): The request containing the code to format.

    Returns:
        dict: A dictionary containing the formatted code.
    """
    try:
        formatted_code = black.format_str(request.code, mode=black.Mode())
        return {"code": formatted_code}
    except black.NothingChanged:
        return {"code": request.code}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class MarkdownForm(BaseModel):
    md: str


@router.post("/markdown")
async def get_html_from_markdown(
    form_data: MarkdownForm,
):
    """
    Convert the given Markdown to HTML.

    Args:
        form_data (MarkdownForm): The form data containing the Markdown.

    Returns:
        dict: A dictionary containing the HTML.
    """
    return {"html": markdown.markdown(form_data.md)}


class ChatForm(BaseModel):
    title: str
    messages: list[dict]


@router.post("/pdf")
async def download_chat_as_pdf(
    form_data: ChatTitleMessagesForm,
):
    """
    Generate a PDF from the given chat messages.

    Args:
        form_data (ChatTitleMessagesForm): The form data containing the chat messages.

    Returns:
        Response: A response containing the generated PDF.
    """
    try:
        pdf_bytes = PDFGenerator(form_data).generate_chat_pdf()

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment;filename=chat.pdf"},
        )
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/db/download")
async def download_db(user=Depends(get_admin_user)):
    """
    Download the SQLite database file.

    Args:
        user: The admin user.

    Returns:
        FileResponse: A response containing the database file.
    """
    if not ENABLE_ADMIN_EXPORT:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )
    from open_webui.apps.webui.internal.db import engine

    if engine.name != "sqlite":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DB_NOT_SQLITE,
        )
    return FileResponse(
        engine.url.database,
        media_type="application/octet-stream",
        filename="webui.db",
    )


@router.get("/litellm/config")
async def download_litellm_config_yaml(user=Depends(get_admin_user)):
    """
    Download the LiteLLM configuration YAML file.

    Args:
        user: The admin user.

    Returns:
        FileResponse: A response containing the configuration YAML file.
    """
    return FileResponse(
        f"{DATA_DIR}/litellm/config.yaml",
        media_type="application/octet-stream",
        filename="config.yaml",
    )
