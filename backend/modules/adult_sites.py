import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger
from bs4 import BeautifulSoup
import aiohttp
from fake_useragent import UserAgent
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.models.database import AdultProfile, Identity, Attribute, Source, AsyncSessionLocal
from backend.utils.scraping_utils import ScrapingUtils, AsyncScrapingUtils
from backend.config.adult_personals_sources import adult_sites_config

class AdultSiteScraper:
    """Adult/NSFW site enumeration module"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or adult_sites_config
        self.scraping_utils = ScrapingUtils(self.config.get('general_settings', {}))
        self.async_scraping_utils = AsyncScrapingUtils(self.config.get('general_settings', {}))
        self.ua = UserAgent()
    
    async def search_adult_sites(self, target: str, platforms: Optional[List[str]] = None) -> List[Dict]:
        """Search for target across adult platforms"""
        if platforms is None:
            platforms = list(self.config['adult_sites'].keys())
        
        results = []
        tasks = []
        
        for platform in platforms:
            if platform in self.config['adult_sites']:
                task = asyncio.create_task(self._search_platform(platform, target))
                tasks.append(task)
        
        # Run tasks concurrently with rate limiting
        for task in asyncio.as_completed(tasks):
            try:
                result = await task
                if result:
                    results.extend(result)
            except Exception as e:
                logger.error(f"Error searching {platform}: {e}")
        
        return results
    
    async def _search_platform(self, platform: str, target: str) -> List[Dict]:
        """Search specific adult platform"""
        platform_config = self.config['adult_sites'][platform]
        results = []
        
        try:
            # Build search URL
            search_url = platform_config['base_url'] + platform_config['search_endpoint'].replace('{username}', target)
            
            logger.info(f"Searching {platform} for {target}: {search_url}")
            
            # Make async request
            response = await self.async_scraping_utils.make_async_request(search_url)
            if response:
                html = await response.text()
                soup = self.scraping_utils.parse_html(html)
                
                # Extract profile data
                profile_data = self._extract_profile_data(soup, platform_config, target)
                
                if profile_data:
                    # Calculate confidence score
                    confidence_score = self._calculate_confidence_score(profile_data, target)
                    profile_data['confidence_score'] = confidence_score
                    profile_data['platform'] = platform
                    profile_data['scraped_at'] = datetime.utcnow().isoformat()
                    
                    results.append(profile_data)
                    
                    # Store in database
                    await self._store_profile_data(profile_data)
        
        except Exception as e:
            logger.error(f"Error searching {platform}: {e}")
        
        return results
    
    def _extract_profile_data(self, soup: BeautifulSoup, platform_config: Dict, target: str) -> Optional[Dict]:
        """Extract profile data from HTML"""
        selectors = platform_config['selectors']
        profile_data = {}
        
        # Extract basic profile info
        username = self.scraping_utils.extract_text(soup, selectors['username'])
        if not username:
            return None
            
        profile_data['username'] = username
        profile_data['profile_url'] = self.scraping_utils.extract_attribute(soup, selectors['profile_url'], 'href')
        profile_data['bio'] = self.scraping_utils.extract_text(soup, selectors['bio'])
        
        # Extract join date
        join_date_str = self.scraping_utils.extract_text(soup, selectors['join_date'])
        try:
            profile_data['join_date'] = datetime.strptime(join_date_str, '%Y-%m-%d').isoformat() if join_date_str else None
        except:
            profile_data['join_date'] = None
        
        # Extract profile image
        profile_data['profile_image_url'] = self.scraping_utils.extract_attribute(soup, selectors['profile_image'], 'src')
        
        # Extract linked accounts
        if 'social_links' in selectors:
            social_links = self.scraping_utils.extract_links(soup, selectors['social_links'])
            profile_data['linked_accounts'] = social_links
        else:
            profile_data['linked_accounts'] = []
        
        return profile_data
    
    def _calculate_confidence_score(self, profile_data: Dict, target: str) -> float:
        """Calculate confidence score for profile match"""
        matches = 0
        total_fields = 3
        
        # Check username match
        if profile_data['username'].lower() == target.lower():
            matches += 1
        elif target.lower() in profile_data['username'].lower():
            matches += 0.5
        
        # Check bio for target
        if profile_data['bio'] and target.lower() in profile_data['bio'].lower():
            matches += 0.5
        
        # Check profile URL
        if profile_data['profile_url'] and target.lower() in profile_data['profile_url'].lower():
            matches += 0.5
        
        # Calculate score
        confidence_score = matches / total_fields
        
        # Exact match bonus
        if profile_data['username'].lower() == target.lower():
            confidence_score *= 1.2
        
        return min(confidence_score, 1.0)
    
    async def _store_profile_data(self, profile_data: Dict):
        """Store profile data in database"""
        async with AsyncSessionLocal() as session:
            try:
                # Create or update identity
                identity = await session.execute(
                    "SELECT id FROM identities WHERE username = :username",
                    {"username": profile_data['username']}
                )
                identity_result = identity.fetchone()
                
                if identity_result:
                    identity_id = identity_result[0]
                else:
                    new_identity = Identity(
                        username=profile_data['username'],
                        source=f"{profile_data['platform']}_profile",
                        confidence_score=profile_data['confidence_score']
                    )
                    session.add(new_identity)
                    await session.flush()
                    identity_id = new_identity.id
                
                # Create or update adult profile
                existing_profile = await session.execute(
                    "SELECT id FROM adult_profiles WHERE platform = :platform AND username = :username",
                    {"platform": profile_data['platform'], "username": profile_data['username']}
                )
                existing_profile_result = existing_profile.fetchone()
                
                if existing_profile_result:
                    # Update existing profile
                    await session.execute(
                        """
                        UPDATE adult_profiles
                        SET profile_url = :profile_url,
                            bio = :bio,
                            join_date = :join_date,
                            profile_image_url = :profile_image_url,
                            linked_accounts = :linked_accounts,
                            confidence_score = :confidence_score,
                            scraped_at = :scraped_at
                        WHERE id = :id
                        """,
                        {
                            "id": existing_profile_result[0],
                            "profile_url": profile_data['profile_url'],
                            "bio": profile_data['bio'],
                            "join_date": profile_data['join_date'],
                            "profile_image_url": profile_data['profile_image_url'],
                            "linked_accounts": json.dumps(profile_data['linked_accounts']),
                            "confidence_score": profile_data['confidence_score'],
                            "scraped_at": datetime.utcnow()
                        }
                    )
                else:
                    # Create new profile
                    new_profile = AdultProfile(
                        identity_id=identity_id,
                        platform=profile_data['platform'],
                        username=profile_data['username'],
                        profile_url=profile_data['profile_url'],
                        bio=profile_data['bio'],
                        join_date=profile_data['join_date'],
                        profile_image_url=profile_data['profile_image_url'],
                        linked_accounts=profile_data['linked_accounts'],
                        confidence_score=profile_data['confidence_score'],
                        scraped_at=datetime.utcnow()
                    )
                    session.add(new_profile)
                
                # Create attributes for linked accounts
                for account in profile_data['linked_accounts']:
                    attribute = Attribute(
                        identity_id=identity_id,
                        attribute_type='linked_account',
                        attribute_value=account,
                        source=f"{profile_data['platform']}_linked_account",
                        confidence_score=profile_data['confidence_score']
                    )
                    session.add(attribute)
                
                await session.commit()
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Error storing profile data: {e}")
    
    async def get_adult_profiles_by_identity(self, identity_id: int) -> List[Dict]:
        """Get all adult profiles for an identity"""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    """
                    SELECT id, platform, username, profile_url, bio, join_date, 
                           profile_image_url, linked_accounts, confidence_score, scraped_at
                    FROM adult_profiles
                    WHERE identity_id = :identity_id AND is_active = TRUE
                    ORDER BY confidence_score DESC
                    """,
                    {"identity_id": identity_id}
                )
                
                profiles = []
                for row in result:
                    profiles.append({
                        "id": row[0],
                        "platform": row[1],
                        "username": row[2],
                        "profile_url": row[3],
                        "bio": row[4],
                        "join_date": row[5],
                        "profile_image_url": row[6],
                        "linked_accounts": json.loads(row[7]) if row[7] else [],
                        "confidence_score": row[8],
                        "scraped_at": row[9]
                    })
                
                return profiles
                
            except Exception as e:
                logger.error(f"Error getting adult profiles: {e}")
                return []
    
    async def search_by_contact_info(self, contact_info: str) -> List[Dict]:
        """Search adult profiles by contact info"""
        results = []
        
        # Search by email
        if '@' in contact_info:
            results.extend(await self._search_by_email(contact_info))
        
        # Search by phone
        else:
            results.extend(await self._search_by_phone(contact_info))
        
        return results
    
    async def _search_by_email(self, email: str) -> List[Dict]:
        """Search adult profiles by email"""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    """
                    SELECT ap.id, ap.platform, ap.username, ap.profile_url, ap.bio, 
                           ap.join_date, ap.profile_image_url, ap.linked_accounts, 
                           ap.confidence_score, ap.scraped_at
                    FROM adult_profiles ap
                    JOIN identities i ON ap.identity_id = i.id
                    WHERE i.email = :email AND ap.is_active = TRUE
                    ORDER BY ap.confidence_score DESC
                    """,
                    {"email": email}
                )
                
                profiles = []
                for row in result:
                    profiles.append({
                        "id": row[0],
                        "platform": row[1],
                        "username": row[2],
                        "profile_url": row[3],
                        "bio": row[4],
                        "join_date": row[5],
                        "profile_image_url": row[6],
                        "linked_accounts": json.loads(row[7]) if row[7] else [],
                        "confidence_score": row[8],
                        "scraped_at": row[9]
                    })
                
                return profiles
                
            except Exception as e:
                logger.error(f"Error searching by email: {e}")
                return []
    
    async def _search_by_phone(self, phone: str) -> List[Dict]:
        """Search adult profiles by phone"""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    """
                    SELECT ap.id, ap.platform, ap.username, ap.profile_url, ap.bio, 
                           ap.join_date, ap.profile_image_url, ap.linked_accounts, 
                           ap.confidence_score, ap.scraped_at
                    FROM adult_profiles ap
                    JOIN identities i ON ap.identity_id = i.id
                    WHERE i.phone = :phone AND ap.is_active = TRUE
                    ORDER BY ap.confidence_score DESC
                    """,
                    {"phone": phone}
                )
                
                profiles = []
                for row in result:
                    profiles.append({
                        "id": row[0],
                        "platform": row[1],
                        "username": row[2],
                        "profile_url": row[3],
                        "bio": row[4],
                        "join_date": row[5],
                        "profile_image_url": row[6],
                        "linked_accounts": json.loads(row[7]) if row[7] else [],
                        "confidence_score": row[8],
                        "scraped_at": row[9]
                    })
                
                return profiles
                
            except Exception as e:
                logger.error(f"Error searching by phone: {e}")
                return []
    
    async def get_linked_identities(self, identity_id: int) -> List[Dict]:
        """Get all linked identities from adult platforms"""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    """
                    SELECT a.attribute_value, a.source, a.confidence_score
                    FROM attributes a
                    WHERE a.identity_id = :identity_id 
                    AND a.attribute_type = 'linked_account'
                    AND a.is_active = TRUE
                    ORDER BY a.confidence_score DESC
                    """,
                    {"identity_id": identity_id}
                )
                
                identities = []
                for row in result:
                    identities.append({
                        "linked_account": row[0],
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
adult_site_scraper = AdultSiteScraper()