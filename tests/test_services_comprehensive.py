#!/usr/bin/env python3
"""Comprehensive tests for services modules."""

import asyncio
import json
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from typing import Any, Dict, List, Optional

import pytest

# Import services modules
from services.auth_service import (
    AuthService,
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    get_current_user,
    require_auth,
    require_admin,
)
from services.background_workers import (
    BackgroundWorkerManager,
    TaskProcessor,
    WorkerPool,
    process_task,
    schedule_recurring_task,
    cleanup_completed_tasks,
)
from services.cost_tracking import (
    CostTracker,
    track_api_cost,
    get_cost_summary,
    calculate_monthly_cost,
    check_cost_limits,
)
from services.email_service import (
    EmailService,
    send_email,
    send_notification_email,
    send_welcome_email,
    validate_email_address,
)
from services.monitoring import (
    MetricsCollector,
    PerformanceMonitor,
    HealthChecker,
    collect_metrics,
    monitor_performance,
    check_health,
)
from services.notion.notion_client import (
    NotionClient,
    get_notion_client,
    create_page,
    update_page,
    query_database,
)
from services.performance import (
    PerformanceTracker,
    track_performance,
    get_performance_metrics,
    optimize_query,
)
from services.performance_monitor import (
    SystemMonitor,
    ApplicationMonitor,
    DatabaseMonitor,
    monitor_system,
    monitor_application,
    monitor_database,
)
from services.redis_cache import (
    RedisCache,
    get_redis_cache,
    cache_get,
    cache_set,
    cache_delete,
    cache_exists,
)
from services.stripe_service import (
    StripeService,
    create_customer,
    create_subscription,
    cancel_subscription,
    get_subscription_status,
)


class TestAuthService:
    """Test authentication service."""

    def test_hash_password(self) -> None:
        """Test password hashing."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 50  # bcrypt hash length
        assert hashed.startswith("$2b$")

    def test_verify_password_correct(self) -> None:
        """Test password verification with correct password."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self) -> None:
        """Test password verification with incorrect password."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False

    def test_create_access_token(self) -> None:
        """Test access token creation."""
        user_id = "user123"
        token = create_access_token(user_id)
        
        assert isinstance(token, str)
        assert len(token) > 50  # JWT token length

    def test_decode_access_token_valid(self) -> None:
        """Test decoding valid access token."""
        user_id = "user123"
        token = create_access_token(user_id)
        
        decoded = decode_access_token(token)
        assert decoded["user_id"] == user_id
        assert "exp" in decoded

    def test_decode_access_token_invalid(self) -> None:
        """Test decoding invalid access token."""
        invalid_token = "invalid.token.here"
        
        decoded = decode_access_token(invalid_token)
        assert decoded is None

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self) -> None:
        """Test getting current user with valid token."""
        with patch('services.auth_service.supabase_client') as mock_supabase:
            mock_supabase.table().select().eq().execute.return_value.data = [
                {"id": "user123", "email": "test@example.com"}
            ]
            
            user_id = "user123"
            token = create_access_token(user_id)
            
            user = await get_current_user(token)
            assert user["id"] == user_id

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self) -> None:
        """Test getting current user with invalid token."""
        invalid_token = "invalid.token.here"
        
        user = await get_current_user(invalid_token)
        assert user is None

    def test_auth_service_init(self) -> None:
        """Test AuthService initialization."""
        service = AuthService()
        assert hasattr(service, 'supabase_client')

    @pytest.mark.asyncio
    async def test_require_auth_valid(self) -> None:
        """Test require_auth decorator with valid token."""
        mock_request = Mock()
        mock_request.headers = {"Authorization": "Bearer valid_token"}
        
        with patch('services.auth_service.get_current_user') as mock_get_user:
            mock_get_user.return_value = {"id": "user123", "role": "user"}
            
            @require_auth
            async def test_endpoint(request):
    pass
                return {"message": "success"}
            
            result = await test_endpoint(mock_request)
            assert result["message"] == "success"

    @pytest.mark.asyncio
    async def test_require_admin_valid(self) -> None:
        """Test require_admin decorator with admin user."""
        mock_request = Mock()
        mock_request.headers = {"Authorization": "Bearer admin_token"}
        
        with patch('services.auth_service.get_current_user') as mock_get_user:
            mock_get_user.return_value = {"id": "admin123", "role": "admin"}
            
            @require_admin
            async def test_endpoint(request):
    pass
                return {"message": "admin_success"}
            
            result = await test_endpoint(mock_request)
            assert result["message"] == "admin_success"


class TestBackgroundWorkers:
    """Test background workers."""

    def test_task_processor_init(self) -> None:
        """Test TaskProcessor initialization."""
        processor = TaskProcessor()
        assert hasattr(processor, 'queue')
        assert hasattr(processor, 'workers')

    @pytest.mark.asyncio
    async def test_process_task_success(self) -> None:
        """Test processing task successfully."""
        task = {
            "id": "task123",
            "type": "email",
            "data": {"to": "test@example.com", "subject": "Test"}
        }
        
        result = await process_task(task)
        assert result["status"] == "completed"
        assert result["task_id"] == "task123"

    @pytest.mark.asyncio
    async def test_process_task_failure(self) -> None:
        """Test processing task with failure."""
        invalid_task = {
            "id": "task456",
            "type": "invalid_type",
            "data": {}
        }
        
        result = await process_task(invalid_task)
        assert result["status"] == "failed"
        assert "error" in result

    def test_worker_pool_init(self) -> None:
        """Test WorkerPool initialization."""
        pool = WorkerPool(max_workers=5)
        assert pool.max_workers == 5
        assert len(pool.workers) == 0

    @pytest.mark.asyncio
    async def test_schedule_recurring_task(self) -> None:
        """Test scheduling recurring task."""
        task_data = {
            "type": "cleanup",
            "interval": 3600,  # 1 hour
            "data": {"table": "logs"}
        }
        
        task_id = await schedule_recurring_task(task_data)
        assert isinstance(task_id, str)
        assert len(task_id) > 10

    @pytest.mark.asyncio
    async def test_cleanup_completed_tasks(self) -> None:
        """Test cleaning up completed tasks."""
        with patch('services.background_workers.redis_client') as mock_redis:
            mock_redis.scan_iter.return_value = ["task:123", "task:456"]
            mock_redis.get.side_effect = [
                json.dumps({"status": "completed", "completed_at": "2023-01-01T00:00:00"}),
                json.dumps({"status": "running"})
            ]
            
            cleaned_count = await cleanup_completed_tasks()
            assert cleaned_count >= 0

    def test_background_worker_manager_init(self) -> None:
        """Test BackgroundWorkerManager initialization."""
        manager = BackgroundWorkerManager()
        assert hasattr(manager, 'task_processor')
        assert hasattr(manager, 'worker_pool')


class TestCostTracking:
    """Test cost tracking service."""

    def test_cost_tracker_init(self) -> None:
        """Test CostTracker initialization."""
        tracker = CostTracker()
        assert hasattr(tracker, 'daily_costs')
        assert hasattr(tracker, 'monthly_limits')

    @pytest.mark.asyncio
    async def test_track_api_cost(self) -> None:
        """Test tracking API cost."""
        cost_data = {
            "service": "openai",
            "operation": "completion",
            "cost": 0.002,
            "tokens": 1000,
            "user_id": "user123"
        }
        
        result = await track_api_cost(cost_data)
        assert result["status"] == "tracked"
        assert result["cost"] == 0.002

    @pytest.mark.asyncio
    async def test_get_cost_summary(self) -> None:
        """Test getting cost summary."""
        user_id = "user123"
        period = "daily"
        
        with patch('services.cost_tracking.redis_client') as mock_redis:
            mock_redis.get.return_value = json.dumps({
                "total_cost": 0.15,
                "operations": 75,
                "services": {"openai": 0.12, "anthropic": 0.03}
            })
            
            summary = await get_cost_summary(user_id, period)
            assert summary["total_cost"] == 0.15
            assert summary["operations"] == 75

    @pytest.mark.asyncio
    async def test_calculate_monthly_cost(self) -> None:
        """Test calculating monthly cost."""
        user_id = "user123"
        
        with patch('services.cost_tracking.supabase_client') as mock_supabase:
            mock_supabase.table().select().gte().lte().eq().execute.return_value.data = [
                {"cost": 0.05, "created_at": "2023-01-15T10:00:00"},
                {"cost": 0.03, "created_at": "2023-01-20T14:00:00"}
            ]
            
            monthly_cost = await calculate_monthly_cost(user_id)
            assert monthly_cost >= 0.08

    @pytest.mark.asyncio
    async def test_check_cost_limits(self) -> None:
        """Test checking cost limits."""
        user_id = "user123"
        current_cost = 45.50
        
        result = await check_cost_limits(user_id, current_cost)
        assert "within_limits" in result
        assert "limit_percentage" in result


class TestEmailService:
    """Test email service."""

    def test_email_service_init(self) -> None:
        """Test EmailService initialization."""
        service = EmailService()
        assert hasattr(service, 'smtp_server')
        assert hasattr(service, 'smtp_port')

    def test_validate_email_address_valid(self) -> None:
        """Test validating valid email address."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org"
        ]
        
        for email in valid_emails:
            assert validate_email_address(email) is True

    def test_validate_email_address_invalid(self) -> None:
        """Test validating invalid email address."""
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "user@",
            "user..name@example.com",
            ""
        ]
        
        for email in invalid_emails:
            assert validate_email_address(email) is False

    @pytest.mark.asyncio
    async def test_send_email_success(self) -> None:
        """Test sending email successfully."""
        email_data = {
            "to": "test@example.com",
            "subject": "Test Subject",
            "body": "Test body content",
            "html": "<p>Test HTML content</p>"
        }
        
        with patch('services.email_service.smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            result = await send_email(email_data)
            assert result["status"] == "sent"
            assert result["to"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_send_notification_email(self) -> None:
        """Test sending notification email."""
        user_id = "user123"
        notification_type = "task_completed"
        data = {"task_name": "Data Analysis", "completed_at": "2023-01-15T10:00:00"}
        
        with patch('services.email_service.send_email') as mock_send:
            mock_send.return_value = {"status": "sent"}
            
            result = await send_notification_email(user_id, notification_type, data)
            assert result["status"] == "sent"

    @pytest.mark.asyncio
    async def test_send_welcome_email(self) -> None:
        """Test sending welcome email."""
        user_data = {
            "email": "newuser@example.com",
            "name": "New User",
            "id": "user456"
        }
        
        with patch('services.email_service.send_email') as mock_send:
            mock_send.return_value = {"status": "sent"}
            
            result = await send_welcome_email(user_data)
            assert result["status"] == "sent"


class TestMonitoring:
    """Test monitoring services."""

    def test_metrics_collector_init(self) -> None:
        """Test MetricsCollector initialization."""
        collector = MetricsCollector()
        assert hasattr(collector, 'metrics')
        assert hasattr(collector, 'counters')

    @pytest.mark.asyncio
    async def test_collect_metrics(self) -> None:
        """Test collecting metrics."""
        metric_type = "api_request"
        metric_data = {
            "endpoint": "/api/users",
            "method": "GET",
            "status_code": 200,
            "response_time": 0.15
        }
        
        result = await collect_metrics(metric_type, metric_data)
        assert result["status"] == "collected"
        assert result["metric_type"] == metric_type

    def test_performance_monitor_init(self) -> None:
        """Test PerformanceMonitor initialization."""
        monitor = PerformanceMonitor()
        assert hasattr(monitor, 'start_time')
        assert hasattr(monitor, 'metrics')

    @pytest.mark.asyncio
    async def test_monitor_performance(self) -> None:
        """Test monitoring performance."""
        operation_name = "database_query"
        
        with patch('services.monitoring.time.time') as mock_time:
            mock_time.side_effect = [1000.0, 1000.15]  # 150ms operation
            
            async with monitor_performance(operation_name):
                await asyncio.sleep(0.01)  # Simulate work
            
            # Performance should be tracked
            assert True  # Test passes if no exception

    def test_health_checker_init(self) -> None:
        """Test HealthChecker initialization."""
        checker = HealthChecker()
        assert hasattr(checker, 'checks')
        assert hasattr(checker, 'status')

    @pytest.mark.asyncio
    async def test_check_health(self) -> None:
        """Test health checking."""
        service_name = "database"
        
        with patch('services.monitoring.ping_service') as mock_ping:
            mock_ping.return_value = True
            
            health_status = await check_health(service_name)
            assert health_status["status"] in ["healthy", "unhealthy"]
            assert health_status["service"] == service_name


class TestNotionClient:
    """Test Notion client."""

    def test_notion_client_init(self) -> None:
        """Test NotionClient initialization."""
        with patch.dict('os.environ', {'NOTION_API_KEY': 'test_key'}):
            client = NotionClient()
            assert hasattr(client, 'api_key')

    @pytest.mark.asyncio
    async def test_get_notion_client(self) -> None:
        """Test getting Notion client."""
        with patch.dict('os.environ', {'NOTION_API_KEY': 'test_key'}):
            client = await get_notion_client()
            assert isinstance(client, NotionClient)

    @pytest.mark.asyncio
    async def test_create_page(self) -> None:
        """Test creating Notion page."""
        page_data = {
            "parent": {"database_id": "db123"},
            "properties": {
                "Name": {"title": [{"text": {"content": "Test Page"}}]}
            }
        }
        
        with patch('services.notion.notion_client.httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": "page123", "url": "https://notion.so/page123"}
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            result = await create_page(page_data)
            assert result["id"] == "page123"

    @pytest.mark.asyncio
    async def test_update_page(self) -> None:
        """Test updating Notion page."""
        page_id = "page123"
        update_data = {
            "properties": {
                "Status": {"select": {"name": "Completed"}}
            }
        }
        
        with patch('services.notion.notion_client.httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": "page123", "last_edited_time": "2023-01-15T10:00:00"}
            mock_client.return_value.__aenter__.return_value.patch.return_value = mock_response
            
            result = await update_page(page_id, update_data)
            assert result["id"] == "page123"

    @pytest.mark.asyncio
    async def test_query_database(self) -> None:
        """Test querying Notion database."""
        database_id = "db123"
        query_data = {
            "filter": {
                "property": "Status",
                "select": {"equals": "Active"}
            }
        }
        
        with patch('services.notion.notion_client.httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "results": [{"id": "page1"}, {"id": "page2"}],
                "has_more": False
            }
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            result = await query_database(database_id, query_data)
            assert len(result["results"]) == 2


class TestPerformance:
    """Test performance tracking."""

    def test_performance_tracker_init(self) -> None:
        """Test PerformanceTracker initialization."""
        tracker = PerformanceTracker()
        assert hasattr(tracker, 'metrics')
        assert hasattr(tracker, 'thresholds')

    @pytest.mark.asyncio
    async def test_track_performance(self) -> None:
        """Test tracking performance."""
        operation = "api_call"
        duration = 0.25
        metadata = {"endpoint": "/api/users", "method": "GET"}
        
        result = await track_performance(operation, duration, metadata)
        assert result["operation"] == operation
        assert result["duration"] == duration

    @pytest.mark.asyncio
    async def test_get_performance_metrics(self) -> None:
        """Test getting performance metrics."""
        operation = "database_query"
        time_range = "1h"
        
        with patch('services.performance.redis_client') as mock_redis:
            mock_redis.zrange.return_value = [
                json.dumps({"duration": 0.1, "timestamp": 1640995200}),
                json.dumps({"duration": 0.15, "timestamp": 1640995260})
            ]
            
            metrics = await get_performance_metrics(operation, time_range)
            assert "average_duration" in metrics
            assert "total_operations" in metrics

    @pytest.mark.asyncio
    async def test_optimize_query(self) -> None:
        """Test query optimization."""
        query = "SELECT * FROM users WHERE active = true"
        
        optimized = await optimize_query(query)
        assert "optimized_query" in optimized
        assert "suggestions" in optimized


class TestRedisCache:
    """Test Redis cache."""

    def test_redis_cache_init(self) -> None:
        """Test RedisCache initialization."""
        cache = RedisCache()
        assert hasattr(cache, 'client')

    @pytest.mark.asyncio
    async def test_get_redis_cache(self) -> None:
        """Test getting Redis cache instance."""
        cache = await get_redis_cache()
        assert isinstance(cache, RedisCache)

    @pytest.mark.asyncio
    async def test_cache_set_get(self) -> None:
        """Test setting and getting cache value."""
        key = "test_key"
        value = {"data": "test_value", "timestamp": time.time()}
        ttl = 3600
        
        with patch('services.redis_cache.redis_client') as mock_redis:
            mock_redis.setex.return_value = True
            mock_redis.get.return_value = json.dumps(value)
            
            # Test set
            result = await cache_set(key, value, ttl)
            assert result is True
            
            # Test get
            cached_value = await cache_get(key)
            assert cached_value["data"] == "test_value"

    @pytest.mark.asyncio
    async def test_cache_delete(self) -> None:
        """Test deleting cache value."""
        key = "test_key"
        
        with patch('services.redis_cache.redis_client') as mock_redis:
            mock_redis.delete.return_value = 1
            
            result = await cache_delete(key)
            assert result is True

    @pytest.mark.asyncio
    async def test_cache_exists(self) -> None:
        """Test checking if cache key exists."""
        key = "test_key"
        
        with patch('services.redis_cache.redis_client') as mock_redis:
            mock_redis.exists.return_value = 1
            
            exists = await cache_exists(key)
            assert exists is True


class TestStripeService:
    """Test Stripe service."""

    def test_stripe_service_init(self) -> None:
        """Test StripeService initialization."""
        with patch.dict('os.environ', {'STRIPE_SECRET_KEY': 'sk_test_123'}):
            service = StripeService()
            assert hasattr(service, 'api_key')

    @pytest.mark.asyncio
    async def test_create_customer(self) -> None:
        """Test creating Stripe customer."""
        customer_data = {
            "email": "customer@example.com",
            "name": "Test Customer",
            "metadata": {"user_id": "user123"}
        }
        
        with patch('services.stripe_service.stripe.Customer.create') as mock_create:
            mock_create.return_value = {
                "id": "cus_123",
                "email": "customer@example.com",
                "created": 1640995200
            }
            
            customer = await create_customer(customer_data)
            assert customer["id"] == "cus_123"
            assert customer["email"] == "customer@example.com"

    @pytest.mark.asyncio
    async def test_create_subscription(self) -> None:
        """Test creating Stripe subscription."""
        subscription_data = {
            "customer": "cus_123",
            "price": "price_456",
            "metadata": {"user_id": "user123"}
        }
        
        with patch('services.stripe_service.stripe.Subscription.create') as mock_create:
            mock_create.return_value = {
                "id": "sub_789",
                "status": "active",
                "current_period_start": 1640995200,
                "current_period_end": 1643673600
            }
            
            subscription = await create_subscription(subscription_data)
            assert subscription["id"] == "sub_789"
            assert subscription["status"] == "active"

    @pytest.mark.asyncio
    async def test_cancel_subscription(self) -> None:
        """Test canceling Stripe subscription."""
        subscription_id = "sub_789"
        
        with patch('services.stripe_service.stripe.Subscription.modify') as mock_modify:
            mock_modify.return_value = {
                "id": "sub_789",
                "status": "canceled",
                "canceled_at": 1641081600
            }
            
            result = await cancel_subscription(subscription_id)
            assert result["status"] == "canceled"

    @pytest.mark.asyncio
    async def test_get_subscription_status(self) -> None:
        """Test getting subscription status."""
        subscription_id = "sub_789"
        
        with patch('services.stripe_service.stripe.Subscription.retrieve') as mock_retrieve:
            mock_retrieve.return_value = {
                "id": "sub_789",
                "status": "active",
                "current_period_end": 1643673600
            }
            
            status = await get_subscription_status(subscription_id)
            assert status["status"] == "active"


class TestServicesIntegration:
    """Test services integration."""

    @pytest.mark.asyncio
    async def test_auth_and_cost_tracking_integration(self) -> None:
        """Test integration between auth and cost tracking."""
        user_id = "user123"
        token = create_access_token(user_id)
        
        # Simulate API call with cost tracking
        cost_data = {
            "service": "openai",
            "operation": "completion",
            "cost": 0.005,
            "user_id": user_id
        }
        
        with patch('services.cost_tracking.redis_client'):
            cost_result = await track_api_cost(cost_data)
            assert cost_result["status"] == "tracked"

    @pytest.mark.asyncio
    async def test_monitoring_and_performance_integration(self) -> None:
        """Test integration between monitoring and performance tracking."""
        operation_name = "api_request"
        
        # Simulate monitored operation
        start_time = time.time()
        await asyncio.sleep(0.01)  # Simulate work
        duration = time.time() - start_time
        
        with patch('services.performance.redis_client'):
            perf_result = await track_performance(operation_name, duration)
            assert perf_result["operation"] == operation_name

    @pytest.mark.asyncio
    async def test_email_and_notification_integration(self) -> None:
        """Test integration between email service and notifications."""
        user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "id": "user123"
        }
        
        with patch('services.email_service.send_email') as mock_send:
            mock_send.return_value = {"status": "sent"}
            
            # Test welcome email
            welcome_result = await send_welcome_email(user_data)
            assert welcome_result["status"] == "sent"
            
            # Test notification email
            notification_result = await send_notification_email(
                user_data["id"], "task_completed", {"task": "Test Task"}
            )
            assert notification_result["status"] == "sent"


class TestServicesErrorHandling:
    """Test services error handling."""

    @pytest.mark.asyncio
    async def test_auth_service_error_handling(self) -> None:
        """Test auth service error handling."""
        # Test with invalid token
        invalid_token = "invalid.token.here"
        user = await get_current_user(invalid_token)
        assert user is None

    @pytest.mark.asyncio
    async def test_cost_tracking_error_handling(self) -> None:
        """Test cost tracking error handling."""
        invalid_cost_data = {
            "service": "",  # Invalid empty service
            "cost": -1,     # Invalid negative cost
        }
        
        with patch('services.cost_tracking.redis_client') as mock_redis:
            mock_redis.setex.side_effect = Exception("Redis error")
            
            result = await track_api_cost(invalid_cost_data)
            assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_email_service_error_handling(self) -> None:
        """Test email service error handling."""
        invalid_email_data = {
            "to": "invalid-email",  # Invalid email format
            "subject": "",          # Empty subject
            "body": ""              # Empty body
        }
        
        result = await send_email(invalid_email_data)
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_stripe_service_error_handling(self) -> None:
        """Test Stripe service error handling."""
        with patch('services.stripe_service.stripe.Customer.create') as mock_create:
            mock_create.side_effect = Exception("Stripe API error")
            
            result = await create_customer({"email": "test@example.com"})
            assert result["status"] == "error"


class TestServicesPerformance:
    """Test services performance characteristics."""

    @pytest.mark.asyncio
    async def test_cache_performance(self) -> None:
        """Test cache performance."""
        key = "performance_test"
        value = {"data": "test" * 1000}  # Larger payload
        
        with patch('services.redis_cache.redis_client') as mock_redis:
            mock_redis.setex.return_value = True
            mock_redis.get.return_value = json.dumps(value)
            
            # Test multiple cache operations
            start_time = time.time()
            for i in range(10):
                await cache_set(f"{key}_{i}", value, 3600)
                await cache_get(f"{key}_{i}")
            duration = time.time() - start_time
            
            # Should complete quickly (less than 1 second for 20 operations)
            assert duration < 1.0

    @pytest.mark.asyncio
    async def test_background_worker_performance(self) -> None:
        """Test background worker performance."""
        tasks = []
        for i in range(5):
            tasks.append({
                "id": f"task_{i}",
                "type": "email",
                "data": {"to": f"test{i}@example.com"}
            })
        
        start_time = time.time()
        results = []
        for task in tasks:
            result = await process_task(task)
            results.append(result)
        duration = time.time() - start_time
        
        # Should process all tasks quickly
        assert len(results) == 5
        assert duration < 1.0
