import logging

from fastapi import APIRouter

from api.models.message import NotionRequest, NotionResponse
from send_message import archive_notion

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/archive", response_model=NotionResponse)
async def notion_archive(request: NotionRequest):
    logger.info(f"Received message: {request.message}")
    try:
        response_message = archive_notion(request.message)
        logger.info(f"Processed message: {response_message}")
        return NotionResponse(response_message=response_message)
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise
