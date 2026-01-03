import os
import tempfile
import unittest

from backend.modules.persistence import SqliteSocialMediaStore
from backend.modules.social_extraction import LinkedAccount, NormalizedPost, NormalizedProfile


class TestPersistence(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False)
        self.tmp.close()
        self.store = SqliteSocialMediaStore(db_path=self.tmp.name)

    async def asyncTearDown(self):
        try:
            os.unlink(self.tmp.name)
        except OSError:
            pass

    async def test_round_trip(self):
        prof = NormalizedProfile(platform="github", username="octocat", bio="hi")
        stored = await self.store.upsert_profile(prof)
        self.assertEqual(stored.platform, "github")

        await self.store.replace_posts(stored.id, [NormalizedPost(platform="github", username="octocat", post_id="1", url=None, content="x")])
        posts = await self.store.get_posts(stored.id, offset=0, limit=10)
        self.assertEqual(len(posts), 1)

        linked = [
            LinkedAccount(
                from_platform="github",
                from_username="octocat",
                linked_platform="twitter",
                linked_username="octo",
                confidence=0.9,
            )
        ]
        await self.store.replace_linked_accounts("github", "octocat", linked)
        links = await self.store.get_linked_accounts("github", "octocat")
        self.assertEqual(links[0]["platform"], "twitter")


if __name__ == "__main__":
    unittest.main()
