"""Webhook endpoints for AdRev event ingestion into Solarware user wallets."""
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from ..core import get_db, logger
from ..services.user_wallet_service import UserWalletService

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


def _coerce_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _coerce_int(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value.strip()))
        except Exception:
            return default
    return default


def _extract_event_type(
    payload: Dict[str, Any],
    header_event_type: Optional[str],
) -> str:
    return (
        (header_event_type or "").strip()
        or str(payload.get("event") or "").strip()
        or "adrev_event"
    )


@router.post("/adrev")
async def receive_adrev_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_adrev_event_type: Optional[str] = Header(default=None),
    x_adrev_delivery_id: Optional[str] = Header(default=None),
):
    """Receive AdRev webhook callbacks and append wallet events when userRef is present."""
    try:
        raw = await request.json()
    except Exception:
        raw = {}

    payload = _coerce_dict(raw)
    data = _coerce_dict(payload.get("data"))
    metadata = _coerce_dict(data.get("metadata"))

    event_type = _extract_event_type(payload, x_adrev_event_type)

    # Dedicated onboarding/test webhook checks from AdRev.
    if event_type in {
        "verification",
        "ad_started",
        "ad_completed",
        "ad_failed",
        "campaign_started",
        "campaign_completed",
        "reward_approved",
    }:
        return {
            "ok": True,
            "processed": False,
            "event_type": event_type,
            "message": "Verification/test event acknowledged.",
        }

    user_id = str(data.get("userRef") or payload.get("userRef") or "").strip()
    external_event_id = (
        str(data.get("idempotencyKey") or "").strip()
        or (x_adrev_delivery_id or "").strip()
        or None
    )

    if not user_id:
        logger.info(
            "adrev_webhook_ack_no_user_ref event_type=%s delivery_id=%s",
            event_type,
            x_adrev_delivery_id,
        )
        return {
            "ok": True,
            "processed": False,
            "event_type": event_type,
            "message": "No userRef provided; event acknowledged without wallet mutation.",
        }

    points_delta = 0
    if event_type in {"reward_approved", "ad_event.reward", "ad_event.complete"}:
        points_delta = max(
            0,
            _coerce_int(metadata.get("points_delta"), 0)
            or _coerce_int(metadata.get("reward_points"), 0)
            or _coerce_int(metadata.get("rewardMinor"), 0),
        )

    normalized_event_type = f"adrev.{event_type.replace(' ', '_').lower()}"
    event_payload = {
        "received_at": datetime.utcnow().isoformat() + "Z",
        "headers": {
            "x_adrev_event_type": x_adrev_event_type,
            "x_adrev_delivery_id": x_adrev_delivery_id,
        },
        "payload": payload,
    }

    try:
        event, wallet, created = UserWalletService.append_event(
            db=db,
            user_id=user_id,
            event_type=normalized_event_type,
            points_delta=points_delta,
            external_event_id=external_event_id,
            payload=event_payload,
        )

        return {
            "ok": True,
            "processed": True,
            "created": bool(created),
            "event_id": event.id,
            "event_type": normalized_event_type,
            "user_id": user_id,
            "points_delta": points_delta,
            "balance_after": wallet.points_balance,
        }
    except LookupError:
        return {
            "ok": True,
            "processed": False,
            "event_type": normalized_event_type,
            "message": f"User '{user_id}' not found; webhook acknowledged.",
        }
