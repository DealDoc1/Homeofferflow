from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


class PwaUpdateExperienceTests(unittest.TestCase):
    def test_installed_app_surfaces_an_explicit_update_choice(self):
        self.assertIn("card.id = 'hofPwaUpdateCard'", INDEX)
        self.assertIn('HomeOfferFlow update ready', INDEX)
        self.assertIn('your saved work stays on this device', INDEX)
        self.assertIn("registration.addEventListener('updatefound'", INDEX)
        self.assertIn("navigator.serviceWorker.addEventListener('controllerchange'", INDEX)
        self.assertIn("if (!isHomeOfferFlowStandaloneApp() || (!registration?.waiting && !workerAlreadyActive) || document.getElementById('hofPwaUpdateCard')) return;", INDEX)
        self.assertIn("Reserve the update choice for an installed app", INDEX)

    def test_update_activates_without_reloading_open_work(self):
        self.assertIn("HOF_SKIP_WAITING", INDEX)
        self.assertIn("event.data?.type === 'HOF_SKIP_WAITING'", WORKER)
        install_handler = WORKER.split("self.addEventListener('install'", 1)[1].split("self.addEventListener('message'", 1)[0]
        self.assertIn(".then(() => self.skipWaiting())", install_handler)
        self.assertIn("Activation alone never reloads an in-progress transaction", INDEX)

    def test_shell_cache_changes_for_the_update_notification(self):
        self.assertIn("homeofferflow-shell-v76", WORKER)
        self.assertIn("fetch(event.request, { cache: 'no-store' })", WORKER)
        self.assertIn("safe-area-inset-bottom", INDEX)


if __name__ == "__main__":
    unittest.main()
