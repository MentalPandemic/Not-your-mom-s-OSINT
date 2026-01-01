from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from urllib.parse import urljoin


@dataclass
class PlatformConfig:
    name: str
    base_url: str
    profile_patterns: List[str]
    enabled: bool = True
    fuzzy_search_enabled: bool = True
    api_rate_limit: int = 60  # requests per minute
    auth_required: bool = False
    api_key: Optional[str] = None


class PlatformRegistry:
    """Registry of supported platforms for username enumeration"""
    
    def __init__(self):
        self.platforms = self._initialize_platforms()
    
    def _initialize_platforms(self) -> Dict[str, PlatformConfig]:
        """Initialize supported social platforms"""
        platforms = {
            'twitter': PlatformConfig(
                name='Twitter',
                base_url='https://twitter.com',
                profile_patterns=['/{username}'],
                enabled=True,
                fuzzy_search_enabled=True,
                api_rate_limit=15
            ),
            'github': PlatformConfig(
                name='GitHub',
                base_url='https://github.com',
                profile_patterns=['/{username}'],
                enabled=True,
                fuzzy_search_enabled=True,
                api_rate_limit=60
            ),
            'instagram': PlatformConfig(
                name='Instagram',
                base_url='https://www.instagram.com',
                profile_patterns=['/{username}', '/{username}/'],
                enabled=True,
                fuzzy_search_enabled=False,
                api_rate_limit=30
            ),
            'linkedin': PlatformConfig(
                name='LinkedIn',
                base_url='https://www.linkedin.com/in',
                profile_patterns=['/{username}', '/{username}/'],
                enabled=True,
                fuzzy_search_enabled=False,
                auth_required=True,
                api_rate_limit=100
            ),
            'facebook': PlatformConfig(
                name='Facebook',
                base_url='https://www.facebook.com',
                profile_patterns=['/{username}', '/{username}/'],
                enabled=True,
                fuzzy_search_enabled=False,
                api_rate_limit=60
            ),
            'reddit': PlatformConfig(
                name='Reddit',
                base_url='https://www.reddit.com/user',
                profile_patterns=['/{username}', '/{username}/'],
                enabled=True,
                fuzzy_search_enabled=True,
                api_rate_limit=300
            ),
            'youtube': PlatformConfig(
                name='YouTube',
                base_url='https://www.youtube.com',
                profile_patterns=['/c/{username}', '/user/{username}', '/@{username}'],
                enabled=True,
                fuzzy_search_enabled=False,
                api_rate_limit=180
            ),
            'tiktok': PlatformConfig(
                name='TikTok',
                base_url='https://www.tiktok.com',
                profile_patterns=['/@{username}', '@{username}'],
                enabled=True,
                fuzzy_search_enabled=False,
                api_rate_limit=100
            ),
            'pinterest': PlatformConfig(
                name='Pinterest',
                base_url='https://www.pinterest.com',
                profile_patterns=['/{username}/', '/{username}'],
                enabled=True,
                fuzzy_search_enabled=True,
                api_rate_limit=100
            ),
            'medium': PlatformConfig(
                name='Medium',
                base_url='https://medium.com',
                profile_patterns=['/@{username}'],
                enabled=True,
                fuzzy_search_enabled=False,
                api_rate_limit=100
            ),
            'stackoverflow': PlatformConfig(
                name='StackOverflow',
                base_url='https://stackoverflow.com/users',
                profile_patterns=['/{username_id}/{username}'],
                enabled=True,
                fuzzy_search_enabled=False,
                api_rate_limit=100
            ),
            'discord': PlatformConfig(
                name='Discord',
                base_url='https://discordapp.com/users',
                profile_patterns=['/{username}'],
                enabled=False,  # Discord doesn't have public profile URLs
                fuzzy_search_enabled=False,
                auth_required=True
            ),
            'twitch': PlatformConfig(
                name='Twitch',
                base_url='https://www.twitch.tv',
                profile_patterns=['/{username}', '/{username}/'],
                enabled=True,
                fuzzy_search_enabled=True,
                api_rate_limit=800
            ),
            'snapchat': PlatformConfig(
                name='SnapChat',
                base_url='https://snapchat.com/add',
                profile_patterns=['/{username}'],
                enabled=True,
                fuzzy_search_enabled=False,
                api_rate_limit=50
            ),
            'telegram': PlatformConfig(
                name='Telegram',
                base_url='https://t.me',
                profile_patterns=['/{username}'],
                enabled=True,
                fuzzy_search_enabled=False,
                api_rate_limit=1000
            ),
            'keybase': PlatformConfig(
                name='Keybase',
                base_url='https://keybase.io',
                profile_patterns=['/{username}'],
                enabled=True,
                fuzzy_search_enabled=True,
                api_rate_limit=500
            ),
            'gitlab': PlatformConfig(
                name='GitLab',
                base_url='https://gitlab.com',
                profile_patterns=['/{username}'],
                enabled=True,
                fuzzy_search_enabled=True,
                api_rate_limit=60
            )
        }
        
        return platforms
    
    def get_platform(self, platform_name: str) -> Optional[PlatformConfig]:
        """Get platform configuration by name"""
        return self.platforms.get(platform_name.lower())
    
    def get_all_platforms(self) -> List[PlatformConfig]:
        """Get all enabled platform configurations"""
        return [p for p in self.platforms.values() if p.enabled]
    
    def get_enabled_platforms(self) -> List[PlatformConfig]:
        """Get all enabled platforms"""
        return self.get_all_platforms()
    
    def add_platform(self, platform_name: str, config: PlatformConfig):
        """Add a new platform to the registry"""
        self.platforms[platform_name.lower()] = config
    
    def update_platform(self, platform_name: str, config: PlatformConfig):
        """Update platform configuration"""
        if platform_name.lower() in self.platforms:
            self.platforms[platform_name.lower()] = config
    
    def remove_platform(self, platform_name: str):
        """Remove a platform from the registry"""
        self.platforms.pop(platform_name.lower(), None)
    
    def generate_profile_urls(self, platform: PlatformConfig, username: str) -> List[str]:
        """Generate possible profile URLs for a username on a platform"""
        urls = []
        
        for pattern in platform.profile_patterns:
            # Replace {username} placeholder with actual username
            if '{username}' in pattern:
                url_path = pattern.replace('{username}', username)
                full_url = urljoin(platform.base_url, url_path)
                urls.append(full_url)
            
            # Handle special patterns like {username_id}
            if '{username_id}' in pattern and '/' in pattern:
                # This is a simplified version - real implementation would need ID mapping
                simplified_pattern = pattern.replace('/{username_id}', '')
                if '{username}' in simplified_pattern:
                    url_path = simplified_pattern.replace('{username}', username)
                    full_url = urljoin(platform.base_url, url_path)
                    urls.append(full_url)
        
        return urls