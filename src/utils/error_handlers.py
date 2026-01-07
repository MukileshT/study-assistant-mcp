"""
Custom error handlers and exception classes.
"""

import sys
import traceback
from typing import Optional, Callable, Any
from functools import wraps

from .logger import get_logger, console

logger = get_logger(__name__)


class StudyAssistantError(Exception):
    """Base exception for Study Assistant errors."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        """
        Initialize error.
        
        Args:
            message: Error message
            details: Additional error details
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class ConfigurationError(StudyAssistantError):
    """Error in configuration or settings."""
    pass


class APIError(StudyAssistantError):
    """Error calling external API."""
    
    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[dict] = None,
    ):
        """
        Initialize API error.
        
        Args:
            message: Error message
            provider: API provider name
            status_code: HTTP status code
            details: Additional details
        """
        self.provider = provider
        self.status_code = status_code
        error_details = details or {}
        
        if provider:
            error_details["provider"] = provider
        if status_code:
            error_details["status_code"] = status_code
        
        super().__init__(message, error_details)


class ProcessingError(StudyAssistantError):
    """Error during image or text processing."""
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        stage: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        """
        Initialize processing error.
        
        Args:
            message: Error message
            file_path: File being processed
            stage: Processing stage
            details: Additional details
        """
        self.file_path = file_path
        self.stage = stage
        error_details = details or {}
        
        if file_path:
            error_details["file_path"] = file_path
        if stage:
            error_details["stage"] = stage
        
        super().__init__(message, error_details)


class StorageError(StudyAssistantError):
    """Error during storage operations."""
    
    def __init__(
        self,
        message: str,
        storage_type: Optional[str] = None,
        operation: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        """
        Initialize storage error.
        
        Args:
            message: Error message
            storage_type: Type of storage (notion, database, file)
            operation: Operation being performed
            details: Additional details
        """
        self.storage_type = storage_type
        self.operation = operation
        error_details = details or {}
        
        if storage_type:
            error_details["storage_type"] = storage_type
        if operation:
            error_details["operation"] = operation
        
        super().__init__(message, error_details)


def handle_error(
    error: Exception,
    context: Optional[dict] = None,
    reraise: bool = False,
    exit_on_error: bool = False,
) -> Optional[Exception]:
    """
    Handle an error with logging and optional actions.
    
    Args:
        error: The exception to handle
        context: Additional context information
        reraise: Whether to re-raise the exception
        exit_on_error: Whether to exit the program
        
    Returns:
        The error if not reraised, None otherwise
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    # Log the error
    logger.error(
        f"{error_type}: {error_msg}",
        extra={"context": context or {}},
        exc_info=True
    )
    
    # Display user-friendly message
    if isinstance(error, StudyAssistantError):
        console.print(f"\n[red]Error:[/red] {error.message}")
        if error.details:
            console.print(f"[dim]Details: {error.details}[/dim]")
    else:
        console.print(f"\n[red]Unexpected Error:[/red] {error_msg}")
    
    # Show traceback in debug mode
    from config.settings import get_settings
    settings = get_settings()
    if settings.log_level == "DEBUG":
        console.print("\n[dim]Traceback:[/dim]")
        traceback.print_exc()
    
    # Exit if requested
    if exit_on_error:
        console.print("\n[red]Exiting due to error.[/red]")
        sys.exit(1)
    
    # Re-raise if requested
    if reraise:
        raise error
    
    return error


def error_handler_decorator(
    reraise: bool = False,
    default_return: Any = None,
    context_func: Optional[Callable] = None,
):
    """
    Decorator to handle errors in functions.
    
    Args:
        reraise: Whether to re-raise exceptions
        default_return: Default return value on error
        context_func: Function to generate context from args/kwargs
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                context = {}
                if context_func:
                    try:
                        context = context_func(*args, **kwargs)
                    except:
                        pass
                
                context["function"] = func.__name__
                handle_error(e, context=context, reraise=reraise)
                return default_return
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = {}
                if context_func:
                    try:
                        context = context_func(*args, **kwargs)
                    except:
                        pass
                
                context["function"] = func.__name__
                handle_error(e, context=context, reraise=reraise)
                return default_return
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def format_error_message(error: Exception) -> str:
    """
    Format an error message for display.
    
    Args:
        error: The exception
        
    Returns:
        Formatted error message
    """
    if isinstance(error, StudyAssistantError):
        msg = f"{type(error).__name__}: {error.message}"
        if error.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in error.details.items())
            msg += f" ({detail_str})"
        return msg
    else:
        return f"{type(error).__name__}: {str(error)}"


def create_error_report(
    error: Exception,
    context: Optional[dict] = None,
) -> dict:
    """
    Create a structured error report.
    
    Args:
        error: The exception
        context: Additional context
        
    Returns:
        Error report dictionary
    """
    report = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc(),
    }
    
    if isinstance(error, StudyAssistantError):
        report["details"] = error.details
    
    if context:
        report["context"] = context
    
    return report


class ErrorRecovery:
    """Helper class for error recovery strategies."""
    
    @staticmethod
    async def retry_with_backoff(
        func: Callable,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        *args,
        **kwargs
    ) -> Any:
        """
        Retry a function with exponential backoff.
        
        Args:
            func: Function to retry
            max_retries: Maximum number of retries
            backoff_factor: Backoff multiplier
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries fail
        """
        import asyncio
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                
                if attempt < max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    logger.warning(
                        f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {str(e)}"
                    )
                    await asyncio.sleep(wait_time)
                    continue
        
        logger.error(f"All {max_retries} attempts failed")
        raise last_error
    
    @staticmethod
    def with_fallback(
        primary_func: Callable,
        fallback_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Try primary function, fall back to secondary on error.
        
        Args:
            primary_func: Primary function to try
            fallback_func: Fallback function
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Result from successful function
        """
        try:
            return primary_func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Primary function failed, using fallback: {str(e)}")
            return fallback_func(*args, **kwargs)


# Pre-configured error handlers for common scenarios
def handle_api_error(error: Exception, provider: str):
    """Handle API-related errors."""
    if isinstance(error, APIError):
        handle_error(error)
    else:
        api_error = APIError(
            message=str(error),
            provider=provider,
        )
        handle_error(api_error)


def handle_file_error(error: Exception, file_path: str):
    """Handle file-related errors."""
    if isinstance(error, ProcessingError):
        handle_error(error)
    else:
        processing_error = ProcessingError(
            message=str(error),
            file_path=file_path,
        )
        handle_error(processing_error)


def handle_storage_error(error: Exception, storage_type: str, operation: str):
    """Handle storage-related errors."""
    if isinstance(error, StorageError):
        handle_error(error)
    else:
        storage_error = StorageError(
            message=str(error),
            storage_type=storage_type,
            operation=operation,
        )
        handle_error(storage_error)