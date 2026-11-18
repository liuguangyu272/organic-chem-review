"""Validate explicit, mapped elementary steps and render supported mechanisms.

The supplied mechanism is a hypothesis. Passing these checks is not experimental proof.
Requires RDKit; uses a bundled MIT-licensed community mechanism core.
"""

import argparse
import copy
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET


def prepare_view(spec, view='teaching', panel=None):
    """Presentation only: preserve chemistry; optionally reveal one original step."""
    spec = copy.deepcopy(spec)
    if panel is not None:
        panels = spec.get('panels', [])
        if not 1 <= panel <= len(panels):
            raise ValueError(f'Panel must be between 1 and {len(panels)}')
        spec['panels'] = [panels[panel - 1]]
    if view == 'teaching':
        spec['presentation_mode'] = 'teaching'
        spec.pop('presentation', None)
        layout = spec.setdefault('layout', {})
        layout.update(show_title=False, show_subtitle=False, show_panel_titles=True,
                      show_molecule_labels=True, show_arrow_labels=True,
                      show_partial_charges=True, show_formal_charges=True,
                      show_notes=True, show_footer=False, show_atom_maps=False,
                      font_family='Arial,"Microsoft YaHei","Noto Sans CJK SC",sans-serif')
    return spec


def make_png(svg_path, png_path):
    """Prefer a local converter, then isolated headless Chromium; no personal profile."""
    root = ET.parse(svg_path).getroot()
    viewbox = root.get('viewBox', '').replace(',', ' ').split()
    def dimension(name, fallback):
        raw = root.get(name, '').rstrip('px')
        try:
            return max(1, math.ceil(float(raw)))
        except ValueError:
            return max(1, math.ceil(float(fallback)))
    width = dimension('width', viewbox[2] if len(viewbox) == 4 else 1000)
    height = dimension('height', viewbox[3] if len(viewbox) == 4 else 600)
    try:
        import cairosvg
        content = svg_path.read_text(encoding='utf-8')
        cairosvg.svg2png(bytestring=content.encode('utf-8'), write_to=str(png_path),
                        output_width=width * 2, output_height=height * 2)
        return None
    except (ImportError, OSError, ValueError):
        pass
    candidates = [shutil.which(n) for n in ('chromium', 'chromium-browser', 'google-chrome', 'msedge')]
    for variable in ('PROGRAMFILES(X86)', 'PROGRAMFILES', 'LOCALAPPDATA'):
        browser_root = os.environ.get(variable)
        if browser_root:
            candidates.extend([str(Path(browser_root) / 'Microsoft/Edge/Application/msedge.exe'),
                               str(Path(browser_root) / 'Google/Chrome/Application/chrome.exe')])
    browser = next((p for p in candidates if p and Path(p).is_file()), None)
    if not browser:
        return 'PNG preview unavailable: no local Chromium/Edge/Chrome; SVG was generated.'
    with tempfile.TemporaryDirectory(prefix='organic-chem-preview-') as profile:
        try:
            # A browser enforces a minimum viewport. An exact-sized SVG in a
            # marginless document avoids stretching width='100%' and clipping
            # narrow figures; crop the screenshot to the declared drawing size.
            root.set('width', str(width))
            root.set('height', str(height))
            ET.register_namespace('', 'http://www.w3.org/2000/svg')
            document = Path(profile) / 'preview.html'
            document.write_text('<!doctype html><meta charset="utf-8"><style>html,body{margin:0;background:white}svg{display:block}</style>'
                                + ET.tostring(root, encoding='unicode'), encoding='utf-8')
            screenshot = Path(profile) / 'preview.png'
            result = subprocess.run([
                browser, '--headless', '--disable-gpu', '--no-first-run', '--hide-scrollbars',
                '--force-device-scale-factor=2', '--no-default-browser-check',
                f'--user-data-dir={profile}', f'--window-size={max(500,width)},{max(500,height)}',
                f'--screenshot={screenshot}', document.resolve().as_uri(),
            ], capture_output=True, timeout=45,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            if result.returncode or not screenshot.is_file():
                return 'PNG preview failed; the SVG and validation record remain available.'
            from PIL import Image
            with Image.open(screenshot) as preview:
                if preview.width < width * 2 or preview.height < height * 2:
                    return 'PNG preview failed: screenshot smaller than the figure.'
                preview.crop((0, 0, width * 2, height * 2)).save(png_path)
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
    png = parser.add_mutually_exclusive_group()
    png.add_argument('--png', dest='png', action='store_true', default=True,
                     help='Render an inline PNG preview (default)')
    png.add_argument('--no-png', dest='png', action='store_false', help='Skip PNG for validation/batch use')
    parser.add_argument('--view', choices=['teaching', 'source'], default='teaching',
                        help='Show teaching annotations by default; source preserves supplied display settings')
    parser.add_argument('--panel', type=int, help='Show only this 1-based step, without revealing later steps')
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
        spec = prepare_view(spec, args.view, args.panel)
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
