"""
Web scraping automation engine using Selenium and Playwright
"""

import asyncio
import time
import random
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from playwright.async_api import async_playwright, Browser, Page
from bs4 import BeautifulSoup
import requests
from app.core.config import settings
from app.models.platform import Platform
from app.models.task import Task
from app.models.flight_data import FlightData
from app.core.database import SessionLocal
from app.utils.error_handler import with_retry, ScrapingError, ErrorType, error_handler
from loguru import logger


@dataclass
class ScrapingResult:
    """Result of a scraping operation"""
    success: bool
    data: List[Dict[str, Any]]
    error_message: Optional[str] = None
    screenshots: List[str] = None


class WebScraper:
    """Web scraping automation engine"""
    
    def __init__(self, platform: Platform, task: Task):
        self.platform = platform
        self.task = task
        self.driver = None
        self.browser = None
        self.page = None
        
    @with_retry(context="flight_scraping")
    async def scrape_flights(self) -> ScrapingResult:
        """Main method to scrape flight data"""
        try:
            logger.info(f"Starting flight scraping for {self.platform.name}")
            
            # Choose scraping method based on platform configuration
            if self.platform.name.lower() in ['expedia', 'kayak', 'skyscanner']:
                return await self._scrape_with_playwright()
            else:
                return await self._scrape_with_selenium()
                
        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            return ScrapingResult(
                success=False,
                data=[],
                error_message=str(e)
            )
        finally:
            await self._cleanup()
    
    async def _scrape_with_playwright(self) -> ScrapingResult:
        """Scrape using Playwright (better for modern SPAs)"""
        try:
            async with async_playwright() as p:
                # Launch browser
                self.browser = await p.chromium.launch(
                    headless=settings.SELENIUM_HEADLESS,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                
                # Create page
                self.page = await self.browser.new_page()
                
                # Set viewport
                await self.page.set_viewport_size({"width": 1920, "height": 1080})
                
                # Navigate to platform
                await self.page.goto(self.platform.base_url)
                
                # Wait for page to load
                await self.page.wait_for_load_state('networkidle')
                
                # Perform search
                await self._perform_search_playwright()
                
                # Extract flight data
                flights = await self._extract_flights_playwright()
                
                return ScrapingResult(
                    success=True,
                    data=flights,
                    screenshots=await self._take_screenshots()
                )
                
        except Exception as e:
            logger.error(f"Playwright scraping error: {str(e)}")
            return ScrapingResult(
                success=False,
                data=[],
                error_message=str(e)
            )
    
    async def _scrape_with_selenium(self) -> ScrapingResult:
        """Scrape using Selenium (better for traditional websites)"""
        try:
            # Setup Chrome options
            chrome_options = Options()
            if settings.SELENIUM_HEADLESS:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument(f'--window-size={settings.SELENIUM_WINDOW_SIZE}')
            
            # Create driver
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            
            # Navigate to platform
            self.driver.get(self.platform.base_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Perform search
            await self._perform_search_selenium()
            
            # Extract flight data
            flights = await self._extract_flights_selenium()
            
            return ScrapingResult(
                success=True,
                data=flights,
                screenshots=self._take_screenshots_selenium()
            )
            
        except Exception as e:
            logger.error(f"Selenium scraping error: {str(e)}")
            return ScrapingResult(
                success=False,
                data=[],
                error_message=str(e)
            )
    
    async def _perform_search_playwright(self):
        """Perform flight search using Playwright"""
        try:
            # Fill departure city
            departure_input = await self.page.wait_for_selector(
                'input[placeholder*="From"], input[placeholder*="Departure"], input[name*="from"]',
                timeout=10000
            )
            await departure_input.fill(self.task.departure_city)
            
            # Fill arrival city
            arrival_input = await self.page.wait_for_selector(
                'input[placeholder*="To"], input[placeholder*="Arrival"], input[name*="to"]',
                timeout=10000
            )
            await arrival_input.fill(self.task.arrival_city)
            
            # Fill travel date
            date_input = await self.page.wait_for_selector(
                'input[type="date"], input[placeholder*="Date"], input[name*="date"]',
                timeout=10000
            )
            await date_input.fill(self.task.travel_date.strftime('%Y-%m-%d'))
            
            # Fill number of travelers
            if self.task.num_travelers > 1:
                travelers_input = await self.page.wait_for_selector(
                    'input[name*="passengers"], input[name*="travelers"], select[name*="passengers"]',
                    timeout=5000
                )
                await travelers_input.fill(str(self.task.num_travelers))
            
            # Click search button
            search_button = await self.page.wait_for_selector(
                'button[type="submit"], input[type="submit"], button:has-text("Search"), button:has-text("Find")',
                timeout=10000
            )
            await search_button.click()
            
            # Wait for results to load
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)  # Additional wait for dynamic content
            
        except Exception as e:
            logger.error(f"Error performing search with Playwright: {str(e)}")
            raise
    
    async def _perform_search_selenium(self):
        """Perform flight search using Selenium"""
        try:
            # Fill departure city
            departure_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR, 
                    'input[placeholder*="From"], input[placeholder*="Departure"], input[name*="from"]'
                ))
            )
            departure_input.clear()
            departure_input.send_keys(self.task.departure_city)
            
            # Fill arrival city
            arrival_input = self.driver.find_element(
                By.CSS_SELECTOR,
                'input[placeholder*="To"], input[placeholder*="Arrival"], input[name*="to"]'
            )
            arrival_input.clear()
            arrival_input.send_keys(self.task.arrival_city)
            
            # Fill travel date
            date_input = self.driver.find_element(
                By.CSS_SELECTOR,
                'input[type="date"], input[placeholder*="Date"], input[name*="date"]'
            )
            date_input.clear()
            date_input.send_keys(self.task.travel_date.strftime('%Y-%m-%d'))
            
            # Fill number of travelers
            if self.task.num_travelers > 1:
                try:
                    travelers_input = self.driver.find_element(
                        By.CSS_SELECTOR,
                        'input[name*="passengers"], input[name*="travelers"], select[name*="passengers"]'
                    )
                    travelers_input.clear()
                    travelers_input.send_keys(str(self.task.num_travelers))
                except NoSuchElementException:
                    pass  # Optional field
            
            # Click search button
            search_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((
                    By.CSS_SELECTOR,
                    'button[type="submit"], input[type="submit"], button:has-text("Search"), button:has-text("Find")'
                ))
            )
            search_button.click()
            
            # Wait for results
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.flight-result, .flight-card, .result-item'))
            )
            
        except Exception as e:
            logger.error(f"Error performing search with Selenium: {str(e)}")
            raise
    
    async def _extract_flights_playwright(self) -> List[Dict[str, Any]]:
        """Extract flight data using Playwright"""
        flights = []
        
        try:
            # Wait for flight results
            await self.page.wait_for_selector(
                '.flight-result, .flight-card, .result-item, [data-testid*="flight"]',
                timeout=30000
            )
            
            # Get page content
            content = await self.page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract flight information
            flight_elements = soup.find_all(['div', 'article'], class_=lambda x: x and any(
                keyword in x.lower() for keyword in ['flight', 'result', 'card', 'item']
            ))
            
            for element in flight_elements[:20]:  # Limit to first 20 results
                flight_data = self._parse_flight_element(element)
                if flight_data:
                    flights.append(flight_data)
            
            logger.info(f"Extracted {len(flights)} flights from {self.platform.name}")
            
        except Exception as e:
            logger.error(f"Error extracting flights with Playwright: {str(e)}")
        
        return flights
    
    async def _extract_flights_selenium(self) -> List[Dict[str, Any]]:
        """Extract flight data using Selenium"""
        flights = []
        
        try:
            # Wait for flight results
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR, 
                    '.flight-result, .flight-card, .result-item, [data-testid*="flight"]'
                ))
            )
            
            # Get page source
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Extract flight information
            flight_elements = soup.find_all(['div', 'article'], class_=lambda x: x and any(
                keyword in x.lower() for keyword in ['flight', 'result', 'card', 'item']
            ))
            
            for element in flight_elements[:20]:  # Limit to first 20 results
                flight_data = self._parse_flight_element(element)
                if flight_data:
                    flights.append(flight_data)
            
            logger.info(f"Extracted {len(flights)} flights from {self.platform.name}")
            
        except Exception as e:
            logger.error(f"Error extracting flights with Selenium: {str(e)}")
        
        return flights
    
    def _parse_flight_element(self, element) -> Optional[Dict[str, Any]]:
        """Parse a flight element to extract data"""
        try:
            flight_data = {
                'airline': self._extract_airline(element),
                'flight_number': self._extract_flight_number(element),
                'departure_time': self._extract_departure_time(element),
                'arrival_time': self._extract_arrival_time(element),
                'price': self._extract_price(element),
                'stops': self._extract_stops(element),
                'duration': self._extract_duration(element),
                'source_platform': self.platform.name
            }
            
            # Only return if we have essential data
            if flight_data['price'] and flight_data['departure_time']:
                return flight_data
                
        except Exception as e:
            logger.error(f"Error parsing flight element: {str(e)}")
        
        return None
    
    def _extract_airline(self, element) -> Optional[str]:
        """Extract airline name from element"""
        # Try various selectors for airline
        selectors = [
            '.airline', '.carrier', '[data-testid*="airline"]',
            '.flight-airline', '.operator'
        ]
        
        for selector in selectors:
            airline_elem = element.select_one(selector)
            if airline_elem:
                return airline_elem.get_text(strip=True)
        
        return None
    
    def _extract_flight_number(self, element) -> Optional[str]:
        """Extract flight number from element"""
        selectors = [
            '.flight-number', '.flight-no', '[data-testid*="flight-number"]',
            '.flight-code'
        ]
        
        for selector in selectors:
            flight_elem = element.select_one(selector)
            if flight_elem:
                return flight_elem.get_text(strip=True)
        
        return None
    
    def _extract_departure_time(self, element) -> Optional[str]:
        """Extract departure time from element"""
        selectors = [
            '.departure-time', '.dep-time', '[data-testid*="departure"]',
            '.time-depart', '.from-time'
        ]
        
        for selector in selectors:
            time_elem = element.select_one(selector)
            if time_elem:
                return time_elem.get_text(strip=True)
        
        return None
    
    def _extract_arrival_time(self, element) -> Optional[str]:
        """Extract arrival time from element"""
        selectors = [
            '.arrival-time', '.arr-time', '[data-testid*="arrival"]',
            '.time-arrive', '.to-time'
        ]
        
        for selector in selectors:
            time_elem = element.select_one(selector)
            if time_elem:
                return time_elem.get_text(strip=True)
        
        return None
    
    def _extract_price(self, element) -> Optional[float]:
        """Extract price from element"""
        selectors = [
            '.price', '.cost', '.fare', '[data-testid*="price"]',
            '.flight-price', '.total-price'
        ]
        
        for selector in selectors:
            price_elem = element.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                # Extract numeric value
                import re
                price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                if price_match:
                    return float(price_match.group())
        
        return None
    
    def _extract_stops(self, element) -> int:
        """Extract number of stops from element"""
        selectors = [
            '.stops', '.stop-count', '[data-testid*="stop"]',
            '.connections', '.layover'
        ]
        
        for selector in selectors:
            stops_elem = element.select_one(selector)
            if stops_elem:
                stops_text = stops_elem.get_text(strip=True).lower()
                if 'nonstop' in stops_text or 'direct' in stops_text:
                    return 0
                elif '1 stop' in stops_text or '1 connection' in stops_text:
                    return 1
                elif '2 stop' in stops_text or '2 connection' in stops_text:
                    return 2
        
        return 0  # Default to nonstop
    
    def _extract_duration(self, element) -> Optional[str]:
        """Extract flight duration from element"""
        selectors = [
            '.duration', '.flight-time', '[data-testid*="duration"]',
            '.travel-time', '.time-total'
        ]
        
        for selector in selectors:
            duration_elem = element.select_one(selector)
            if duration_elem:
                return duration_elem.get_text(strip=True)
        
        return None
    
    async def _take_screenshots(self) -> List[str]:
        """Take screenshots for debugging"""
        screenshots = []
        try:
            if self.page:
                timestamp = int(time.time())
                screenshot_path = f"{settings.SCREENSHOTS_DIR}/playwright_{timestamp}.png"
                await self.page.screenshot(path=screenshot_path)
                screenshots.append(screenshot_path)
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
        
        return screenshots
    
    def _take_screenshots_selenium(self) -> List[str]:
        """Take screenshots using Selenium"""
        screenshots = []
        try:
            if self.driver:
                timestamp = int(time.time())
                screenshot_path = f"{settings.SCREENSHOTS_DIR}/selenium_{timestamp}.png"
                self.driver.save_screenshot(screenshot_path)
                screenshots.append(screenshot_path)
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
        
        return screenshots
    
    async def _cleanup(self):
        """Clean up resources"""
        try:
            if self.driver:
                self.driver.quit()
            if self.browser:
                await self.browser.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
