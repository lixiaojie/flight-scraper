"""
Tests for automation engine
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from app.automation.web_scraper import WebScraper, ScrapingResult
from app.models.platform import Platform, PlatformType
from app.models.task import Task, TaskStatus
from app.utils.error_handler import ErrorType, ScrapingError


@pytest.fixture
def sample_platform():
    """Create a sample platform for testing"""
    return Platform(
        id=1,
        name='test_platform',
        display_name='Test Platform',
        platform_type=PlatformType.WEB,
        base_url='https://test.com',
        is_active=True
    )


@pytest.fixture
def sample_task():
    """Create a sample task for testing"""
    from datetime import datetime, timedelta
    return Task(
        id=1,
        name='Test Task',
        departure_city='New York',
        arrival_city='Los Angeles',
        travel_date=datetime.utcnow() + timedelta(days=30),
        num_travelers=1,
        cabin_class='economy',
        status=TaskStatus.PENDING
    )


@pytest.fixture
def web_scraper(sample_platform, sample_task):
    """Create a WebScraper instance for testing"""
    return WebScraper(sample_platform, sample_task)


class TestWebScraper:
    """Test cases for WebScraper class"""
    
    @pytest.mark.asyncio
    async def test_scrape_flights_success(self, web_scraper):
        """Test successful flight scraping"""
        with patch.object(web_scraper, '_scrape_with_playwright') as mock_scrape:
            mock_scrape.return_value = ScrapingResult(
                success=True,
                data=[
                    {
                        'airline': 'Test Airline',
                        'flight_number': 'TA123',
                        'departure_time': '10:00',
                        'arrival_time': '14:00',
                        'price': 299.99,
                        'stops': 0
                    }
                ]
            )
            
            result = await web_scraper.scrape_flights()
            
            assert result.success is True
            assert len(result.data) == 1
            assert result.data[0]['airline'] == 'Test Airline'
            assert result.data[0]['price'] == 299.99
    
    @pytest.mark.asyncio
    async def test_scrape_flights_failure(self, web_scraper):
        """Test flight scraping failure"""
        with patch.object(web_scraper, '_scrape_with_playwright') as mock_scrape:
            mock_scrape.return_value = ScrapingResult(
                success=False,
                data=[],
                error_message='Connection timeout'
            )
            
            result = await web_scraper.scrape_flights()
            
            assert result.success is False
            assert len(result.data) == 0
            assert result.error_message == 'Connection timeout'
    
    @pytest.mark.asyncio
    async def test_cleanup_resources(self, web_scraper):
        """Test resource cleanup"""
        # Mock driver and browser
        web_scraper.driver = Mock()
        web_scraper.browser = AsyncMock()
        
        await web_scraper._cleanup()
        
        # Verify cleanup was called
        web_scraper.driver.quit.assert_called_once()
        web_scraper.browser.close.assert_called_once()
    
    def test_parse_flight_element_valid(self, web_scraper):
        """Test parsing valid flight element"""
        from bs4 import BeautifulSoup
        
        html = """
        <div class="flight-result">
            <div class="airline">Test Airline</div>
            <div class="flight-number">TA123</div>
            <div class="departure-time">10:00</div>
            <div class="arrival-time">14:00</div>
            <div class="price">$299.99</div>
            <div class="stops">Nonstop</div>
        </div>
        """
        
        soup = BeautifulSoup(html, 'html.parser')
        element = soup.find('div', class_='flight-result')
        
        result = web_scraper._parse_flight_element(element)
        
        assert result is not None
        assert result['airline'] == 'Test Airline'
        assert result['flight_number'] == 'TA123'
        assert result['price'] == 299.99
        assert result['stops'] == 0
    
    def test_parse_flight_element_invalid(self, web_scraper):
        """Test parsing invalid flight element"""
        from bs4 import BeautifulSoup
        
        html = """
        <div class="flight-result">
            <div class="airline">Test Airline</div>
            <!-- Missing price and times -->
        </div>
        """
        
        soup = BeautifulSoup(html, 'html.parser')
        element = soup.find('div', class_='flight-result')
        
        result = web_scraper._parse_flight_element(element)
        
        assert result is None  # Should return None for invalid data
    
    def test_extract_price_various_formats(self, web_scraper):
        """Test price extraction from various formats"""
        test_cases = [
            ('$299.99', 299.99),
            ('299.99', 299.99),
            ('$1,299.99', 1299.99),
            ('Free', None),
            ('', None),
            ('Invalid', None)
        ]
        
        for price_text, expected in test_cases:
            # Create mock element with price
            from bs4 import BeautifulSoup
            html = f'<div class="price">{price_text}</div>'
            soup = BeautifulSoup(html, 'html.parser')
            element = soup.find('div', class_='price')
            
            result = web_scraper._extract_price(element)
            assert result == expected, f"Failed for price text: {price_text}"
    
    def test_extract_stops_various_formats(self, web_scraper):
        """Test stops extraction from various formats"""
        test_cases = [
            ('Nonstop', 0),
            ('Direct', 0),
            ('1 stop', 1),
            ('2 stops', 2),
            ('1 connection', 1),
            ('2 connections', 2),
            ('', 0)
        ]
        
        for stops_text, expected in test_cases:
            # Create mock element with stops
            from bs4 import BeautifulSoup
            html = f'<div class="stops">{stops_text}</div>'
            soup = BeautifulSoup(html, 'html.parser')
            element = soup.find('div', class_='stops')
            
            result = web_scraper._extract_stops(element)
            assert result == expected, f"Failed for stops text: {stops_text}"


class TestErrorHandling:
    """Test cases for error handling"""
    
    def test_error_classification(self):
        """Test error classification"""
        from app.utils.error_handler import ErrorHandler
        
        handler = ErrorHandler()
        
        # Test network error
        network_error = Exception("Connection timeout")
        assert handler.classify_error(network_error) == ErrorType.NETWORK_ERROR
        
        # Test rate limit error
        rate_limit_error = Exception("Rate limit exceeded")
        assert handler.classify_error(rate_limit_error) == ErrorType.RATE_LIMIT_ERROR
        
        # Test unknown error
        unknown_error = Exception("Some random error")
        assert handler.classify_error(unknown_error) == ErrorType.UNKNOWN_ERROR
    
    def test_retry_logic(self):
        """Test retry logic"""
        from app.utils.error_handler import ErrorHandler, RetryConfig
        
        config = RetryConfig(max_retries=2, base_delay=0.1)
        handler = ErrorHandler(config)
        
        call_count = 0
        
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Network error")
            return "success"
        
        result = handler.retry_with_backoff(failing_function, context="test")
        
        assert result == "success"
        assert call_count == 3  # Initial call + 2 retries
    
    def test_should_retry(self):
        """Test retry decision logic"""
        from app.utils.error_handler import ErrorHandler, RetryConfig
        
        config = RetryConfig(retryable_errors=[ErrorType.NETWORK_ERROR])
        handler = ErrorHandler(config)
        
        # Should retry network error
        network_error = Exception("Connection timeout")
        assert handler.should_retry(network_error) is True
        
        # Should not retry parsing error
        parsing_error = Exception("JSON parse error")
        assert handler.should_retry(parsing_error) is False


class TestDataProcessing:
    """Test cases for data processing"""
    
    def test_price_cleaning(self):
        """Test price cleaning functionality"""
        from app.services.data_processor import DataProcessor
        from unittest.mock import Mock
        
        db = Mock()
        processor = DataProcessor(db)
        
        test_cases = [
            (299.99, 299.99),
            ("$299.99", 299.99),
            ("$1,299.99", 1299.99),
            ("Free", None),
            ("", None),
            (None, None)
        ]
        
        for input_price, expected in test_cases:
            result = processor._clean_price(input_price)
            assert result == expected, f"Failed for input: {input_price}"
    
    def test_airline_name_cleaning(self):
        """Test airline name cleaning"""
        from app.services.data_processor import DataProcessor
        from unittest.mock import Mock
        
        db = Mock()
        processor = DataProcessor(db)
        
        test_cases = [
            ("United Airlines", "United Airlines"),
            ("united", "United Airlines"),
            ("Delta Air Lines Inc.", "Delta Air Lines"),
            ("", None),
            (None, None)
        ]
        
        for input_airline, expected in test_cases:
            result = processor._clean_airline_name(input_airline)
            assert result == expected, f"Failed for input: {input_airline}"
    
    def test_flight_number_cleaning(self):
        """Test flight number cleaning"""
        from app.services.data_processor import DataProcessor
        from unittest.mock import Mock
        
        db = Mock()
        processor = DataProcessor(db)
        
        test_cases = [
            ("UA123", "UA123"),
            ("Flight UA123", "UA123"),
            ("FL UA123", "UA123"),
            ("", None),
            (None, None)
        ]
        
        for input_flight, expected in test_cases:
            result = processor._clean_flight_number(input_flight)
            assert result == expected, f"Failed for input: {input_flight}"


if __name__ == "__main__":
    pytest.main([__file__])
