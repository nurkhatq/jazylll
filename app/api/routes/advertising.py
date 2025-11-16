from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal

from app.db.base import get_db
from app.api.deps import get_current_user
from app.models.user import User, UserRole
from app.models.salon import Salon
from app.models.payment import Payment, PaymentType, PaymentStatus, PaymentMethod
from app.models.catalog import CatalogImpression, CatalogClick

router = APIRouter(prefix="/salons", tags=["Advertising"])


@router.post("/{salon_id}/advertising/topup", status_code=status.HTTP_201_CREATED)
async def topup_advertising_budget(
    salon_id: UUID,
    amount: Decimal,
    payment_method: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Top up advertising budget"""
    salon = db.query(Salon).filter(Salon.id == salon_id).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    # Check permissions
    if salon.owner_id != current_user.id and current_user.role != UserRole.PLATFORM_ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Validate amount (minimum 5000 KZT)
    if amount < Decimal("5000"):
        raise HTTPException(status_code=400, detail="Minimum top-up amount is 5000 KZT")

    # Create payment record
    payment = Payment(
        salon_id=salon_id,
        payment_type=PaymentType.ADVERTISING_BUDGET,
        amount=amount,
        currency="KZT",
        payment_method=PaymentMethod[payment_method.upper()],
        payment_status=PaymentStatus.PENDING,
        payment_metadata={"initiated_by": str(current_user.id)},
    )

    db.add(payment)
    db.flush()

    # In production, integrate with payment gateway
    # For now, simulate payment URL
    payment_url = f"https://payment-gateway.example.com/pay/{payment.id}"

    # TODO: In real implementation:
    # 1. Create payment session with payment provider
    # 2. Return actual payment URL
    # 3. Handle webhook to update payment status and add budget

    # For demonstration, auto-complete the payment
    payment.payment_status = PaymentStatus.COMPLETED
    payment.completed_at = datetime.utcnow()
    payment.transaction_id = f"TXN-{payment.id}"

    # Add to advertising budget
    salon.advertising_budget = (salon.advertising_budget or Decimal("0")) + amount

    db.commit()

    return {
        "id": str(payment.id),
        "amount": float(amount),
        "status": payment.payment_status.value,
        "payment_url": payment_url,
        "message": "Payment completed successfully (simulated). In production, this would redirect to payment gateway.",
        "new_balance": float(salon.advertising_budget),
    }


@router.patch("/{salon_id}/advertising/bid")
async def update_auction_bid(
    salon_id: UUID,
    bid_amount: Decimal,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update auction bid for advertising"""
    salon = db.query(Salon).filter(Salon.id == salon_id).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    # Check permissions
    if salon.owner_id != current_user.id and current_user.role != UserRole.PLATFORM_ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Validate bid amount (minimum 50 KZT per click, or 0 to disable)
    if bid_amount > 0 and bid_amount < Decimal("50"):
        raise HTTPException(status_code=400, detail="Minimum bid is 50 KZT per click")

    # Check budget if enabling auction
    if bid_amount > 0:
        if not salon.advertising_budget or salon.advertising_budget < Decimal("1000"):
            raise HTTPException(
                status_code=400,
                detail="Insufficient advertising budget. Minimum 1000 KZT required to participate in auction.",
            )

    # Update bid
    salon.auction_bid = bid_amount
    db.commit()

    return {
        "auction_bid": float(salon.auction_bid),
        "current_budget": float(salon.advertising_budget or 0),
        "status": "active" if bid_amount > 0 else "inactive",
        "message": "Auction bid updated successfully",
    }


@router.get("/{salon_id}/advertising/stats")
async def get_advertising_stats(
    salon_id: UUID,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get advertising campaign statistics"""
    salon = db.query(Salon).filter(Salon.id == salon_id).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    # Check permissions
    if salon.owner_id != current_user.id and current_user.role != UserRole.PLATFORM_ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Default to current month if dates not specified
    if not date_from:
        date_from = date.today().replace(day=1)
    if not date_to:
        date_to = date.today()

    # Get impressions
    impressions = (
        db.query(CatalogImpression)
        .filter(
            CatalogImpression.salon_id == salon_id,
            CatalogImpression.impression_date >= date_from,
            CatalogImpression.impression_date <= date_to,
        )
        .all()
    )

    total_impressions = len(impressions)
    promoted_impressions = sum(1 for i in impressions if i.is_promoted)

    # Get clicks
    clicks = (
        db.query(CatalogClick)
        .filter(
            CatalogClick.salon_id == salon_id,
            CatalogClick.clicked_at >= datetime.combine(date_from, datetime.min.time()),
            CatalogClick.clicked_at <= datetime.combine(date_to, datetime.max.time()),
        )
        .all()
    )

    total_clicks = len(clicks)
    promoted_clicks = sum(1 for c in clicks if c.is_promoted)

    # Calculate spend
    total_spent = sum(c.cost for c in clicks if c.cost)

    # Calculate CTR (Click Through Rate)
    ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0

    # Calculate average position
    positions = [i.position for i in impressions if i.position]
    average_position = sum(positions) / len(positions) if positions else 0

    # Estimate daily spend based on current bid
    average_clicks_per_day = total_clicks / ((date_to - date_from).days + 1) if (date_to - date_from).days > 0 else 0
    estimated_daily_spend = average_clicks_per_day * float(salon.auction_bid or 0) * 0.5

    # Estimate days remaining with current budget
    days_remaining = (
        int(float(salon.advertising_budget or 0) / estimated_daily_spend)
        if estimated_daily_spend > 0
        else 0
    )

    return {
        "current_budget": float(salon.advertising_budget or 0),
        "current_bid": float(salon.auction_bid or 0),
        "date_from": str(date_from),
        "date_to": str(date_to),
        "total_spent": float(total_spent),
        "total_impressions": total_impressions,
        "promoted_impressions": promoted_impressions,
        "total_clicks": total_clicks,
        "promoted_clicks": promoted_clicks,
        "ctr": round(ctr, 2),
        "average_position": round(average_position, 1),
        "estimated_daily_spend": round(estimated_daily_spend, 2),
        "days_remaining": days_remaining,
    }
