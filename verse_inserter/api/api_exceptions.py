"""
Custom exception classes for API operations.

Provides granular exception hierarchy for precise error handling
and user-friendly error messages.

Author: Kasim Lyee <lyee@codewithlyee.com>
Organization: Softlite Inc.
License: Proprietary - All Rights Reserved
"""


class APIError(Exception):
    """Base exception for all API-related errors."""
    
    def __init__(self, message: str, status_code: int = None):
        """
        Initialize API error.
        
        Args:
            message: Human-readable error description
            status_code: HTTP status code if applicable
        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class APIConnectionError(APIError):
    """Raised when API connection fails due to network issues."""
    
    def __init__(self, message: str = "Failed to connect to API service"):
        super().__init__(message)


class APIAuthenticationError(APIError):
    """Raised when API authentication fails (invalid key)."""
    
    def __init__(self, message: str = "Invalid API key or authentication failed"):
        super().__init__(message, status_code=401)


class APIRateLimitError(APIError):
    """Raised when API rate limit is exceeded."""
    
    def __init__(self, message: str = "API rate limit exceeded", retry_after: int = None):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class APIVerseNotFoundError(APIError):
    """Raised when requested verse is not found in translation."""
    
    def __init__(self, message: str = "Verse not found in specified translation"):
        super().__init__(message, status_code=404)


class APITimeoutError(APIError):
    """Raised when API request times out."""
    
    def __init__(self, message: str = "API request timed out"):
        super().__init__(message)


class APIServerError(APIError):
    """Raised when API server returns 5xx error."""
    
    def __init__(self, message: str = "API server error", status_code: int = 500):
        super().__init__(message, status_code=status_code)