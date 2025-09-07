"""
Comprehensive error handling and retry mechanisms
"""

import time
import random
from typing import Callable, Any, Optional, Dict, List
from functools import wraps
from enum import Enum
from loguru import logger


class ErrorType(Enum):
    """Types of errors that can occur"""
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    PARSING_ERROR = "parsing_error"
    AUTHENTICATION_ERROR = "authentication_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    ELEMENT_NOT_FOUND = "element_not_found"
    UNKNOWN_ERROR = "unknown_error"


class RetryConfig:
    """Configuration for retry behavior"""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_errors: List[ErrorType] = None
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_errors = retryable_errors or [
            ErrorType.NETWORK_ERROR,
            ErrorType.TIMEOUT_ERROR,
            ErrorType.RATE_LIMIT_ERROR
        ]


class ErrorHandler:
    """Centralized error handling and retry logic"""
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
        self.error_stats = {}
    
    def classify_error(self, error: Exception) -> ErrorType:
        """Classify an error into a specific type"""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # Network-related errors
        if any(keyword in error_str for keyword in ['connection', 'network', 'dns', 'timeout']):
            return ErrorType.NETWORK_ERROR
        
        # Timeout errors
        if 'timeout' in error_str or 'TimeoutException' in error_type:
            return ErrorType.TIMEOUT_ERROR
        
        # Rate limiting
        if any(keyword in error_str for keyword in ['rate limit', 'too many requests', '429']):
            return ErrorType.RATE_LIMIT_ERROR
        
        # Authentication errors
        if any(keyword in error_str for keyword in ['unauthorized', 'forbidden', '401', '403']):
            return ErrorType.AUTHENTICATION_ERROR
        
        # Element not found (for web scraping)
        if 'NoSuchElementException' in error_type or 'element not found' in error_str:
            return ErrorType.ELEMENT_NOT_FOUND
        
        # Parsing errors
        if any(keyword in error_str for keyword in ['parse', 'json', 'xml', 'html']):
            return ErrorType.PARSING_ERROR
        
        return ErrorType.UNKNOWN_ERROR
    
    def should_retry(self, error: Exception) -> bool:
        """Determine if an error should trigger a retry"""
        error_type = self.classify_error(error)
        return error_type in self.config.retryable_errors
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for exponential backoff with jitter"""
        delay = self.config.base_delay * (self.config.exponential_base ** attempt)
        delay = min(delay, self.config.max_delay)
        
        if self.config.jitter:
            # Add random jitter to prevent thundering herd
            jitter = random.uniform(0.1, 0.3) * delay
            delay += jitter
        
        return delay
    
    def log_error(self, error: Exception, attempt: int, context: str = ""):
        """Log error with context and attempt information"""
        error_type = self.classify_error(error)
        
        # Update error statistics
        if error_type not in self.error_stats:
            self.error_stats[error_type] = 0
        self.error_stats[error_type] += 1
        
        logger.error(
            f"Error in {context}: {error_type.value} (attempt {attempt + 1}) - {str(error)}"
        )
    
    def retry_with_backoff(
        self,
        func: Callable,
        *args,
        context: str = "",
        **kwargs
    ) -> Any:
        """Execute function with retry logic and exponential backoff"""
        last_error = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                
                # Log success if we had previous failures
                if attempt > 0:
                    logger.info(f"Success after {attempt} retries in {context}")
                
                return result
                
            except Exception as error:
                last_error = error
                self.log_error(error, attempt, context)
                
                # Don't retry on the last attempt
                if attempt == self.config.max_retries:
                    break
                
                # Check if we should retry this error
                if not self.should_retry(error):
                    logger.warning(f"Non-retryable error in {context}: {str(error)}")
                    break
                
                # Calculate delay and wait
                delay = self.calculate_delay(attempt)
                logger.info(f"Retrying {context} in {delay:.2f} seconds...")
                time.sleep(delay)
        
        # If we get here, all retries failed
        logger.error(f"All retries failed for {context}")
        raise last_error
    
    def get_error_stats(self) -> Dict[str, int]:
        """Get error statistics"""
        return {error_type.value: count for error_type, count in self.error_stats.items()}
    
    def reset_stats(self):
        """Reset error statistics"""
        self.error_stats.clear()


# Global error handler instance
error_handler = ErrorHandler()


def with_retry(
    config: RetryConfig = None,
    context: str = ""
):
    """Decorator for adding retry logic to functions"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            handler = ErrorHandler(config) if config else error_handler
            return handler.retry_with_backoff(func, *args, context=context or func.__name__, **kwargs)
        return wrapper
    return decorator


class ScrapingError(Exception):
    """Custom exception for scraping-related errors"""
    
    def __init__(self, message: str, error_type: ErrorType = ErrorType.UNKNOWN_ERROR, context: Dict = None):
        super().__init__(message)
        self.error_type = error_type
        self.context = context or {}


class RateLimitError(ScrapingError):
    """Exception for rate limiting errors"""
    
    def __init__(self, message: str, retry_after: int = None):
        super().__init__(message, ErrorType.RATE_LIMIT_ERROR)
        self.retry_after = retry_after


class AuthenticationError(ScrapingError):
    """Exception for authentication errors"""
    
    def __init__(self, message: str):
        super().__init__(message, ErrorType.AUTHENTICATION_ERROR)


class ParsingError(ScrapingError):
    """Exception for data parsing errors"""
    
    def __init__(self, message: str, raw_data: str = None):
        super().__init__(message, ErrorType.PARSING_ERROR)
        self.raw_data = raw_data


# Utility functions for common error handling patterns

def handle_network_error(func: Callable) -> Callable:
    """Decorator specifically for network-related operations"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_type = error_handler.classify_error(e)
            if error_type == ErrorType.NETWORK_ERROR:
                logger.warning(f"Network error in {func.__name__}: {str(e)}")
            raise
    return wrapper


def handle_timeout_error(func: Callable) -> Callable:
    """Decorator specifically for timeout-related operations"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_type = error_handler.classify_error(e)
            if error_type == ErrorType.TIMEOUT_ERROR:
                logger.warning(f"Timeout error in {func.__name__}: {str(e)}")
            raise
    return wrapper


def safe_execute(func: Callable, default_return: Any = None, context: str = "") -> Any:
    """Safely execute a function with error handling"""
    try:
        return func()
    except Exception as e:
        error_handler.log_error(e, 0, context)
        return default_return


# Error recovery strategies

class RecoveryStrategy:
    """Base class for error recovery strategies"""
    
    def can_recover(self, error: Exception) -> bool:
        """Check if this strategy can recover from the error"""
        raise NotImplementedError
    
    def recover(self, error: Exception, context: Dict = None) -> Any:
        """Attempt to recover from the error"""
        raise NotImplementedError


class FallbackDataStrategy(RecoveryStrategy):
    """Strategy for providing fallback data when scraping fails"""
    
    def __init__(self, fallback_data: Any):
        self.fallback_data = fallback_data
    
    def can_recover(self, error: Exception) -> bool:
        return isinstance(error, (ParsingError, ScrapingError))
    
    def recover(self, error: Exception, context: Dict = None) -> Any:
        logger.info("Using fallback data due to scraping error")
        return self.fallback_data


class RetryWithDelayStrategy(RecoveryStrategy):
    """Strategy for retrying with increased delay"""
    
    def __init__(self, delay: float = 5.0):
        self.delay = delay
    
    def can_recover(self, error: Exception) -> bool:
        return error_handler.classify_error(error) == ErrorType.RATE_LIMIT_ERROR
    
    def recover(self, error: Exception, context: Dict = None) -> Any:
        logger.info(f"Waiting {self.delay} seconds before retry due to rate limiting")
        time.sleep(self.delay)
        return None  # Indicates retry should be attempted


# Error monitoring and alerting

class ErrorMonitor:
    """Monitor errors and trigger alerts when thresholds are exceeded"""
    
    def __init__(self, error_threshold: int = 10, time_window: int = 300):
        self.error_threshold = error_threshold
        self.time_window = time_window
        self.error_history = []
    
    def record_error(self, error: Exception, context: str = ""):
        """Record an error occurrence"""
        error_record = {
            'timestamp': time.time(),
            'error_type': error_handler.classify_error(error),
            'context': context,
            'message': str(error)
        }
        self.error_history.append(error_record)
        
        # Clean old errors
        current_time = time.time()
        self.error_history = [
            record for record in self.error_history
            if current_time - record['timestamp'] <= self.time_window
        ]
        
        # Check if threshold is exceeded
        if len(self.error_history) >= self.error_threshold:
            self._trigger_alert()
    
    def _trigger_alert(self):
        """Trigger an alert when error threshold is exceeded"""
        logger.critical(
            f"Error threshold exceeded: {len(self.error_history)} errors in {self.time_window} seconds"
        )
        # Here you could integrate with external alerting systems
        # like Slack, email, or monitoring services
    
    def get_error_rate(self) -> float:
        """Get current error rate (errors per minute)"""
        current_time = time.time()
        recent_errors = [
            record for record in self.error_history
            if current_time - record['timestamp'] <= 60  # Last minute
        ]
        return len(recent_errors)


# Global error monitor
error_monitor = ErrorMonitor()
