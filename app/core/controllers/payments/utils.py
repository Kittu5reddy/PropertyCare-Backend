
import  hmac, hashlib
from app.core.controllers.auth.main import get_current_user
from app.core.models import get_db,AsyncSession
from fastapi import Depends,HTTPException
from app.core.controllers.auth.main import oauth2_scheme
from app.user.controllers.properties.utils import get_current_property

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException

from app.user.controllers.subscriptions.utils import get_current_sub

# =========================
# HMAC (Concatenation Logic)
# =========================
def generate_v2_hmac(secret_key: str, data: dict) -> str:
    """Generate HMAC per PayPhi Spec (A–Z concatenation)."""
    clean = {k: v for k, v in data.items() if v not in (None, "", [])}
    sorted_keys = sorted(clean.keys(), key=lambda x: x.lower())
    concat_str = "".join(str(clean[k]) for k in sorted_keys)

    digest = hmac.new(
        secret_key.encode("utf-8"),
        concat_str.encode("ascii"),
        hashlib.sha256
    ).hexdigest().lower()

    print("\n[HMAC DEBUG]")
    print("Sorted Keys:", sorted_keys)
    print("Concatenated String:", concat_str)
    print("Generated HMAC:", digest)
    print("----------------------------\n")

    return digest


# =========================
# VERIFY RETURN HASH
# =========================
def verify_payphi_response_hash(data: dict, secret_key: str) -> bool:
    """Verify PayPhi callback secureHash."""
    received_hash = data.get("secureHash")
    if not received_hash:
        print("[ERROR] Missing secureHash in return payload.")
        return False

    clean = {k: v for k, v in data.items() if k.lower() != "securehash" and v not in (None, "")}
    sorted_keys = sorted(clean.keys(), key=lambda x: x.lower())
    concat_str = "".join(str(clean[k]) for k in sorted_keys) + secret_key
    generated = hashlib.sha256(concat_str.encode("utf-8")).hexdigest().lower()

    print("\n[VERIFY RETURN HASH]")
    print("Concatenated + secret:", concat_str)
    print("Local Hash :", generated)
    print("Server Hash:", received_hash)
    print("Match? →", generated == received_hash)
    print("----------------------------\n")

    return generated == received_hash


# =========================
# VERIFY SERVER HASH (for response)
# =========================
def verify_server_securehash(data: dict, secret_key: str):
    """Validate PayPhi’s response secureHash."""
    server_hash = data.get("secureHash")
    if not server_hash:
        print("[WARN] No secureHash from server")
        return

    clean = {k: v for k, v in data.items() if k.lower() != "securehash" and v not in (None, "")}
    sorted_keys = sorted(clean.keys(), key=lambda x: x.lower())
    concat_str = "".join(str(clean[k]) for k in sorted_keys)
    local_hash = hmac.new(secret_key.encode("utf-8"), concat_str.encode("ascii"), hashlib.sha256).hexdigest().lower()

    print("\n[VERIFY SERVER HASH]")
    print("Concatenated String:", concat_str)
    print("Local Hash :", local_hash)
    print("Server Hash:", server_hash)
    print("Match? →", local_hash == server_hash)
    print("----------------------------\n")







from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

async def cal_subscription_amount(
    user_id: str,
    property_id: str,
    sub_id: str,
    duration: int,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    try:
        # Validate user
        user = await get_current_user(token, db)

        # Validate subscription
        sub = await get_current_sub(sub_id=sub_id, db=db)

        # Validate property
        property = await get_current_property(
            property_id=property_id,
            user_id=user.user_id,
            db=db
        )

        # ------------------------------------------------------
        # Category mismatch
        # ------------------------------------------------------
        if sub.category.upper() != property.type.upper():
            raise HTTPException(
                status_code=400,
                detail="Subscription category does not match property type",
            )

        # ------------------------------------------------------
        # FLAT Calculation
        # ------------------------------------------------------
        if property.type.upper() == "FLAT":
            rental_income = property.rental_income or 0

            # If rental income is >15000 → percentage calculation
            if rental_income > 15000:
                total_amount = duration * (
                    rental_income * (sub.rental_percentages / 100)
                )
                return {
                    "property_type": "FLAT",
                    "duration": duration,
                    "calculation": "percentage",
                    "percentage": sub.rental_percentages,
                    "rental_income": rental_income,
                    "total_amount": round(total_amount, 2),
                }

            # Else → fixed amount from durations
            fixed_amount = sub.durations.get(str(duration))
            if fixed_amount is None:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid duration for this subscription plan",
                )

            return {
                "property_type": "FLAT",
                "duration": duration,
                "calculation": "fixed",
                "total_amount": fixed_amount,
            }

        # ------------------------------------------------------
        # PLOT Calculation (always fixed)
        # ------------------------------------------------------
        if property.type.upper() == "PLOT":
            fixed_amount = sub.durations.get(str(duration))
            if fixed_amount is None:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid duration for this subscription plan",
                )

            return {
                "property_type": "PLOT",
                "duration": duration,
                "calculation": "fixed",
                "total_amount": fixed_amount,
            }

        # ------------------------------------------------------
        # Unsupported Property Type
        # ------------------------------------------------------
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported property type: {property.type}",
        )

    # ----------------------------------------------------------
    # HTTP Exceptions (return directly)
    # ----------------------------------------------------------
    except HTTPException:
        raise

    # ----------------------------------------------------------
    # Other unexpected errors
    # ----------------------------------------------------------
    except Exception as e:
        print("Error in cal_subscription_amount:", e)
        raise HTTPException(
            status_code=500,
            detail="Failed to calculate subscription amount",
        )
