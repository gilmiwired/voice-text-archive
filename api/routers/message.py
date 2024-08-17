import logging

from fastapi import APIRouter, HTTPException

from api.models.message import NotionRequest, NotionResponse
from send_message import archive_notion

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/archive", response_model=NotionResponse)
async def notion_archive(request: NotionRequest) -> NotionResponse:
    logger.info(f"Received message: {request.message}")
    try:
        response_message = archive_notion(request.message)
        if "successfully" not in response_message.lower():
            logger.error(f"Error processing message: {response_message}")
            raise HTTPException(status_code=400, detail=response_message)
        logger.info(f"Processed message: {response_message}")
        return NotionResponse(response_message=response_message)
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))
