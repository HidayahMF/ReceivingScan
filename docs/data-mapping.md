# Data Mapping Status

The internal Pydantic contract is in `backend/app/schemas.py`. All unknown fields are nullable and document quantity is separate from actual quantity. SQL Server migration design is intentionally not included yet because target schema and DBA approval are unknown. MySQL PO mapping remains blocked until metadata-only inspection identifies tables, columns, units, status logic, and receipt semantics.
