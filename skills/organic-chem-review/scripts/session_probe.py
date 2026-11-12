"""Run an actual structure-rendering check in the current Python process's environment.

This does not register a ChatGPT skill or prove which chat product executed it.
"""
import argparse
import importlib
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='Directory for probe artifacts')
    args = parser.parse_args()
    folder = args.output.resolve()
    folder.mkdir(parents=True, exist_ok=True)
    report = {
        'schema': 'organic-chem-review.session-probe.v1',
        'python_version': sys.version.split()[0],
        'scope': 'This Python environment only; not proof of execution in a particular ChatGPT session.',
        'rdkit_version': None,
        'status': 'not_checked',
        'generated_files': [],
    }
    code = 0
    try:
        rdkit = importlib.import_module('rdkit')
        report['rdkit_version'] = rdkit.__version__
        importlib.import_module('PIL.Image')
    except (ImportError, OSError) as exc:
        report.update(status='dependencies_unavailable', detail=str(exc))
        code = 2
    else:
        prefix = folder / 'probe-structure'
        command = [sys.executable, '-X', 'utf8', str(Path(__file__).with_name('render_structures.py')),
                   '--smiles', 'C=CC=O', '--label', 'Acrolein', '--output', str(prefix)]
        try:
            result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', timeout=45)
            if result.returncode:
                raise RuntimeError(result.stderr.strip() or 'Structure renderer failed')
            audit = json.loads(Path(str(prefix) + '.json').read_text(encoding='utf-8'))
            if audit['molecules'][0]['formula'] != 'C3H4O':
                raise RuntimeError('Probe molecule did not match the expected molecular formula')
            from PIL import Image
            with Image.open(Path(str(prefix) + '.png')) as image:
                image.verify()
            report.update(status='structure_rendering_verified', generated_files=[
                str(Path(str(prefix) + suffix)) for suffix in ('.svg', '.png', '.json')])
        except (OSError, ValueError, KeyError, RuntimeError, subprocess.TimeoutExpired) as exc:
            report.update(status='rendering_failed', detail=str(exc))
            code = 3
    path = folder / 'session-check.json'
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'report': str(path),
                      'rdkit_version': report['rdkit_version'], 'files': report['generated_files']}, ensure_ascii=False))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
