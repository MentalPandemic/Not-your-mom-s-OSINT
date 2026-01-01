import json
import os
from typing import Dict, Any

# Load adult/personals configuration
with open(os.path.join(os.path.dirname(__file__), 'adult_personals_sources.json'), 'r') as f:
    adult_personals_config = json.load(f)

# Extract adult sites and personals sites configs
adult_sites_config = adult_personals_config.get('adult_sites', {})
personals_sites_config = adult_personals_config.get('personals_sites', {})
general_settings = adult_personals_config.get('general_settings', {})

__all__ = [
    'adult_personals_config',
    'adult_sites_config', 
    'personals_sites_config',
    'general_settings'
]