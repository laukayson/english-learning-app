"""
Rate Limiter for Language Learning App
Implements rate limiting to prevent DDOS attacks and abuse
"""

import time
import logging
from collections import defaultdict, deque
from typing import Dict, Any, Optional
import threading

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self):
        self.clients = defaultdict(lambda: {
            'requests': deque(),
            'blocked_until': 0,
            'violation_count': 0
        })
        self.lock = threading.Lock()
        
        # Rate limiting configuration
        self.limits = {
            'default': {
                'requests_per_minute': 30,
                'requests_per_hour': 200,
                'requests_per_day': 1000
            },
            'ai_chat': {
                'requests_per_minute': 10,
                'requests_per_hour': 100,
                'requests_per_day': 500
            },
            'image_generation': {
                'requests_per_minute': 2,
                'requests_per_hour': 10,
                'requests_per_day': 50
            },
            'voice_processing': {
                'requests_per_minute': 60,
                'requests_per_hour': 500,
                'requests_per_day': 2000
            }
        }
        
        # Blocking configuration
        self.block_durations = {
            1: 10,      # 10 seconds for first violation
            2: 30,      # 30 seconds for second violation
            3: 60,      # 1 minute for third violation
            4: 300,     # 5 minutes for fourth violation
            5: 900      # 15 minutes for fifth+ violations
        }
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_old_requests, daemon=True)
        self.cleanup_thread.start()

    def allow_request(self, client_id: str, endpoint_type: str = 'default') -> bool:
        """Check if a request should be allowed for the given client"""
        
        with self.lock:
            current_time = time.time()
            client_data = self.clients[client_id]
            
            # Check if client is currently blocked
            if current_time < client_data['blocked_until']:
                logger.info(f"Request blocked for client {client_id}: still in timeout")
                return False
            
            # Get rate limits for this endpoint type
            limits = self.limits.get(endpoint_type, self.limits['default'])
            
            # Clean old requests
            self._clean_old_requests(client_data['requests'], current_time)
            
            # Check rate limits
            if self._check_rate_limit(client_data['requests'], limits, current_time):
                # Add current request
                client_data['requests'].append(current_time)
                return True
            else:
                # Rate limit exceeded - apply blocking
                self._apply_blocking(client_id, client_data)
                logger.warning(f"Rate limit exceeded for client {client_id}, endpoint: {endpoint_type}")
                return False

    def _check_rate_limit(self, requests: deque, limits: Dict[str, int], current_time: float) -> bool:
        """Check if the request is within rate limits"""
        
        # Check requests per minute
        minute_ago = current_time - 60
        minute_requests = sum(1 for req_time in requests if req_time >= minute_ago)
        if minute_requests >= limits['requests_per_minute']:
            return False
        
        # Check requests per hour
        hour_ago = current_time - 3600
        hour_requests = sum(1 for req_time in requests if req_time >= hour_ago)
        if hour_requests >= limits['requests_per_hour']:
            return False
        
        # Check requests per day
        day_ago = current_time - 86400
        day_requests = sum(1 for req_time in requests if req_time >= day_ago)
        if day_requests >= limits['requests_per_day']:
            return False
        
        return True

    def _clean_old_requests(self, requests: deque, current_time: float):
        """Remove requests older than 24 hours"""
        
        day_ago = current_time - 86400
        while requests and requests[0] < day_ago:
            requests.popleft()

    def _apply_blocking(self, client_id: str, client_data: Dict[str, Any]):
        """Apply blocking to a client that exceeded rate limits"""
        
        client_data['violation_count'] += 1
        violation_count = min(client_data['violation_count'], 5)
        
        block_duration = self.block_durations[violation_count]
        client_data['blocked_until'] = time.time() + block_duration
        
        logger.warning(f"Client {client_id} blocked for {block_duration} seconds (violation #{violation_count})")

    def _cleanup_old_requests(self):
        """Background thread to cleanup old client data"""
        
        while True:
            try:
                time.sleep(3600)  # Run every hour
                
                with self.lock:
                    current_time = time.time()
                    clients_to_remove = []
                    
                    for client_id, client_data in self.clients.items():
                        # Clean old requests
                        self._clean_old_requests(client_data['requests'], current_time)
                        
                        # Remove clients with no recent activity
                        if (not client_data['requests'] and 
                            current_time > client_data['blocked_until'] and
                            current_time - client_data.get('last_request', 0) > 86400):
                            clients_to_remove.append(client_id)
                    
                    for client_id in clients_to_remove:
                        del self.clients[client_id]
                    
                    if clients_to_remove:
                        logger.info(f"Cleaned up {len(clients_to_remove)} inactive clients")
                        
            except Exception as e:
                logger.error(f"Error in cleanup thread: {e}")

    def get_client_status(self, client_id: str) -> Dict[str, Any]:
        """Get current status for a client"""
        
        with self.lock:
            current_time = time.time()
            client_data = self.clients[client_id]
            
            # Clean old requests
            self._clean_old_requests(client_data['requests'], current_time)
            
            # Calculate current usage
            minute_ago = current_time - 60
            hour_ago = current_time - 3600
            day_ago = current_time - 86400
            
            minute_requests = sum(1 for req_time in client_data['requests'] if req_time >= minute_ago)
            hour_requests = sum(1 for req_time in client_data['requests'] if req_time >= hour_ago)
            day_requests = sum(1 for req_time in client_data['requests'] if req_time >= day_ago)
            
            is_blocked = current_time < client_data['blocked_until']
            time_until_unblock = max(0, client_data['blocked_until'] - current_time) if is_blocked else 0
            
            return {
                'client_id': client_id,
                'is_blocked': is_blocked,
                'time_until_unblock': int(time_until_unblock),
                'violation_count': client_data['violation_count'],
                'current_usage': {
                    'minute': minute_requests,
                    'hour': hour_requests,
                    'day': day_requests
                },
                'limits': self.limits['default'],
                'requests_remaining': {
                    'minute': max(0, self.limits['default']['requests_per_minute'] - minute_requests),
                    'hour': max(0, self.limits['default']['requests_per_hour'] - hour_requests),
                    'day': max(0, self.limits['default']['requests_per_day'] - day_requests)
                }
            }

    def reset_client(self, client_id: str):
        """Reset a client's rate limiting data (admin function)"""
        
        with self.lock:
            if client_id in self.clients:
                del self.clients[client_id]
                logger.info(f"Reset rate limiting data for client {client_id}")

    def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide rate limiting statistics"""
        
        with self.lock:
            current_time = time.time()
            
            total_clients = len(self.clients)
            blocked_clients = sum(1 for client_data in self.clients.values() 
                                if current_time < client_data['blocked_until'])
            
            total_requests_minute = 0
            total_requests_hour = 0
            total_requests_day = 0
            
            minute_ago = current_time - 60
            hour_ago = current_time - 3600
            day_ago = current_time - 86400
            
            for client_data in self.clients.values():
                self._clean_old_requests(client_data['requests'], current_time)
                
                total_requests_minute += sum(1 for req_time in client_data['requests'] if req_time >= minute_ago)
                total_requests_hour += sum(1 for req_time in client_data['requests'] if req_time >= hour_ago)
                total_requests_day += sum(1 for req_time in client_data['requests'] if req_time >= day_ago)
            
            return {
                'total_clients': total_clients,
                'blocked_clients': blocked_clients,
                'active_clients': total_clients - blocked_clients,
                'total_requests': {
                    'minute': total_requests_minute,
                    'hour': total_requests_hour,
                    'day': total_requests_day
                },
                'system_limits': self.limits,
                'timestamp': current_time
            }

    def is_suspicious_activity(self, client_id: str) -> bool:
        """Detect potentially suspicious activity patterns"""
        
        with self.lock:
            client_data = self.clients[client_id]
            current_time = time.time()
            
            # Clean old requests
            self._clean_old_requests(client_data['requests'], current_time)
            
            # Check for burst patterns
            last_minute = current_time - 60
            recent_requests = [req_time for req_time in client_data['requests'] if req_time >= last_minute]
            
            if len(recent_requests) > 20:  # More than 20 requests in a minute
                return True
            
            # Check for regular high-frequency patterns
            if len(recent_requests) > 0:
                avg_interval = (recent_requests[-1] - recent_requests[0]) / len(recent_requests) if len(recent_requests) > 1 else 0
                if avg_interval < 2:  # Less than 2 seconds between requests
                    return True
            
            # Check violation count
            if client_data['violation_count'] >= 3:
                return True
            
            return False

    def add_whitelist(self, client_id: str):
        """Add a client to whitelist (bypass rate limiting)"""
        # This would be implemented for trusted clients
        # For now, we'll just reset their violations
        with self.lock:
            if client_id in self.clients:
                self.clients[client_id]['violation_count'] = 0
                self.clients[client_id]['blocked_until'] = 0

    def get_endpoint_specific_limits(self, endpoint_type: str) -> Dict[str, int]:
        """Get rate limits for a specific endpoint type"""
        return self.limits.get(endpoint_type, self.limits['default']).copy()
