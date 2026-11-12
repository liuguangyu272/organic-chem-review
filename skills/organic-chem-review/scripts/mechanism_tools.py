"""Validate explicit, mapped elementary steps and render supported mechanisms.

The supplied mechanism is a hypothesis. Passing these checks is not experimental proof.
Requires RDKit; uses a bundled MIT-licensed community mechanism core.
"""

import argparse
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET


def make_png(svg_path, png_path):
    """Optional offline Chromium preview; never uses a personal browser profile."""
    candidates = [shutil.which(n) for n in ('chromium', 'chromium-browser', 'google-chrome', 'msedge')]
    for variable in ('PROGRAMFILES(X86)', 'PROGRAMFILES', 'LOCALAPPDATA'):
        root = os.environ.get(variable)
        if root:
            candidates.extend([str(Path(root) / 'Microsoft/Edge/Application/msedge.exe'),
                               str(Path(root) / 'Google/Chrome/Application/chrome.exe')])
    browser = next((p for p in candidates if p and Path(p).is_file()), None)
    if not browser:
        return 'PNG preview unavailable: no local Chromium/Edge/Chrome; SVG was generated.'
    root = ET.parse(svg_path).getroot()
    width = math.ceil(float(root.attrib['width'].rstrip('px')))
    height = math.ceil(float(root.attrib['height'].rstrip('px')))
    with tempfile.TemporaryDirectory(prefix='organic-chem-preview-') as profile:
        try:
            result = subprocess.run([
                browser, '--headless', '--disable-gpu', '--no-first-run', '--hide-scrollbars',
                '--force-device-scale-factor=2', '--no-default-browser-check',
                f'--user-data-dir={profile}', f'--window-size={width},{height}',
                f'--screenshot={png_path.resolve()}', svg_path.resolve().as_uri(),
            ], capture_output=True, timeout=45,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            if result.returncode or not png_path.is_file():
                return 'PNG preview failed; the SVG and validation record remain available.'
        except (OSError, subprocess.TimeoutExpired) as exc:
            return f'PNG preview unavailable: {exc}'
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--spec', type=Path, help='Explicit mechanism spec JSON, version 2.1 preferred')
    source.add_argument('--example', choices=['sn2', 'proton_transfer', 'carbonyl_addition', 'e2', 'homolysis'])
    parser.add_argument('--output', type=Path, required=True, help='Output filename prefix')
    parser.add_argument('--validate-only', action='store_true')
    parser.add_argument('--png', action='store_true', help='Also render a PNG using a local headless browser')
    args = parser.parse_args()
    base = Path(__file__).resolve().parent
    sys.path.insert(0, str(base / 'vendor'))
    try:
        from rdkit import rdBase
        from codex_organic_chem.mechanism_canvas import validate_mechanism_spec, render_mechanism_canvas
    except ImportError as exc:
        parser.exit(2, f'RDKit is required in this Python environment: {exc}\n')
    spec_path = args.spec or base.parent / 'assets/mechanisms' / f'{args.example}.json'
    try:
        spec = json.loads(spec_path.read_text(encoding='utf-8-sig'))
        if not isinstance(spec, dict):
            raise ValueError('Expected a mechanism object')
        validation = validate_mechanism_spec(spec)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.error(f'Cannot validate mechanism: {exc}')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    def save(suffix, data):
        path = Path(str(args.output) + suffix)
        path.write_text(data if isinstance(data, str) else json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        return path
    checks = save('.checks.json', validation)
    if validation['blocking_issues'] or validation['semantic_checks']['status'] != 'valid':
        print(json.dumps({'status': 'blocked', 'checks': str(checks.resolve()),
                          'issues': validation['blocking_issues'],
                          'semantic_status': validation['semantic_checks']['status']}, ensure_ascii=False))
        return 2
    if args.validate_only:
        print(json.dumps({'status': 'validated_bookkeeping_only', 'checks': str(checks.resolve())}))
        return 0
    result = render_mechanism_canvas(spec)
    save('.checks.json', result['publication_checks'])
    if result['publication_checks']['blocking_issues']:
        print(json.dumps({'status': 'layout_blocked', 'checks': str(checks.resolve()),
                          'issues': result['publication_checks']['blocking_issues']}, ensure_ascii=False))
        return 2
    files = [save('.svg', result['svg']), save('.spec.json', spec),
             save('.trace.json', result['mechanism_trace']), save('.cdxml', result['cdxml']), checks]
    warnings = list(result.get('warnings', []))
    if args.png:
        png_path = Path(str(args.output) + '.png')
        warning = make_png(files[0], png_path)
        if warning:
            warnings.append(warning)
        else:
            files.append(png_path)
    print(json.dumps({'status': result['status'], 'rdkit_version': rdBase.rdkitVersion,
                      'scope': 'Electron bookkeeping and geometric checks only; requires chemical and visual review.',
                      'files': [str(p.resolve()) for p in files], 'warnings': warnings}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
