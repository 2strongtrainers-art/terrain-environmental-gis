"""Stage a GIS-only Pages update and prove unrelated published files are intact.

This command never commits, pushes, or publishes. The input is an isolated
checkout of gh-pages; the output is a reviewable candidate in a new directory.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
GIS_FILES = (
    'index.html', 'app.js', 'styles.css', 'demo.html', 'demo.css', 'demo.js',
    'viewer.html', 'viewer.js', 'manifest.webmanifest', 'sw.js',
    'share-fix.js', 'report-plus.js',
)


def manifest(root):
    result = {}
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root)
        if '.git' in relative.parts:
            continue
        if path.is_symlink():
            raise ValueError(f'Release inputs must not contain symlinks: {relative}')
        if path.is_file():
            result[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def verify_preservation(before, after):
    changed = sorted(path for path in before.keys() | after.keys()
                     if before.get(path) != after.get(path))
    unexpected = sorted(set(changed) - set(GIS_FILES))
    if unexpected:
        raise ValueError(f'Non-GIS published files changed: {unexpected}')
    for prefix in ('atlas/', 'alan-fishing-escape/'):
        if not any(path.startswith(prefix) for path in before):
            raise ValueError(f'Published checkout is missing {prefix}')
    preserved = {path: digest for path, digest in before.items() if path not in GIS_FILES}
    return {
        'changed_files': changed,
        'gis_files': {path: after[path] for path in GIS_FILES},
        'preserved_file_count': len(preserved),
        'preserved_manifest_sha256': hashlib.sha256(
            json.dumps(preserved, sort_keys=True, separators=(',', ':')).encode()
        ).hexdigest(),
        'atlas_files_unchanged': sum(path.startswith('atlas/') or path.startswith('atlas-')
                                     for path in preserved),
        'fishing_files_unchanged': sum(path.startswith('alan-fishing-escape/')
                                      for path in preserved),
        'unexpected_changes': unexpected,
    }


def build(source, published, out):
    source, published, out = (path.resolve() for path in (source, published, out))
    if out == published or published in out.parents or out in published.parents:
        raise ValueError('Candidate and published input must be separate directories')
    if out.exists():
        raise ValueError('Candidate output already exists; choose a new directory')
    for name in GIS_FILES:
        if not (source / name).is_file():
            raise ValueError(f'Missing GIS asset: {name}')
    before = manifest(published)
    shutil.copytree(published, out, ignore=shutil.ignore_patterns('.git'))
    for name in GIS_FILES:
        shutil.copy2(source / name, out / name)
    return verify_preservation(before, manifest(out))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT)
    parser.add_argument('--published', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.out.resolve() == args.report.resolve() or args.out.resolve() in args.report.resolve().parents:
        raise SystemExit('The proof report must be outside the published candidate')
    result = build(args.source, args.published, args.out)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
