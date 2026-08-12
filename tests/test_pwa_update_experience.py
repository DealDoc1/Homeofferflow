from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


class PwaUpdateExperienceTests(unittest.TestCase):
    def test_installed_app_surfaces_an_explicit_update_choice(self):
        self.assertIn("card.id = 'hofPwaUpdateCard'", INDEX)
        self.assertIn('HomeOfferFlow update ready', INDEX)
        self.assertIn('your local draft stays on this device', INDEX)
        self.assertIn("registration.addEventListener('updatefound'", INDEX)
        self.assertIn("navigator.serviceWorker.addEventListener('controllerchange'", INDEX)

    def test_update_only_activates_after_the_user_confirms(self):
        self.assertIn("HOF_SKIP_WAITING", INDEX)
        self.assertIn("event.data?.type === 'HOF_SKIP_WAITING'", WORKER)
        self.assertNotIn("self.skipWaiting();", WORKER.split("self.addEventListener('message'", 1)[0])

    def test_shell_cache_changes_for_the_update_notification(self):
        self.assertIn("homeofferflow-shell-v7", WORKER)


if __name__ == "__main__":
    unittest.main()
