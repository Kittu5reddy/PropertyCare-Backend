from fastapi import FastAPI, Request, Form, APIRouter,Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, Dict, Any
import httpx, json, os
from app.core.validators.transaction import Transaction as TransactionSchema
from datetime import datetime
from .utils import *
from app.core.controllers.auth.main import get_current_user,oauth2_scheme
from app.core.models import get_db,AsyncSession
from sqlalchemy import select
from app.user.models.personal_details import PersonalDetails
from app.core.models.subscriptions_plans import SubscriptionPlans

payments = APIRouter('/payments')
templates = Jinja2Templates(directory="templates")

# =========================
# CONFIGURATION
# =========================
PAYPHI_BASE = os.getenv("PAYPHI_BASE", "https://qa.phicommerce.com")
INITIATE_SALE_URL = f"{PAYPHI_BASE}/pg/api/v2/initiateSale"
MERCHANT_ID = os.getenv("PAYPHI_MERCHANT_ID", "T_08886")
SECRET_KEY = os.getenv("PAYPHI_SECRET", "abc")
RETURN_URL = "https://qa.phicommerce.com/pg/api/merchant"

# =========================
# INITIATE PAYMENT
# =========================

@payments.post("/payphi/initiate")
async def payphi_initiate(
    tx_payload: TransactionSchema,
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    # create txn ids (unique transaction number + txnDate)
    merchantTxnNo = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
    txnDate = datetime.now().strftime("%Y%m%d%H%M%S")

    # get the logged-in user
    user = await get_current_user(token, db)

    # fetch personal details for the user
    res = await db.execute(select(PersonalDetails).where(PersonalDetails.user_id == user.user_id))
    user_data = res.scalar_one_or_none()

    # if personal details NOT found -> error (your original code raised when found)
    if not user_data:
        raise HTTPException(status_code=404, detail="User personal details not found. Please complete your profile.")

    # calculate subscription amount (ensure your cal_subscription_amount returns a dict with an amount key)
    calc = await cal_subscription_amount(
        user_id=tx_payload.user_id,
        property_id=tx_payload.property_id,
        sub_id=tx_payload.sub_id,
        duration=tx_payload.duration,
        token=token,
        db=db,
    )

    if not calc:
        raise HTTPException(status_code=400, detail="Unable to calculate subscription amount")

    # --- pick the correct amount key from the returned object ---
    # earlier implementations used keys like 'total_amount' — adapt if necessary
    amount = calc.get("total_amount") or calc.get("amount")
    if amount is None:
        raise HTTPException(status_code=500, detail="Calculated amount missing in response from calculator")

    # ensure we use plain strings, NOT tuples (remove trailing commas)
    customerEmailID = user.email
    customerMobileNo = user_data.contact_number

    # build payload for payment gateway (don't reuse variable name 'payload' which is input)
    initiate_payload: Dict[str, Any] = {
        "addlParam1": tx_payload.user_id,
        "addlParam2": tx_payload.property_id,
        "addlParam3": tx_payload.sub_id,
        "amount": str(amount),              # often gateways expect string; convert if required
        "currencyCode": "356",
        "customerEmailID": customerEmailID,
        "customerMobileNo": customerMobileNo,
        "merchantId": MERCHANT_ID,
        "merchantTxnNo": merchantTxnNo,
        "payType": "0",
        "returnURL": RETURN_URL,
        "transactionType": "SALE",
        "txnDate": txnDate,
    }

    # generate secure hash (assumes generate_v2_hmac accepts (secret, dict) and returns string)
    initiate_payload["secureHash"] = generate_v2_hmac(SECRET_KEY, initiate_payload)

    headers = {"Content-Type": "application/json"}


    # call PG
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(INITIATE_SALE_URL, json=initiate_payload, headers=headers)

    try:
        data = resp.json()
    except Exception:
        raise HTTPException(status_code=502, detail="Invalid response from payment gateway")

    # verify server secure hash (wrap in try/except so we can return a proper error)
    try:
        verify_server_securehash(data, SECRET_KEY)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Payment response verification failed")

    # build redirect URI (safe-guard absent keys)
    redirect_uri = None
    if isinstance(data, dict):
        redirect_base = data.get("redirectURI")
        tranCtx = data.get("tranCtx")
        if redirect_base and tranCtx:
            redirect_uri = f"{redirect_base}?tranCtx={tranCtx}"

    if redirect_uri:
        return templates.TemplateResponse("redirect.html", {"request": request, "redirect_url": redirect_uri})

    # fallback: return the raw response for debugging/client handling
    return JSONResponse(
        status_code=resp.status_code,
        content={
            "http_status": resp.status_code,
            "request": initiate_payload,
            "response": data,
        },
    )
