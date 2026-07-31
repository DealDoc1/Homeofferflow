from pathlib import Path
import unittest


class BrokerageAccountLoaderGuardTests(unittest.TestCase):
    def test_brokerage_loader_initializes_optional_platform_namespace(self):
        source = Path("index.html").read_text(encoding="utf-8")
        marker = "root.loadBrokerageFoundation = async function loadBrokerageFoundation()"
        start = source.index(marker)
        block = source[start : start + 2500]
        self.assertIn("root.hofPlatform = root.hofPlatform || {};", block)


if __name__ == "__main__":
    unittest.main()
