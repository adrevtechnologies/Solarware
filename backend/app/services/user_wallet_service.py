"""User account, wallet, and reward-event operations."""
from datetime import datetime
from typing import Optional, Dict, Any, Tuple, List
import logging
import random

from sqlalchemy.orm import Session

from ..models import UserAccount, UserWallet, UserRewardEvent

logger = logging.getLogger(__name__)


class UserWalletService:
    """Transactional operations for user identity, wallet, and event history."""

    @staticmethod
    def get_user(db: Session, user_id: str) -> Optional[UserAccount]:
        return db.query(UserAccount).filter(UserAccount.user_id == user_id).first()

    @staticmethod
    def get_wallet(db: Session, user_id: str) -> Optional[UserWallet]:
        return db.query(UserWallet).filter(UserWallet.user_id == user_id).first()

    @staticmethod
    def _generate_user_id(db: Session, prefix: str = "SW") -> str:
        """Generate a unique user_id like SW123456."""
        for _ in range(30):
            candidate = f"{prefix}{random.randint(100000, 999999)}"
            if not UserWalletService.get_user(db, candidate):
                return candidate
        raise RuntimeError("Unable to generate unique user ID")

    @staticmethod
    def create_user_with_wallet(db: Session, user_id: str) -> Tuple[UserAccount, UserWallet]:
        existing = UserWalletService.get_user(db, user_id)
        if existing:
            raise ValueError("User already exists")

        account = UserAccount(user_id=user_id)
        db.add(account)
        db.flush()

        wallet = UserWallet(account_id=account.id, user_id=user_id, points_balance=0)
        db.add(wallet)

        db.commit()
        db.refresh(account)
        db.refresh(wallet)
        return account, wallet

    @staticmethod
    def signup_user(db: Session, desired_user_id: Optional[str] = None) -> Tuple[UserAccount, UserWallet]:
        """Create a user account for website signup, with optional desired user_id."""
        user_id = (desired_user_id or "").strip()
        if not user_id:
            user_id = UserWalletService._generate_user_id(db)
        return UserWalletService.create_user_with_wallet(db, user_id)

    @staticmethod
    def append_event(
        db: Session,
        user_id: str,
        event_type: str,
        points_delta: int,
        external_event_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Tuple[UserRewardEvent, UserWallet, bool]:
        account = UserWalletService.get_user(db, user_id)
        if not account:
            raise LookupError("User not found")

        wallet = UserWalletService.get_wallet(db, user_id)
        if not wallet:
            raise LookupError("Wallet not found")

        if external_event_id:
            duplicate = (
                db.query(UserRewardEvent)
                .filter(UserRewardEvent.external_event_id == external_event_id)
                .first()
            )
            if duplicate:
                return duplicate, wallet, False

        balance_after = wallet.points_balance + points_delta
        wallet.points_balance = balance_after
        wallet.updated_at = datetime.utcnow()

        event = UserRewardEvent(
            account_id=account.id,
            user_id=user_id,
            event_type=event_type,
            points_delta=points_delta,
            balance_after=balance_after,
            external_event_id=external_event_id,
            payload=payload,
        )

        db.add(event)
        db.commit()
        db.refresh(wallet)
        db.refresh(event)

        logger.info(
            "wallet_event_recorded user_id=%s event_type=%s points_delta=%s balance_after=%s",
            user_id,
            event_type,
            points_delta,
            balance_after,
        )
        return event, wallet, True

    @staticmethod
    def list_events(db: Session, user_id: str, limit: int = 50, offset: int = 0) -> List[UserRewardEvent]:
        return (
            db.query(UserRewardEvent)
            .filter(UserRewardEvent.user_id == user_id)
            .order_by(UserRewardEvent.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_last_event(db: Session, user_id: str) -> Optional[UserRewardEvent]:
        return (
            db.query(UserRewardEvent)
            .filter(UserRewardEvent.user_id == user_id)
            .order_by(UserRewardEvent.created_at.desc())
            .first()
        )
