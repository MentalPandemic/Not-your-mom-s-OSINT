import unittest

from backend.modules.social_extraction import (
    NormalizedPost,
    NormalizedProfile,
    discover_linked_accounts,
    extract_emails,
    extract_urls,
)


class TestSocialExtraction(unittest.TestCase):
    def test_extract_emails(self):
        text = "Contact: test@example.com and TEST@example.com."
        self.assertEqual(extract_emails(text), ["test@example.com"])

    def test_extract_urls(self):
        text = "See https://github.com/foo and www.twitter.com/bar"
        urls = extract_urls(text)
        self.assertIn("https://github.com/foo", urls)
        self.assertIn("https://www.twitter.com/bar", urls)

    def test_discover_linked_accounts_from_bio_url(self):
        prof = NormalizedProfile(
            platform="twitter",
            username="alice",
            bio="Find me on https://github.com/alice",
            profile_url="https://x.com/alice",
        )
        linked = discover_linked_accounts(prof, [])
        self.assertTrue(any(a.linked_platform == "github" and a.linked_username == "alice" for a in linked))


if __name__ == "__main__":
    unittest.main()
