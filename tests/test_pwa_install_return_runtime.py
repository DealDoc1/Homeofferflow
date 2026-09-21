from pathlib import Path
import subprocess
import unittest


class PwaInstallReturnRuntimeTests(unittest.TestCase):
    def test_installed_app_return_runtime(self):
        result = subprocess.run(
            ["node", "--test", str(Path(__file__).with_name("pwa_install_return.runtime.cjs"))],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
