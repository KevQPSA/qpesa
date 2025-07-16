"""
Custom exception classes for the application.
Provides standardized error responses for API endpoints.
"""
from fastapi import HTTPException, status
from typing import Any, Dict, Optional

class CustomException(HTTPException):
    """Base custom exception for the application."""
    def __init__(self, status_code: int, message: str, details: dict = None):
        super().__init__(status_code=status_code, detail={"error": message, "details": details})
        self.message = message
        self.details = details

class AuthenticationError(CustomException):
    """Raised when authentication fails (e.g., invalid credentials, token)."""
    def __init__(self, message: str = "Authentication failed", details: dict = None):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, message=message, details=details)

class AuthorizationError(CustomException):
    """Raised when a user is not authorized to perform an action."""
    def __init__(self, message: str = "Not authorized to perform this action", details: dict = None):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, message=message, details=details)

class ValidationError(CustomException):
    """Raised when input data fails validation."""
    def __init__(self, message: str = "Validation error", details: dict = None):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, message=message, details=details)

class NotFoundError(CustomException):
    """Raised when a requested resource is not found."""
    def __init__(self, message: str = "Resource not found", details: dict = None):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, message=message, details=details)

class PaymentError(CustomException):
    """Raised when a payment operation fails."""
    def __init__(self, message: str = "Payment processing failed", details: dict = None):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, message=message, details=details)

class BlockchainError(CustomException):
    """Raised when there's an issue interacting with a blockchain service."""
    def __init__(self, message: str = "Blockchain service error", details: dict = None):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, message=message, details=details)

class DuplicateEntryError(CustomException):
    """Raised when attempting to create a duplicate resource."""
    def __init__(self, message: str = "Duplicate entry", details: dict = None):
        super().__init__(status_code=status.HTTP_409_CONFLICT, message=message, details=details)

class MpesaError(CustomException):
    """Raised when M-Pesa API interaction fails."""
    def __init__(self, message: str = "M-Pesa service unavailable", details: dict = None):
        super().__init__(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, message=message, details=details)

class DatabaseError(CustomException):
    """Raised when there's an issue with database operations."""
    def __init__(self, message: str = "Database operation failed", details: dict = None):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, message=message, details=details)
