"""
Example Usage Script for Username Enumeration Module

Demonstrates basic and advanced usage of the username enumeration system.
"""

import asyncio
import logging
from backend.modules import (
    UsernameEnumerator,
    UsernameMatcher,
    CrossReferenceEngine,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_basic_search():
    """Example 1: Basic username search"""
    print("\n" + "="*60)
    print("Example 1: Basic Username Search")
    print("="*60)
    
    async with UsernameEnumerator(max_concurrent=20) as enumerator:
        username = "example_user"
        print(f"\nSearching for: {username}")
        print("Platforms configured:", len(enumerator.platforms))
        
        # Perform search
        matches = await enumerator.search(username, fuzzy_match=False)
        
        # Display results
        print(f"\nFound {len(matches)} matches:")
        for match in matches[:10]:  # Show first 10
            print(f"  • {match.platform}: {match.profile_url}")
            print(f"    Confidence: {match.confidence.value}, Verified: {match.is_verified}")


async def example_fuzzy_search():
    """Example 2: Fuzzy matching search"""
    print("\n" + "="*60)
    print("Example 2: Fuzzy Matching Search")
    print("="*60)
    
    matcher = UsernameMatcher(fuzzy_threshold=70)
    
    username = "john_smith"
    print(f"\nUsername: {username}")
    
    # Generate variations
    variations = matcher.generate_variations(username)
    print(f"\nGenerated {len(variations)} variations:")
    for var in variations[:20]:
        similarity = matcher.calculate_similarity(username, var)
        print(f"  • {var} (similarity: {similarity}%)")
    
    # Extract from email
    email = "john.smith.work+dev@gmail.com"
    from_email = matcher.extract_username_from_email(email)
    print(f"\nEmail: {email}")
    print("Extracted usernames:", from_email)
    
    # Extract from name
    name = "John Michael Smith"
    from_name = matcher.extract_username_from_name(name)
    print(f"\nName: {name}")
    print("Possible usernames:", from_name[:10])


async def example_reverse_lookup():
    """Example 3: Reverse lookup by email"""
    print("\n" + "="*60)
    print("Example 3: Reverse Email Lookup")
    print("="*60)
    
    matcher = UsernameMatcher()
    
    email = "john.smith@example.com"
    print(f"\nEmail: {email}")
    
    # Extract usernames
    usernames = matcher.extract_username_from_email(email)
    print(f"Extracted usernames: {usernames}")
    
    # Search for extracted usernames
    async with UsernameEnumerator(max_concurrent=10) as enumerator:
        for username in usernames[:3]:  # Check first 3
            print(f"\nSearching for: {username}")
            matches = await enumerator.search(username, fuzzy_match=False)
            print(f"  Found {len(matches)} matches")


async def example_cross_reference():
    """Example 4: Cross-reference identities"""
    print("\n" + "="*60)
    print("Example 4: Cross-Reference Engine")
    print("="*60)
    
    engine = CrossReferenceEngine()
    matcher = UsernameMatcher()
    
    # Find related usernames
    usernames = ["john_doe", "john.doe", "johndoe", "jane_doe"]
    print(f"\nUsernames to cross-reference: {usernames}")
    
    related = engine.find_related_usernames(usernames, threshold=70)
    
    print("\nRelationships found:")
    for username, matches in related.items():
        print(f"\n  {username} related to:")
        for related_username, score in matches:
            print(f"    • {related_username} (similarity: {score}%)")
    
    # Find potential aliases
    if related:
        primary = list(related.keys())[0]
        aliases = engine.find_potential_aliases(primary, min_similarity=0.7)
        print(f"\nPotential aliases for {primary}:")
        for alias in aliases[:5]:
            print(f"  • {alias['username']} on {alias['platform']}")


async def example_statistics():
    """Example 5: Platform statistics"""
    print("\n" + "="*60)
    print("Example 5: Platform Statistics")
    print("="*60)
    
    enumerator = UsernameEnumerator()
    stats = enumerator.get_platform_stats()
    
    print(f"\nTotal Platforms: {stats['total_platforms']}")
    print(f"Max Concurrent: {stats['max_concurrent']}")
    print(f"Request Timeout: {stats['timeout']}s")
    print(f"Max Retries: {stats['max_retries']}")
    
    print("\nPlatforms by Category:")
    for category, count in stats['categories'].items():
        print(f"  • {category}: {count}")


async def example_name_based_enumeration():
    """Example 6: Name-based enumeration"""
    print("\n" + "="*60)
    print("Example 6: Name-Based Enumeration")
    print("="*60)
    
    matcher = UsernameMatcher()
    
    # Generate usernames from name
    name = "Alexander James Thompson"
    print(f"\nFull Name: {name}")
    
    usernames = matcher.extract_username_from_name(name)
    print(f"\nGenerated {len(usernames)} possible usernames:")
    for username in usernames[:15]:
        print(f"  • {username}")


async def example_phone_based_enumeration():
    """Example 7: Phone-based enumeration"""
    print("\n" + "="*60)
    print("Example 7: Phone-Based Enumeration")
    print("="*60)
    
    matcher = UsernameMatcher()
    
    # Generate usernames from phone
    phone = "+1 (555) 123-4567"
    print(f"\nPhone: {phone}")
    
    usernames = matcher.extract_username_from_phone(phone)
    print(f"\nExtracted {len(usernames)} potential usernames:")
    for username in usernames:
        print(f"  • {username}")


async def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("USERNAME ENUMERATION MODULE - USAGE EXAMPLES")
    print("="*60)
    
    try:
        await example_basic_search()
        await example_fuzzy_search()
        await example_reverse_lookup()
        await example_cross_reference()
        await example_statistics()
        await example_name_based_enumeration()
        await example_phone_based_enumeration()
        
        print("\n" + "="*60)
        print("All examples completed!")
        print("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
