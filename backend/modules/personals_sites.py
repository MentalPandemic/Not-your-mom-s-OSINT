import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger
from bs4 import BeautifulSoup
import aiohttp
from fake_useragent import UserAgent
from tenacity import retry, stop_after_attempt, wait_exponential
import re

from backend.models.database import PersonalsPost, Identity, Attribute, Content, AsyncSessionLocal
from backend.utils.scraping_utils import ScrapingUtils, AsyncScrapingUtils
from backend.config.adult_personals_sources import personals_sites_config

class PersonalsSiteScraper:
    """Personals/Classified sites scraping module"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or personals_sites_config
        self.scraping_utils = ScrapingUtils(self.config.get('general_settings', {}))
        self.async_scraping_utils = AsyncScrapingUtils(self.config.get('general_settings', {}))
        self.ua = UserAgent()
    
    async def search_personals_sites(self, target: str, sites: Optional[List[str]] = None) -> List[Dict]:
        """Search for target across personals platforms"""
        if sites is None:
            sites = list(self.config['personals_sites'].keys())
        
        results = []
        tasks = []
        
        for site in sites:
            if site in self.config['personals_sites']:
                task = asyncio.create_task(self._search_site(site, target))
                tasks.append(task)
        
        # Run tasks concurrently with rate limiting
        for task in asyncio.as_completed(tasks):
            try:
                result = await task
                if result:
                    results.extend(result)
            except Exception as e:
                logger.error(f"Error searching {site}: {e}")
        
        return results
    
    async def _search_site(self, site: str, target: str) -> List[Dict]:
        """Search specific personals site"""
        site_config = self.config['personals_sites'][site]
        results = []
        
        try:
            # Build search URL
            search_url = site_config['base_url'] + site_config['search_endpoint'].replace('{location}', target)
            
            logger.info(f"Searching {site} for {target}: {search_url}")
            
            # Make async request
            response = await self.async_scraping_utils.make_async_request(search_url)
            if response:
                html = await response.text()
                soup = self.scraping_utils.parse_html(html)
                
                # Extract post data
                post_data_list = self._extract_post_data(soup, site_config, target)
                
                for post_data in post_data_list:
                    if post_data:
                        # Calculate confidence score
                        confidence_score = self._calculate_confidence_score(post_data, target)
                        post_data['confidence_score'] = confidence_score
                        post_data['site'] = site
                        post_data['scraped_at'] = datetime.utcnow().isoformat()
                        
                        results.append(post_data)
                        
                        # Store in database
                        await self._store_post_data(post_data)
        
        except Exception as e:
            logger.error(f"Error searching {site}: {e}")
        
        return results
    
    def _extract_post_data(self, soup: BeautifulSoup, site_config: Dict, target: str) -> List[Dict]:
        """Extract post data from HTML"""
        selectors = site_config['selectors']
        post_data_list = []
        
        # Find all post containers - this would need to be customized per site
        # For now, we'll assume we can find individual posts
        posts = soup.find_all('div', class_='post')  # This selector would be site-specific
        
        for post in posts:
            post_data = {}
            
            # Extract post title
            post_data['post_title'] = self.scraping_utils.extract_text(post, selectors['post_title'])
            
            # Extract post content
            post_data['post_content'] = self.scraping_utils.extract_text(post, selectors['post_content'])
            
            # Extract contact info
            post_data['phone_number'] = self.scraping_utils.extract_text(post, selectors['phone_number'])
            post_data['email'] = self.scraping_utils.extract_text(post, selectors['email'])
            
            # Extract location
            post_data['location'] = self.scraping_utils.extract_text(post, selectors['location'])
            
            # Extract post date
            post_date_str = self.scraping_utils.extract_text(post, selectors['post_date'])
            try:
                post_data['post_date'] = datetime.strptime(post_date_str, '%Y-%m-%d').isoformat() if post_date_str else None
            except:
                post_data['post_date'] = None
            
            # Extract images
            image_urls = self.scraping_utils.extract_links(post, selectors['images'])
            post_data['image_urls'] = image_urls
            
            # Extract post ID from URL or other identifier
            post_data['post_id'] = self._generate_post_id(post_data, site_config['base_url'])
            
            post_data_list.append(post_data)
        
        return post_data_list
    
    def _generate_post_id(self, post_data: Dict, base_url: str) -> str:
        """Generate unique post ID"""
        # This would be site-specific - for now use a hash of title + content
        import hashlib
        unique_str = f"{post_data['post_title']}{post_data['post_content']}"
        return hashlib.md5(unique_str.encode()).hexdigest()
    
    def _calculate_confidence_score(self, post_data: Dict, target: str) -> float:
        """Calculate confidence score for post match"""
        matches = 0
        total_fields = 4
        
        # Check if target appears in title
        if post_data['post_title'] and target.lower() in post_data['post_title'].lower():
            matches += 1
        
        # Check if target appears in content
        if post_data['post_content'] and target.lower() in post_data['post_content'].lower():
            matches += 1
        
        # Check if target matches phone number
        if post_data['phone_number'] and self.scraping_utils.normalize_phone_number(post_data['phone_number']) == self.scraping_utils.normalize_phone_number(target):
            matches += 1
        
        # Check if target matches email
        if post_data['email'] and self.scraping_utils.normalize_email(post_data['email']) == self.scraping_utils.normalize_email(target):
            matches += 1
        
        # Check if target appears in location
        if post_data['location'] and target.lower() in post_data['location'].lower():
            matches += 0.5
        
        # Calculate score
        confidence_score = matches / total_fields
        
        # Exact match bonus for phone/email
        if (post_data['phone_number'] and self.scraping_utils.normalize_phone_number(post_data['phone_number']) == self.scraping_utils.normalize_phone_number(target)) or \
           (post_data['email'] and self.scraping_utils.normalize_email(post_data['email']) == self.scraping_utils.normalize_email(target)):
            confidence_score *= 1.3
        
        return min(confidence_score, 1.0)
    
    async def _store_post_data(self, post_data: Dict):
        """Store post data in database"""
        async with AsyncSessionLocal() as session:
            try:
                # Create or update identity based on contact info
                identity_id = None
                
                # Try to find identity by phone
                if post_data['phone_number']:
                    phone = self.scraping_utils.normalize_phone_number(post_data['phone_number'])
                    identity = await session.execute(
                        "SELECT id FROM identities WHERE phone = :phone",
                        {"phone": phone}
                    )
                    identity_result = identity.fetchone()
                    
                    if identity_result:
                        identity_id = identity_result[0]
                
                # Try to find identity by email
                if not identity_id and post_data['email']:
                    email = self.scraping_utils.normalize_email(post_data['email'])
                    identity = await session.execute(
                        "SELECT id FROM identities WHERE email = :email",
                        {"email": email}
                    )
                    identity_result = identity.fetchone()
                    
                    if identity_result:
                        identity_id = identity_result[0]
                
                # Create new identity if none found
                if not identity_id:
                    new_identity = Identity(
                        username=f"personals_{post_data['site']}_{post_data['post_id'][:20]}",
                        phone=post_data['phone_number'],
                        email=post_data['email'],
                        source=f"{post_data['site']}_post",
                        confidence_score=post_data['confidence_score']
                    )
                    session.add(new_identity)
                    await session.flush()
                    identity_id = new_identity.id
                
                # Create or update personals post
                existing_post = await session.execute(
                    "SELECT id FROM personals_posts WHERE site = :site AND post_id = :post_id",
                    {"site": post_data['site'], "post_id": post_data['post_id']}
                )
                existing_post_result = existing_post.fetchone()
                
                if existing_post_result:
                    # Update existing post
                    await session.execute(
                        """
                        UPDATE personals_posts
                        SET identity_id = :identity_id,
                            post_title = :post_title,
                            post_content = :post_content,
                            phone_number = :phone_number,
                            email = :email,
                            location = :location,
                            post_date = :post_date,
                            image_urls = :image_urls,
                            confidence_score = :confidence_score,
                            scraped_at = :scraped_at
                        WHERE id = :id
                        """,
                        {
                            "id": existing_post_result[0],
                            "identity_id": identity_id,
                            "post_title": post_data['post_title'],
                            "post_content": post_data['post_content'],
                            "phone_number": post_data['phone_number'],
                            "email": post_data['email'],
                            "location": post_data['location'],
                            "post_date": post_data['post_date'],
                            "image_urls": json.dumps(post_data['image_urls']),
                            "confidence_score": post_data['confidence_score'],
                            "scraped_at": datetime.utcnow()
                        }
                    )
                else:
                    # Create new post
                    new_post = PersonalsPost(
                        identity_id=identity_id,
                        site=post_data['site'],
                        post_id=post_data['post_id'],
                        post_title=post_data['post_title'],
                        post_content=post_data['post_content'],
                        phone_number=post_data['phone_number'],
                        email=post_data['email'],
                        location=post_data['location'],
                        post_date=post_data['post_date'],
                        image_urls=post_data['image_urls'],
                        confidence_score=post_data['confidence_score'],
                        scraped_at=datetime.utcnow()
                    )
                    session.add(new_post)
                
                # Create content record
                content = Content(
                    identity_id=identity_id,
                    source_site=post_data['site'],
                    post_id=post_data['post_id'],
                    contact_info={
                        'phone': post_data['phone_number'],
                        'email': post_data['email']
                    },
                    location_data={
                        'raw': post_data['location']
                    },
                    post_content=post_data['post_content'],
                    image_urls=post_data['image_urls'],
                    posted_date=post_data['post_date'],
                    confidence_score=post_data['confidence_score']
                )
                session.add(content)
                
                # Create attributes for contact info
                if post_data['phone_number']:
                    attribute = Attribute(
                        identity_id=identity_id,
                        attribute_type='phone_number',
                        attribute_value=post_data['phone_number'],
                        source=f"{post_data['site']}_post",
                        confidence_score=post_data['confidence_score']
                    )
                    session.add(attribute)
                
                if post_data['email']:
                    attribute = Attribute(
                        identity_id=identity_id,
                        attribute_type='email',
                        attribute_value=post_data['email'],
                        source=f"{post_data['site']}_post",
                        confidence_score=post_data['confidence_score']
                    )
                    session.add(attribute)
                
                await session.commit()
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Error storing post data: {e}")
    
    async def get_personals_posts_by_identity(self, identity_id: int) -> List[Dict]:
        """Get all personals posts for an identity"""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    """
                    SELECT id, site, post_id, post_title, post_content, 
                           phone_number, email, location, post_date, 
                           image_urls, confidence_score, scraped_at
                    FROM personals_posts
                    WHERE identity_id = :identity_id AND is_active = TRUE
                    ORDER BY confidence_score DESC
                    """,
                    {"identity_id": identity_id}
                )
                
                posts = []
                for row in result:
                    posts.append({
                        "id": row[0],
                        "site": row[1],
                        "post_id": row[2],
                        "post_title": row[3],
                        "post_content": row[4],
                        "phone_number": row[5],
                        "email": row[6],
                        "location": row[7],
                        "post_date": row[8],
                        "image_urls": json.loads(row[9]) if row[9] else [],
                        "confidence_score": row[10],
                        "scraped_at": row[11]
                    })
                
                return posts
                
            except Exception as e:
                logger.error(f"Error getting personals posts: {e}")
                return []
    
    async def search_by_contact_info(self, contact_info: str) -> List[Dict]:
        """Search personals posts by contact info"""
        results = []
        
        # Search by email
        if '@' in contact_info:
            results.extend(await self._search_posts_by_email(contact_info))
        
        # Search by phone
        else:
            results.extend(await self._search_posts_by_phone(contact_info))
        
        return results
    
    async def _search_posts_by_email(self, email: str) -> List[Dict]:
        """Search personals posts by email"""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    """
                    SELECT pp.id, pp.site, pp.post_id, pp.post_title, pp.post_content, 
                           pp.phone_number, pp.email, pp.location, pp.post_date, 
                           pp.image_urls, pp.confidence_score, pp.scraped_at
                    FROM personals_posts pp
                    JOIN identities i ON pp.identity_id = i.id
                    WHERE i.email = :email AND pp.is_active = TRUE
                    ORDER BY pp.confidence_score DESC
                    """,
                    {"email": email}
                )
                
                posts = []
                for row in result:
                    posts.append({
                        "id": row[0],
                        "site": row[1],
                        "post_id": row[2],
                        "post_title": row[3],
                        "post_content": row[4],
                        "phone_number": row[5],
                        "email": row[6],
                        "location": row[7],
                        "post_date": row[8],
                        "image_urls": json.loads(row[9]) if row[9] else [],
                        "confidence_score": row[10],
                        "scraped_at": row[11]
                    })
                
                return posts
                
            except Exception as e:
                logger.error(f"Error searching posts by email: {e}")
                return []
    
    async def _search_posts_by_phone(self, phone: str) -> List[Dict]:
        """Search personals posts by phone"""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    """
                    SELECT pp.id, pp.site, pp.post_id, pp.post_title, pp.post_content, 
                           pp.phone_number, pp.email, pp.location, pp.post_date, 
                           pp.image_urls, pp.confidence_score, pp.scraped_at
                    FROM personals_posts pp
                    JOIN identities i ON pp.identity_id = i.id
                    WHERE i.phone = :phone AND pp.is_active = TRUE
                    ORDER BY pp.confidence_score DESC
                    """,
                    {"phone": phone}
                )
                
                posts = []
                for row in result:
                    posts.append({
                        "id": row[0],
                        "site": row[1],
                        "post_id": row[2],
                        "post_title": row[3],
                        "post_content": row[4],
                        "phone_number": row[5],
                        "email": row[6],
                        "location": row[7],
                        "post_date": row[8],
                        "image_urls": json.loads(row[9]) if row[9] else [],
                        "confidence_score": row[10],
                        "scraped_at": row[11]
                    })
                
                return posts
                
            except Exception as e:
                logger.error(f"Error searching posts by phone: {e}")
                return []
    
    async def get_linked_identities(self, identity_id: int) -> List[Dict]:
        """Get all linked identities from personals posts"""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    """
                    SELECT a.attribute_value, a.source, a.confidence_score
                    FROM attributes a
                    WHERE a.identity_id = :identity_id 
                    AND (a.attribute_type = 'phone_number' OR a.attribute_type = 'email')
                    AND a.is_active = TRUE
                    ORDER BY a.confidence_score DESC
                    """,
                    {"identity_id": identity_id}
                )
                
                identities = []
                for row in result:
                    identities.append({
                        "contact_info": row[0],
                        "source": row[1],
                        "confidence_score": row[2]
                    })
                
                return identities
                
            except Exception as e:
                logger.error(f"Error getting linked identities: {e}")
                return []
    
    def close(self):
        """Close resources"""
        self.scraping_utils.close()
        self.async_scraping_utils.close()

# Singleton instance
personals_site_scraper = PersonalsSiteScraper()