import time
import asyncio
from typing import Dict, Optional, Tuple, Any
from collections import defaultdict, deque
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    requests_per_minute: int = 10
    requests_per_hour: int = 100
    burst_size: int = 5
    block_duration: int = 300  # 5 minutes in seconds


class RateLimitInfo:
    """Rate limit information for tracking"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.requests = deque()  # Stores timestamps of requests
        self.blocked_until: Optional[datetime] = None
        self.total_requests = 0
        self.total_blocked = 0
        
    def is_blocked(self) -> bool:
        """Check if this IP is currently blocked"""
        if self.blocked_until:
            if datetime.utcnow() < self.blocked_until:
                return True
            else:
                self.blocked_until = None  # Block expired
        return False
    
    def add_request(self):
        """Add a request timestamp"""
        now = datetime.utcnow()
        self.requests.append(now)
        self.total_requests += 1
        self._cleanup_old_requests()
    
    def _cleanup_old_requests(self):
        """Remove requests older than 1 hour"""
        now = datetime.utcnow()
        cutoff_time = now - timedelta(hours=1)
        
        while self.requests and self.requests[0] < cutoff_time:
            self.requests.popleft()
    
    def get_request_count(self, window_minutes: int = 1) -> int:
        """Get request count in the last X minutes"""
        self._cleanup_old_requests()
        
        if window_minutes == 60:
            return len(self.requests)
        
        now = datetime.utcnow()
        cutoff_time = now - timedelta(minutes=window_minutes)
        
        count = sum(1 for req_time in self.requests if req_time >= cutoff_time)
        return count
    
    def is_rate_limited(self) -> bool:
        """Check if this IP should be rate limited"""
        if self.is_blocked():
            return True
        
        # Check minute limit
        minute_count = self.get_request_count(1)
        if minute_count > self.config.requests_per_minute:
            self._block()
            return True
        
        # Check hour limit
        hour_count = self.get_request_count(60)
        if hour_count > self.config.requests_per_hour:
            self._block()
            return True
        
        return False
    
    def _block(self):
        """Block this IP temporarily"""
        self.blocked_until = datetime.utcnow() + timedelta(seconds=self.config.block_duration)
        self.total_blocked += 1
        logger.warning(f"IP blocked until {self.blocked_until}")
    
    def get_stats(self) -> Dict[str, any]:
        """Get rate limiting statistics"""
        return {
            'total_requests': self.total_requests,
            'total_blocked': self.total_blocked,
            'current_window_requests': self.get_request_count(1),
            'hourly_requests': self.get_request_count(60),
            'is_blocked': self.is_blocked(),
            'blocked_until': self.blocked_until.isoformat() if self.blocked_until else None
        }


class RateLimiter:
    """Rate limiter for API endpoints"""
    
    def __init__(self, config: Optional[Dict[str, RateLimitConfig]] = None):
        self.config = config or {
            'default': RateLimitConfig(),
            'search': RateLimitConfig(requests_per_minute=5, requests_per_hour=50),
            'fuzzy': RateLimitConfig(requests_per_minute=3, requests_per_hour=30),
            'reverse': RateLimitConfig(requests_per_minute=2, requests_per_hour=20),
            'identity': RateLimitConfig(requests_per_minute=10, requests_per_hour=100)
        }
        
        # Store rate limit info per IP and endpoint
        self.rate_limits: Dict[str, Dict[str, RateLimitInfo]] = defaultdict(dict)
        self._lock = asyncio.Lock()
        
        # Cleanup task
        self._cleanup_task = None
        self._cleanup_interval = 3600  # 1 hour in seconds
    
    async def initialize(self):
        """Initialize rate limiter"""
        await self._start_cleanup_task()
        logger.info("Rate limiter initialized")
    
    async def _start_cleanup_task(self):
        """Start background cleanup task"""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._cleanup_old_ips())
    
    async def _cleanup_old_ips(self):
        """Periodically clean up old IP data"""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                await self._cleanup_expired_ips()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Rate limiter cleanup error: {e}")
    
    async def _cleanup_expired_ips(self):
        """Remove old IPs that haven't made requests recently"""
        async with self._lock:
            current_time = datetime.utcnow()
            one_hour_ago = current_time - timedelta(hours=1)
            
            ips_to_remove = []
            
            for ip, endpoint_limits in self.rate_limits.items():
                all_expired = True
                
                for endpoint, limit_info in endpoint_limits.items():
                    # Check if there are any recent requests
                    if limit_info.requests and limit_info.requests[-1] > one_hour_ago:
                        all_expired = False
                        break
                    # Check if still blocked
                    elif limit_info.is_blocked():
                        all_expired = False
                        break
                
                if all_expired:
                    ips_to_remove.append(ip)
            
            for ip in ips_to_remove:
                del self.rate_limits[ip]
            
            if ips_to_remove:
                logger.debug(f"Cleaned up {len(ips_to_remove)} old IP addresses")
    
    def _get_client_ip(self, request) -> str:
        """Extract client IP from request"""
        # Check for forwarded headers first
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(',')[0].strip()
        
        # Fall back to direct connection
        client = request.client
        if client:
            return client.host
        
        return 'unknown'
    
    def _get_endpoint_config(self, endpoint: str) -> RateLimitConfig:
        """Get rate limit config for endpoint"""
        # Map endpoint paths to config keys
        endpoint_map = {
            '/api/search/username': 'search',
            '/api/search/fuzzy-match': 'fuzzy',
            '/api/search/reverse-lookup': 'reverse',
            '/api/results/username': 'search',
            '/api/results/identity-chain': 'identity'
        }
        
        config_key = endpoint_map.get(endpoint, 'default')
        return self.config.get(config_key, self.config['default'])
    
    async def check_rate_limit(self, request, endpoint: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if request should be rate limited
        
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        ip = self._get_client_ip(request)
        
        if ip == 'unknown':
            # Allow requests without IP tracking
            return True, None
        
        config = self._get_endpoint_config(endpoint)
        
        async with self._lock:
            if endpoint not in self.rate_limits[ip]:
                self.rate_limits[ip][endpoint] = RateLimitInfo(config)
            
            limit_info = self.rate_limits[ip][endpoint]
            
            if limit_info.is_rate_limited():
                return False, self._get_rate_limit_headers(limit_info, config)
            
            # Record the request
            limit_info.add_request()
            
            return True, self._get_rate_limit_headers(limit_info, config)
    
    def _get_rate_limit_headers(self, limit_info: RateLimitInfo, config: RateLimitConfig) -> Dict[str, Any]:
        """Generate rate limit headers"""
        minute_remaining = max(0, config.requests_per_minute - limit_info.get_request_count(1))
        hour_remaining = max(0, config.requests_per_hour - limit_info.get_request_count(60))
        
        headers = {
            'X-RateLimit-Limit-Minute': str(config.requests_per_minute),
            'X-RateLimit-Remaining-Minute': str(minute_remaining),
            'X-RateLimit-Limit-Hour': str(config.requests_per_hour),
            'X-RateLimit-Remaining-Hour': str(hour_remaining),
            'X-RateLimit-Reset': self._get_reset_time(config).isoformat()
        }
        
        if limit_info.is_blocked():
            headers['Retry-After'] = str(int((limit_info.blocked_until - datetime.utcnow()).total_seconds()))
        
        return headers
    
    def _get_reset_time(self, config: RateLimitConfig) -> datetime:
        """Get rate limit reset time"""
        now = datetime.utcnow()
        # Reset is at the start of next hour
        next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        return next_hour
    
    async def get_ip_stats(self, ip: str, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """Get rate limiting statistics for an IP"""
        async with self._lock:
            if ip not in self.rate_limits:
                return {'error': 'No data found for this IP'}
            
            if endpoint:
                if endpoint in self.rate_limits[ip]:
                    return self.rate_limits[ip][endpoint].get_stats()
                else:
                    return {'error': 'No data found for this endpoint'}
            else:
                # Return all endpoint stats
                stats = {}
                for ep, limit_info in self.rate_limits[ip].items():
                    stats[ep] = limit_info.get_stats()
                return stats
    
    async def get_all_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics for all IPs"""
        async with self._lock:
            total_requests = 0
            total_blocked = 0
            blocked_ips = []
            
            for ip, endpoint_limits in self.rate_limits.items():
                for endpoint, limit_info in endpoint_limits.items():
                    stats = limit_info.get_stats()
                    total_requests += stats['total_requests']
                    total_blocked += stats['total_blocked']
                    
                    if limit_info.is_blocked():
                        blocked_ips.append({
                            'ip': ip,
                            'endpoint': endpoint,
                            'blocked_until': stats['blocked_until']
                        })
            
            return {
                'total_unique_ips': len(self.rate_limits),
                'total_requests': total_requests,
                'total_blocked_requests': total_blocked,
                'currently_blocked_ips': blocked_ips,
                'endpoints_configured': len(self.config)
            }
    
    async def unblock_ip(self, ip: str, endpoint: Optional[str] = None) -> bool:
        """Manually unblock an IP"""
        async with self._lock:
            if ip not in self.rate_limits:
                return False
            
            if endpoint:
                if endpoint in self.rate_limits[ip]:
                    self.rate_limits[ip][endpoint].blocked_until = None
                    return True
            else:
                # Unblock all endpoints for this IP
                for limit_info in self.rate_limits[ip].values():
                    limit_info.blocked_until = None
                return True
            
            return False
    
    async def reset_ip(self, ip: str, endpoint: Optional[str] = None) -> bool:
        """Reset rate limit counters for an IP"""
        async with self._lock:
            if ip not in self.rate_limits:
                return False
            
            if endpoint:
                if endpoint in self.rate_limits[ip]:
                    # Reset by creating new RateLimitInfo
                    config = self.rate_limits[ip][endpoint].config
                    self.rate_limits[ip][endpoint] = RateLimitInfo(config)
                    return True
            else:
                # Reset all endpoints for this IP
                for ep, limit_info in self.rate_limits[ip].items():
                    config = limit_info.config
                    self.rate_limits[ip][ep] = RateLimitInfo(config)
                return True
            
            return False
    
    async def close(self):
        """Cleanup rate limiter resources"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        self.rate_limits.clear()
        logger.info("Rate limiter closed")


# Global rate limiter instance
_rate_limiter_instance = None


def get_rate_limiter(config: Optional[Dict[str, RateLimitConfig]] = None) -> RateLimiter:
    """Get or create global rate limiter instance"""
    global _rate_limiter_instance
    
    if _rate_limiter_instance is None:
        _rate_limiter_instance = RateLimiter(config)
    
    return _rate_limiter_instance