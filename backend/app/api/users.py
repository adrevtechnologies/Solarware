"""API routes for minimal user accounts, wallets, and reward event history."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..core import get_db
from ..schemas import (
    UserAccountCreate,
    UserSignupRequest,
    UserAccountResponse,
    UserSummaryResponse,
    UserWalletResponse,
    UserRewardEventCreate,
    UserRewardEventResponse,
    UserRewardEventListResponse,
)
from ..services.user_wallet_service import UserWalletService

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/signup", response_model=UserAccountResponse, status_code=status.HTTP_201_CREATED)
def signup_user(payload: UserSignupRequest, db: Session = Depends(get_db)):
    """Website-facing self-signup endpoint. Generates user_id when omitted."""
    try:
        account, wallet = UserWalletService.signup_user(db, payload.desired_user_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return UserAccountResponse(
        user_id=account.user_id,
        is_active=account.is_active,
        created_at=account.created_at,
        wallet=UserWalletResponse(
            user_id=wallet.user_id,
            points_balance=wallet.points_balance,
            updated_at=wallet.updated_at,
        ),
    )


@router.post("", response_model=UserAccountResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserAccountCreate, db: Session = Depends(get_db)):
    """Create a user account with an initialized points wallet."""
    try:
        account, wallet = UserWalletService.create_user_with_wallet(db, payload.user_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return UserAccountResponse(
        user_id=account.user_id,
        is_active=account.is_active,
        created_at=account.created_at,
        wallet=UserWalletResponse(
            user_id=wallet.user_id,
            points_balance=wallet.points_balance,
            updated_at=wallet.updated_at,
        ),
    )


@router.get("/{user_id}", response_model=UserSummaryResponse)
def get_user(user_id: str, db: Session = Depends(get_db)):
    """Get user summary including wallet and last event timestamp."""
    account = UserWalletService.get_user(db, user_id)
    if not account:
        raise HTTPException(status_code=404, detail="User not found")

    wallet = UserWalletService.get_wallet(db, user_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    last_event = UserWalletService.get_last_event(db, user_id)

    return UserSummaryResponse(
        user_id=account.user_id,
        is_active=account.is_active,
        created_at=account.created_at,
        last_event_at=last_event.created_at if last_event else None,
        wallet=UserWalletResponse(
            user_id=wallet.user_id,
            points_balance=wallet.points_balance,
            updated_at=wallet.updated_at,
        ),
    )


@router.get("/{user_id}/wallet", response_model=UserWalletResponse)
def get_user_wallet(user_id: str, db: Session = Depends(get_db)):
    """Get the current wallet balance for a user."""
    wallet = UserWalletService.get_wallet(db, user_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    return UserWalletResponse(
        user_id=wallet.user_id,
        points_balance=wallet.points_balance,
        updated_at=wallet.updated_at,
    )


@router.post("/{user_id}/events", response_model=UserRewardEventResponse)
def append_user_event(user_id: str, payload: UserRewardEventCreate, db: Session = Depends(get_db)):
    """Append an event to user history and update wallet balance by points_delta."""
    try:
        event, _, _ = UserWalletService.append_event(
            db=db,
            user_id=user_id,
            event_type=payload.event_type,
            points_delta=payload.points_delta,
            external_event_id=payload.external_event_id,
            payload=payload.payload,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return UserRewardEventResponse(
        id=event.id,
        user_id=event.user_id,
        event_type=event.event_type,
        points_delta=event.points_delta,
        balance_after=event.balance_after,
        external_event_id=event.external_event_id,
        payload=event.payload,
        created_at=event.created_at,
    )


@router.get("/{user_id}/events", response_model=UserRewardEventListResponse)
def list_user_events(
    user_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List user reward/wallet events in reverse chronological order."""
    account = UserWalletService.get_user(db, user_id)
    if not account:
        raise HTTPException(status_code=404, detail="User not found")

    events = UserWalletService.list_events(db, user_id=user_id, limit=limit, offset=offset)
    return UserRewardEventListResponse(
        user_id=user_id,
        count=len(events),
        events=[
            UserRewardEventResponse(
                id=e.id,
                user_id=e.user_id,
                event_type=e.event_type,
                points_delta=e.points_delta,
                balance_after=e.balance_after,
                external_event_id=e.external_event_id,
                payload=e.payload,
                created_at=e.created_at,
            )
            for e in events
        ],
    )
