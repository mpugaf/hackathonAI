import logging
import uuid

from sqlalchemy.orm import Session

from models.audit_log import AuditLog

logger = logging.getLogger(__name__)


def log_action(
    db: Session,
    user_id: uuid.UUID | None,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID,
    metadata: dict | None = None,
    ip_address: str | None = None,
) -> None:
    try:
        db.add(
            AuditLog(
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                metadata_=metadata,
                ip_address=ip_address,
            )
        )
        db.commit()
    except Exception as exc:  # pragma: no cover - audit must not break business flows.
        db.rollback()
        logger.warning("audit_log_failed action=%s entity=%s error=%s", action, entity_id, exc)
