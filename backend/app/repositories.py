from dataclasses import dataclass
from typing import Protocol
from .config import Settings

@dataclass(frozen=True)
class PurchaseOrder:
    po_number: str
    supplier_name: str | None = None
    status: str | None = None

class PurchaseOrderRepository(Protocol):
    def find_by_number(self, po_number: str) -> PurchaseOrder | None: ...

class MockPurchaseOrderRepository:
    def find_by_number(self, po_number: str) -> PurchaseOrder | None:
        return None

class ReadOnlyMySQLPurchaseOrderRepository:
    """Placeholder until legacy schema is inspected; intentionally performs no writes."""
    def __init__(self, settings: Settings):
        self.settings = settings

    def find_by_number(self, po_number: str) -> PurchaseOrder | None:
        raise NotImplementedError("Legacy MySQL schema must be inspected before enabling this adapter")

class SQLServerRepository:
    """Application persistence boundary; migrations require explicit DBA approval."""
    def __init__(self, settings: Settings):
        self.settings = settings
