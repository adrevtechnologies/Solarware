"""API routes for minimal user accounts, wallets, and reward event history."""
import hashlib
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..core import get_db
from ..models import UserOnboardingProfile
from ..schemas import (
    UserAccountCreate,
    UserSignupRequest,
    UserAccountResponse,
    UserSummaryResponse,
    UserWalletResponse,
    UserRewardEventCreate,
    UserRewardEventResponse,
    UserRewardEventListResponse,
    OnboardingProfileInput,
    OnboardingIntegrationInput,
    UserOnboardingUpsertRequest,
    UserOnboardingResponse,
    UserOnboardingCompleteResponse,
)
from ..services.user_wallet_service import UserWalletService

router = APIRouter(prefix="/api/users", tags=["users"])


def _normalize(value):
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _profile_completed(profile: UserOnboardingProfile) -> bool:
    return bool(
        profile.full_name
        and profile.email
        and profile.company_name
    )


def _integration_completed(profile: UserOnboardingProfile) -> bool:
    return bool(
        profile.adrev_org_id
        and profile.adrev_campaign_id
        and profile.adrev_base_url
        and profile.adrev_webhook_url
        and profile.adrev_api_key_hash
    )


def _missing_fields(profile: UserOnboardingProfile):
    missing = []
    if not profile.full_name:
        missing.append("profile.full_name")
    if not profile.email:
        missing.append("profile.email")
    if not profile.company_name:
        missing.append("profile.company_name")
    if not profile.adrev_org_id:
        missing.append("integration.adrev_org_id")
    if not profile.adrev_campaign_id:
        missing.append("integration.adrev_campaign_id")
    if not profile.adrev_base_url:
        missing.append("integration.adrev_base_url")
    if not profile.adrev_webhook_url:
        missing.append("integration.adrev_webhook_url")
    if not profile.adrev_api_key_hash:
        missing.append("integration.adrev_api_key")
    return missing


def _to_onboarding_response(profile: UserOnboardingProfile) -> UserOnboardingResponse:
    profile_done = _profile_completed(profile)
    integration_done = _integration_completed(profile)
    return UserOnboardingResponse(
        user_id=profile.user_id,
        profile=OnboardingProfileInput(
            full_name=profile.full_name,
            email=profile.email,
            company_name=profile.company_name,
            role_title=profile.role_title,
            phone=profile.phone,
            country=profile.country,
            website=profile.website,
        ),
        integration=OnboardingIntegrationInput(
            adrev_org_id=profile.adrev_org_id,
            adrev_campaign_id=profile.adrev_campaign_id,
            adrev_base_url=profile.adrev_base_url,
            adrev_webhook_url=profile.adrev_webhook_url,
            adrev_integration_mode=profile.adrev_integration_mode,
            client_dashboard_route=profile.client_dashboard_route,
            adrev_api_key=None,
        ),
        api_key_configured=bool(profile.adrev_api_key_hash),
        api_key_last4=profile.adrev_api_key_last4,
        profile_setup_completed=profile_done,
        integration_setup_completed=integration_done,
        onboarding_completed=bool(profile.onboarding_completed),
        onboarding_completed_at=profile.onboarding_completed_at,
        missing_fields=_missing_fields(profile),
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def _get_or_create_onboarding_profile(db: Session, user_id: str) -> UserOnboardingProfile:
    profile = (
        db.query(UserOnboardingProfile)
        .filter(UserOnboardingProfile.user_id == user_id)
        .first()
    )
    if profile:
        return profile

    profile = UserOnboardingProfile(user_id=user_id)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


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


@router.get("/{user_id}/onboarding", response_model=UserOnboardingResponse)
def get_user_onboarding(user_id: str, db: Session = Depends(get_db)):
    """Get onboarding/profile/API integration state for a user."""
    account = UserWalletService.get_user(db, user_id)
    if not account:
        raise HTTPException(status_code=404, detail="User not found")

    profile = _get_or_create_onboarding_profile(db, user_id)
    return _to_onboarding_response(profile)


@router.put("/{user_id}/onboarding", response_model=UserOnboardingResponse)
def upsert_user_onboarding(
    user_id: str,
    payload: UserOnboardingUpsertRequest,
    db: Session = Depends(get_db),
):
    """Create/update onboarding profile + API integration settings."""
    account = UserWalletService.get_user(db, user_id)
    if not account:
        raise HTTPException(status_code=404, detail="User not found")

    profile = _get_or_create_onboarding_profile(db, user_id)

    if payload.profile is not None:
        profile.full_name = _normalize(payload.profile.full_name)
        profile.email = _normalize(payload.profile.email)
        profile.company_name = _normalize(payload.profile.company_name)
        profile.role_title = _normalize(payload.profile.role_title)
        profile.phone = _normalize(payload.profile.phone)
        profile.country = _normalize(payload.profile.country)
        profile.website = _normalize(payload.profile.website)

    if payload.integration is not None:
        profile.adrev_org_id = _normalize(payload.integration.adrev_org_id)
        profile.adrev_campaign_id = _normalize(payload.integration.adrev_campaign_id)
        profile.adrev_base_url = _normalize(payload.integration.adrev_base_url)
        profile.adrev_webhook_url = _normalize(payload.integration.adrev_webhook_url)
        profile.adrev_integration_mode = _normalize(payload.integration.adrev_integration_mode) or "embedded"
        profile.client_dashboard_route = _normalize(payload.integration.client_dashboard_route)

        api_key = _normalize(payload.integration.adrev_api_key)
        if api_key:
            profile.adrev_api_key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
            profile.adrev_api_key_last4 = api_key[-4:] if len(api_key) >= 4 else api_key

    profile_done = _profile_completed(profile)
    integration_done = _integration_completed(profile)

    if not (profile_done and integration_done):
        profile.onboarding_completed = False
        profile.onboarding_completed_at = None

    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)

    return _to_onboarding_response(profile)


@router.post("/{user_id}/onboarding/complete", response_model=UserOnboardingCompleteResponse)
def complete_user_onboarding(user_id: str, db: Session = Depends(get_db)):
    """Mark onboarding as complete after required profile + integration fields exist."""
    account = UserWalletService.get_user(db, user_id)
    if not account:
        raise HTTPException(status_code=404, detail="User not found")

    profile = _get_or_create_onboarding_profile(db, user_id)
    missing = _missing_fields(profile)
    if missing:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Onboarding is incomplete.",
                "missing_fields": missing,
            },
        )

    profile.onboarding_completed = True
    profile.onboarding_completed_at = datetime.utcnow()
    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)

    return UserOnboardingCompleteResponse(
        user_id=user_id,
        onboarding_completed=True,
        onboarding_completed_at=profile.onboarding_completed_at,
        missing_fields=[],
    )
