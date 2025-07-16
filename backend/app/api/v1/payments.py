"""
Payment processing endpoints.
Handles crypto and M-Pesa payment operations.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Annotated
import logging

from app.core.database import get_db
from app.core.exceptions import PaymentError, ValidationError, NotFoundError
from app.schemas.payment import PaymentRequest, PaymentResponse, PaymentStatus, MpesaCallback
from app.services.payment import PaymentService
from app.services.auth import AuthService # Import AuthService to get the dependency

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/crypto/initiate", response_model=PaymentResponse, summary="Initiate a crypto payment")
async def initiate_crypto_payment(
    payment_request: PaymentRequest,
    background_tasks: BackgroundTasks,
    current_user: Annotated[Any, Depends(AuthService.get_current_user_dependency)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> PaymentResponse:
    """
    Initiate a crypto payment (BTC/USDT).
    Generates payment address and starts background monitoring.
    """
    try:
        payment_service = PaymentService(db)
        result = await payment_service.initiate_crypto_payment(
            user_id=current_user.id,
            payment_request=payment_request
        )
        
        # Start background monitoring for blockchain confirmations
        background_tasks.add_task(
            payment_service.monitor_crypto_payment,
            str(result.transaction_id) # Pass transaction ID as string
        )
        
        logger.info(f"Crypto payment initiated: {result.transaction_id} for user {current_user.id}")
        return result
        
    except ValidationError as e:
        logger.warning(f"Crypto payment validation failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except PaymentError as e:
        logger.error(f"Crypto payment initiation failed: {e.message}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error initiating crypto payment: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate crypto payment due to an unexpected error."
        )

@router.post("/mpesa/stk-push", response_model=PaymentResponse, summary="Initiate M-Pesa STK Push payment")
async def initiate_mpesa_payment(
    payment_request: PaymentRequest,
    current_user: Annotated[Any, Depends(AuthService.get_current_user_dependency)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> PaymentResponse:
    """
    Initiate M-Pesa STK Push payment.
    Sends payment request to user's phone.
    """
    try:
        payment_service = PaymentService(db)
        result = await payment_service.initiate_mpesa_payment(
            user_id=current_user.id,
            payment_request=payment_request
        )
        
        logger.info(f"M-Pesa payment initiated: {result.transaction_id} for user {current_user.id}")
        return result
        
    except ValidationError as e:
        logger.warning(f"M-Pesa payment validation failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except PaymentError as e:
        logger.error(f"M-Pesa payment initiation failed: {e.message}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error initiating M-Pesa payment: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate M-Pesa payment due to an unexpected error."
        )

@router.get("/status/{transaction_id}", response_model=PaymentStatus, summary="Get payment status and details")
async def get_payment_status(
    transaction_id: str,
    current_user: Annotated[Any, Depends(AuthService.get_current_user_dependency)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> PaymentStatus:
    """
    Get payment status and details for a specific transaction.
    """
    try:
        payment_service = PaymentService(db)
        result = await payment_service.get_payment_status(
            transaction_id=transaction_id,
            user_id=current_user.id
        )
        
        return result
        
    except NotFoundError as e:
        logger.warning(f"Payment status request failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Failed to get payment status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve payment status due to an unexpected error."
        )

@router.get("/history", response_model=List[Dict[str, Any]], summary="Get user's payment history")
async def get_payment_history(
    limit: int = 50,
    offset: int = 0,
    current_user: Annotated[Any, Depends(AuthService.get_current_user_dependency)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> List[Dict[str, Any]]:
    """
    Get user's payment history with pagination.
    """
    try:
        payment_service = PaymentService(db)
        result = await payment_service.get_payment_history(
            user_id=current_user.id,
            limit=limit,
            offset=offset
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to get payment history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve payment history due to an unexpected error."
        )

@router.post("/mpesa/callback", summary="M-Pesa callback endpoint for payment confirmations")
async def mpesa_callback(
    callback_data: MpesaCallback, # Use the Pydantic schema for validation
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Dict[str, str]:
    """
    M-Pesa callback endpoint for payment confirmations.
    Handles STK Push and other M-Pesa notifications.
    This endpoint is called by Safaricom Daraja API.
    """
    try:
        payment_service = PaymentService(db)
        await payment_service.process_mpesa_callback(callback_data)
        
        logger.info("M-Pesa callback processed successfully")
        # M-Pesa expects a specific success response
        return {"ResultCode": "0", "ResultDesc": "Success"}
        
    except Exception as e:
        logger.error(f"M-Pesa callback processing failed: {str(e)}", exc_info=True)
        # Return success to M-Pesa even if internal processing fails to avoid retries
        return {"ResultCode": "1", "ResultDesc": "Failed"}
