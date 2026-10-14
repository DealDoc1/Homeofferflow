from pathlib import Path
import subprocess
import unittest


class InspectionPartnersRuntimeTests(unittest.TestCase):
    def test_actual_profile_cache_and_inspection_renderer(self):
        result = subprocess.run(['node','--test',str(Path(__file__).with_name('inspection_partners.runtime.cjs'))],capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)


if __name__ == '__main__': unittest.main()
