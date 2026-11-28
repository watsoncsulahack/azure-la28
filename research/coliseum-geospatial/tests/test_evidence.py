"""Offline regressions for acquisition completeness, reference transforms and missing data."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
import numpy as np

ROOT=Path(__file__).resolve().parents[1]/'evidence'
def module(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/(name+'.py'))
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
acquire=module('acquire')


class EvidenceTests(unittest.TestCase):
    def test_octree_intersection_uses_correct_xy_bounds(self):
        self.assertEqual(acquire.node_bounds('1-1-0-1',[0,0,0,8,8,8]),[4,0,4,8,4,8])
        self.assertTrue(acquire.intersects_xy([4,0,4,8,4,8],[3,3,5,5]))
        self.assertFalse(acquire.intersects_xy([4,0,4,8,4,8],[0,5,3,7]))

    def test_throttled_download_does_not_retry_or_leave_valid_cache(self):
        with tempfile.TemporaryDirectory()as directory,patch.object(acquire,'RAW',Path(directory)):
            with patch.object(acquire,'urlopen',side_effect=HTTPError('https://example.invalid',429,'rate limited',{},None))as get:
                with self.assertRaises(HTTPError):
                    acquire.fetch('test.laz','https://example.invalid')
                self.assertEqual(get.call_count,1)
                self.assertFalse((Path(directory)/'test.laz').exists())
                receipt=json.loads((Path(directory)/'test.laz.receipt.json').read_text())
                self.assertEqual(receipt['http_status'],429)
                self.assertEqual(receipt['attempts'],1)

    def test_building_subset_rejects_missing_features(self):
        with tempfile.TemporaryDirectory()as directory:
            p=Path(directory);(p/'ids').write_text('{"objectIds":[1,2]}');(p/'features').write_text('{"features":[]}')
            with patch.object(acquire,'DERIVED',p/'out'),patch.object(acquire,'fetch',side_effect=[p/'ids',p/'features']):
                with self.assertRaisesRegex(ValueError,'Missing or duplicated'):
                    acquire.buildings()
            self.assertFalse((p/'out/buildings.geojson').exists())

    def test_candidate_pose_is_explicitly_unapproved_and_right_handed(self):
        p=ROOT/'reports/candidate-registration.json'
        data=json.loads(p.read_text());m=np.array(data['threejs_to_utm_matrix_row_major'])
        self.assertFalse(data['approved_for_model'])
        self.assertEqual(data['status'],'PROVISIONAL_DIAGNOSTIC_ONLY')
        np.testing.assert_allclose(m[:3,:3].T@m[:3,:3],np.eye(3),atol=1e-12)
        self.assertAlmostEqual(np.linalg.det(m[:3,:3]),1)
        np.testing.assert_allclose((m@np.array([0,1,0,1]))[:3]-m[:3,3],[0,0,1])
        self.assertLess((m@np.array([0,0,1,1]))[1],m[1,3])

    def test_unobserved_geometry_cannot_gain_passing_statistics(self):
        analyze=module('analyze')
        self.assertEqual(analyze.stats([float('nan')]),{'count':0,'status':'UNOBSERVED'})
        report=json.loads((ROOT/'reports/independent-diagnostics.json').read_text())
        self.assertEqual(report['independent_physical_acceptance_checks'],0)
        self.assertFalse(report['ready_for_accessibility_or_crowd_simulation'])
        self.assertGreater(report['bowl_missing_cells'],0)


if __name__=='__main__':unittest.main()
