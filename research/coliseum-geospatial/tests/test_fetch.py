import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("coliseum_geo_fetch", ROOT / "fetch.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class FetchTests(unittest.TestCase):
    def test_bbox_contains_expected_coliseum_center(self):
        w, s, e, n = module.bbox()
        self.assertTrue(w < -118.28782 < e)
        self.assertTrue(s < 34.0140 < n)

    def test_2020_footprint_source_and_query(self):
        self.assertIn("2020", module.SERVICE)
        url = module.ids_url()
        self.assertIn("returnIdsOnly=true", url)
        self.assertIn("inSR=4326", url)

    def test_lidar_source_vintages(self):
        self.assertIn("CA_LosAngeles_1_B23", module.EPT["2023"])
        self.assertIn("2016", module.EPT["2016"])

    def test_arcgis_ids_not_fetched_on_dry_run(self):
        # No network call: dry-run must return immediately.
        module.collect_buildings(dry_run=True)


if __name__ == "__main__":
    unittest.main()
