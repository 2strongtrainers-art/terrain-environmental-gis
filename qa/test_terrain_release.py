"""Regression checks for the GIS publication boundary, using disposable fixtures."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    'terrain_release', Path(__file__).resolve().parents[1] / 'scripts/build_terrain_release.py')
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleaseBoundaryTests(unittest.TestCase):
    def test_preserves_atlas_game_and_unknown_published_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, published, out = (root / name for name in ('source', 'published', 'candidate'))
            source.mkdir()
            published.mkdir()
            for name in release.GIS_FILES:
                (source / name).write_text('new GIS: ' + name)
            for name in ('atlas/index.html', 'atlas/collections/custom/index.html',
                         'atlas-upgrade.js', 'alan-fishing-escape/index.html',
                         'alan-fishing-escape/assets/panorama.png', 'unrelated.txt'):
                path = published / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('existing published bytes: ' + name)
            (published / 'index.html').write_text('old GIS')
            report = release.build(source, published, out)
            self.assertEqual(report['unexpected_changes'], [])
            self.assertEqual(report['preserved_file_count'], 6)
            self.assertEqual(report['fishing_files_unchanged'], 2)
            self.assertEqual(report['atlas_files_unchanged'], 3)
            self.assertEqual((out / 'index.html').read_text(), 'new GIS: index.html')
            self.assertEqual((published / 'index.html').read_text(), 'old GIS')
            before = release.manifest(published)
            (out / 'atlas/index.html').write_text('accidental overwrite')
            with self.assertRaisesRegex(ValueError, 'Non-GIS'):
                release.verify_preservation(before, release.manifest(out))
            with self.assertRaisesRegex(ValueError, 'already exists'):
                release.build(source, published, out)

    def test_rejects_missing_published_app_before_certifying(self):
        with self.assertRaisesRegex(ValueError, 'missing atlas/'):
            release.verify_preservation({}, {})


if __name__ == '__main__':
    unittest.main()
