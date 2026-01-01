import aiohttp
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import random
import time
from tenacity import retry, stop_after_attempt, wait_exponential
from loguru import logger
import json
from typing import Optional, Dict, Any, List
import re
from datetime import datetime

class ScrapingUtils:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.ua = UserAgent()
        self.session = None
        self.async_session = None
        
    def get_user_agent(self) -> str:
        """Get random user agent"""
        if self.config.get('user_agent_rotation', True):
            return self.ua.random
        return self.config.get('user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers for requests"""
        return {
            'User-Agent': self.get_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def make_request(self, url: str, method: str = 'GET', **kwargs) -> Optional[requests.Response]:
        """Make HTTP request with retry logic"""
        try:
            if not self.session:
                self.session = requests.Session()
                self.session.headers.update(self.get_headers())
            
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise
    
    async def make_async_request(self, url: str, method: str = 'GET', **kwargs) -> Optional[aiohttp.ClientResponse]:
        """Make async HTTP request"""
        try:
            if not self.async_session:
                connector = aiohttp.TCPConnector(limit=self.config.get('max_concurrent_requests', 10))
                self.async_session = aiohttp.ClientSession(connector=connector, headers=self.get_headers())
            
            async with self.async_session.request(method, url, **kwargs) as response:
                response.raise_for_status()
                return response
        except Exception as e:
            logger.error(f"Async request failed: {e}")
            raise
    
    def parse_html(self, html_content: str) -> BeautifulSoup:
        """Parse HTML content"""
        return BeautifulSoup(html_content, 'html.parser')
    
    def extract_text(self, soup: BeautifulSoup, selector: str, default: str = '') -> str:
        """Extract text from HTML using CSS selector"""
        element = soup.select_one(selector)
        return element.get_text(strip=True) if element else default
    
    def extract_attribute(self, soup: BeautifulSoup, selector: str, attribute: str, default: str = '') -> str:
        """Extract attribute from HTML element"""
        element = soup.select_one(selector)
        return element.get(attribute, default) if element else default
    
    def extract_multiple(self, soup: BeautifulSoup, selector: str) -> List[str]:
        """Extract multiple elements matching selector"""
        elements = soup.select(selector)
        return [element.get_text(strip=True) for element in elements]
    
    def extract_links(self, soup: BeautifulSoup, selector: str) -> List[str]:
        """Extract links from HTML"""
        elements = soup.select(selector)
        return [element.get('href', '') for element in elements if element.get('href')]
    
    def extract_phone_numbers(self, text: str) -> List[str]:
        """Extract phone numbers from text"""
        phone_pattern = r'\+?\d[\d\s\-\(\)\.]{7,}\d'
        return list(set(re.findall(phone_pattern, text)))
    
    def extract_emails(self, text: str) -> List[str]:
        """Extract emails from text"""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return list(set(re.findall(email_pattern, text)))
    
    def normalize_phone_number(self, phone: str) -> str:
        """Normalize phone number"""
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # International format
        if len(digits) == 11 and digits.startswith('1'):
            return f"+1{digits[1:]}"
        elif len(digits) == 10:
            return f"+1{digits}"
        elif len(digits) > 7:
            return f"+{digits}"
        
        return phone
    
    def normalize_email(self, email: str) -> str:
        """Normalize email"""
        return email.strip().lower()
    
    def extract_location(self, text: str) -> Optional[str]:
        """Extract location from text"""
        # Simple location extraction - can be enhanced with NLP
        location_patterns = [
            r'\b(?:in|at|from)\s+([A-Za-z\s]+(?:,\s*[A-Z]{2})?(?:\s+\d{5})?)\b',
            r'\b([A-Za-z\s]+(?:,\s*[A-Z]{2})?)\b'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        return None
    
    def calculate_confidence_score(self, matches: int, total_fields: int, exact_match: bool = False) -> float:
        """Calculate confidence score"""
        base_score = matches / total_fields
        
        if exact_match:
            base_score *= 1.2
        
        return min(base_score, 1.0)
    
    def delay_request(self):
        """Add delay between requests"""
        delay = random.uniform(0.5, 2.0)
        time.sleep(delay)
    
    def close(self):
        """Close sessions"""
        if self.session:
            self.session.close()
        if self.async_session:
            self.async_session.close()

class AsyncScrapingUtils(ScrapingUtils):
    """Async version of scraping utilities"""
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def close(self):
        """Close async session"""
        if self.async_session:
            await self.async_session.close()
            self.async_session = None