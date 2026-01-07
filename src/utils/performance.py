"""
Performance optimization utilities.
"""

import time
import asyncio
import functools
from typing import Callable, Any, Optional
from collections import deque
from datetime import datetime, timedelta

from src.utils.logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Rate limiter for API calls."""
    
    def __init__(self, max_calls: int, time_window: int):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = deque()
    
    async def acquire(self):
        """Wait until rate limit allows a call."""
        now = time.time()
        
        # Remove old calls outside time window
        while self.calls and self.calls[0] < now - self.time_window:
            self.calls.popleft()
        
        # Wait if at limit
        if len(self.calls) >= self.max_calls:
            sleep_time = self.calls[0] + self.time_window - now
            if sleep_time > 0:
                logger.debug(f"Rate limit reached, waiting {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
                return await self.acquire()
        
        # Record this call
        self.calls.append(now)


class Cache:
    """Simple in-memory cache with TTL."""
    
    def __init__(self, ttl: int = 3600):
        """
        Initialize cache.
        
        Args:
            ttl: Time to live in seconds
        """
        self.ttl = ttl
        self.cache = {}
        self.timestamps = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key not in self.cache:
            return None
        
        # Check if expired
        if time.time() - self.timestamps[key] > self.ttl:
            del self.cache[key]
            del self.timestamps[key]
            return None
        
        return self.cache[key]
    
    def set(self, key: str, value: Any):
        """Set value in cache."""
        self.cache[key] = value
        self.timestamps[key] = time.time()
    
    def clear(self):
        """Clear cache."""
        self.cache.clear()
        self.timestamps.clear()


def timer(func: Callable) -> Callable:
    """Decorator to time function execution."""
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        elapsed = time.time() - start
        logger.debug(f"{func.__name__} took {elapsed:.2f}s")
        return result
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        logger.debug(f"{func.__name__} took {elapsed:.2f}s")
        return result
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def batch_processor(batch_size: int = 10, max_wait: float = 1.0):
    """
    Decorator to batch process items.
    
    Args:
        batch_size: Maximum batch size
        max_wait: Maximum wait time in seconds
    """
    def decorator(func: Callable):
        queue = []
        last_process = time.time()
        lock = asyncio.Lock()
        
        @functools.wraps(func)
        async def wrapper(item):
            async with lock:
                queue.append(item)
                
                should_process = (
                    len(queue) >= batch_size or
                    time.time() - last_process > max_wait
                )
                
                if should_process:
                    batch = queue.copy()
                    queue.clear()
                    nonlocal last_process
                    last_process = time.time()
                    
                    return await func(batch)
                
                # Wait for batch to fill
                await asyncio.sleep(0.1)
                return None
        
        return wrapper
    
    return decorator


class PerformanceMonitor:
    """Monitor system performance."""
    
    def __init__(self):
        """Initialize performance monitor."""
        self.metrics = {}
        self.start_time = time.time()
    
    def record_metric(self, name: str, value: float):
        """Record a performance metric."""
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append({
            "value": value,
            "timestamp": time.time()
        })
    
    def get_average(self, name: str, last_n: int = 10) -> Optional[float]:
        """Get average of last N measurements."""
        if name not in self.metrics:
            return None
        
        recent = self.metrics[name][-last_n:]
        if not recent:
            return None
        
        return sum(m["value"] for m in recent) / len(recent)
    
    def get_summary(self) -> dict:
        """Get performance summary."""
        summary = {
            "uptime_seconds": time.time() - self.start_time,
            "metrics": {}
        }
        
        for name, values in self.metrics.items():
            if values:
                summary["metrics"][name] = {
                    "count": len(values),
                    "latest": values[-1]["value"],
                    "average": sum(v["value"] for v in values) / len(values),
                    "min": min(v["value"] for v in values),
                    "max": max(v["value"] for v in values),
                }
        
        return summary


# Global instances
_rate_limiters = {}
_caches = {}
_performance_monitor = PerformanceMonitor()


def get_rate_limiter(name: str, max_calls: int, time_window: int) -> RateLimiter:
    """Get or create a rate limiter."""
    if name not in _rate_limiters:
        _rate_limiters[name] = RateLimiter(max_calls, time_window)
    return _rate_limiters[name]


def get_cache(name: str, ttl: int = 3600) -> Cache:
    """Get or create a cache."""
    if name not in _caches:
        _caches[name] = Cache(ttl)
    return _caches[name]


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor."""
    return _performance_monitor


async def optimize_image_batch(images: list, max_concurrent: int = 3):
    """
    Process images concurrently with limit.
    
    Args:
        images: List of image paths
        max_concurrent: Maximum concurrent operations
        
    Returns:
        List of results
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_with_limit(image):
        async with semaphore:
            # Process image
            return image
    
    tasks = [process_with_limit(img) for img in images]
    return await asyncio.gather(*tasks)


def memory_efficient_chunker(iterable, chunk_size: int):
    """
    Chunk data efficiently for large datasets.
    
    Args:
        iterable: Data to chunk
        chunk_size: Size of each chunk
        
    Yields:
        Chunks of data
    """
    chunk = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) >= chunk_size:
            yield chunk
            chunk = []
    
    if chunk:
        yield chunk