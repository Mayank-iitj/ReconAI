"""
Custom exceptions for SmartRecon-AI
"""

from typing import Optional, Dict, Any
from fastapi import status


class SmartReconException(Exception):
    """Base exception for SmartRecon-AI"""
    
    def __init__(
        self,
        message: str,
        error_code: str = "SMARTRECON_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthorizationError(SmartReconException):
    """Raised when target is not authorized for testing"""
    
    def __init__(self, message: str = "Target not authorized for testing", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )


class ScopeValidationError(SmartReconException):
    """Raised when scope validation fails"""
    
    def __init__(self, message: str = "Scope validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="SCOPE_VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class ToolExecutionError(SmartReconException):
    """Raised when recon tool execution fails"""
    
    def __init__(
        self,
        tool_name: str,
        message: str = "Tool execution failed",
        details: Optional[Dict[str, Any]] = None
    ):
        full_message = f"{tool_name}: {message}"
        super().__init__(
            message=full_message,
            error_code="TOOL_EXECUTION_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details or {"tool": tool_name}
        )


class LLMError(SmartReconException):
    """Raised when LLM API call fails"""
    
    def __init__(self, message: str = "LLM API error", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="LLM_ERROR",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details
        )


class ScanNotFoundError(SmartReconException):
    """Raised when scan is not found"""
    
    def __init__(self, scan_id: int):
        super().__init__(
            message=f"Scan with ID {scan_id} not found",
            error_code="SCAN_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"scan_id": scan_id}
        )


class TargetNotFoundError(SmartReconException):
    """Raised when target is not found"""
    
    def __init__(self, target_id: int):
        super().__init__(
            message=f"Target with ID {target_id} not found",
            error_code="TARGET_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"target_id": target_id}
        )


class RateLimitExceededError(SmartReconException):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details
        )


class ConcurrentScanLimitError(SmartReconException):
    """Raised when concurrent scan limit is reached"""
    
    def __init__(self, current: int, max_allowed: int):
        super().__init__(
            message=f"Concurrent scan limit reached ({current}/{max_allowed})",
            error_code="CONCURRENT_SCAN_LIMIT",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={"current": current, "max_allowed": max_allowed}
        )
