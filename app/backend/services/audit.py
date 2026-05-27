import json

from sqlalchemy.orm import Session

from .. import models


def log(db: Session, actor: str, verb: str, target: str, diff: dict | list | str | None = None) -> None:
    payload = diff if isinstance(diff, str) else json.dumps(diff or {}, default=str)
    db.add(models.AuditLog(actor=actor, verb=verb, target=target, diff=payload))
    db.commit()
