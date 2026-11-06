from pathlib import Path

from .celery_app import celery_app
from ..config import get_settings
from ..processing import process_document

@celery_app.task(bind=True, autoretry_for=(OSError,), retry_backoff=True, max_retries=2)
def process_document_task(self, source_path: str) -> dict:
    """Async boundary for M3; persistence/status ownership still belongs to SQL Server."""
    result = process_document(Path(source_path), get_settings())
    return result.model_dump(mode="json")
