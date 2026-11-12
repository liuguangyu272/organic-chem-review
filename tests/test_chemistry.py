"""Reproducible software checks, not a study of educational or chemical accuracy."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
import xml.etree.ElementTree as ET

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/organic-chem-review'
sys.path.insert(0, str(SKILL / 'scripts/vendor'))
from codex_organic_chem.mechanism_canvas import render_mechanism_canvas, validate_mechanism_spec


def run_script(name, *args):
    return subprocess.run([sys.executable, '-X', 'utf8', str(SKILL / 'scripts' / name), *map(str, args)],
                          capture_output=True, text=True, encoding='utf-8')


class ChemistryChecks(unittest.TestCase):
    def test_session_probe_actually_renders(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run_script('session_probe.py', '--output', directory)
            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(result.stdout)
            self.assertEqual(summary['status'], 'structure_rendering_verified')
            report = json.loads((Path(directory) / 'session-check.json').read_text(encoding='utf-8'))
            self.assertEqual(len(report['generated_files']), 3)
            for path in report['generated_files']:
                self.assertTrue(Path(path).is_file())

    def test_session_probe_reports_missing_dependencies(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, '-S', str(SKILL / 'scripts/session_probe.py'),
                                     '--output', directory], capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(result.returncode, 2, result.stderr)
            summary = json.loads(result.stdout)
            self.assertEqual(summary['status'], 'dependencies_unavailable')
            self.assertEqual(summary['files'], [])

    def test_attachment_package_runs_after_extraction(self):
        built = subprocess.run([sys.executable, str(ROOT / 'scripts/build_release.py')], capture_output=True)
        self.assertEqual(built.returncode, 0, built.stderr)
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            archive = ROOT / 'dist/organic-chem-review-chat-v1.1.0.zip'
            with zipfile.ZipFile(archive) as z:
                for name in z.namelist():
                    self.assertFalse(Path(name).is_absolute())
                    self.assertNotIn('..', Path(name).parts)
                z.extractall(folder)
            self.assertTrue((folder / 'CHAT_START.md').is_file())
            command = [sys.executable, str(folder / 'organic-chem-review/scripts/session_probe.py'),
                       '--output', str(folder / 'runtime-check')]
            result = subprocess.run(command, cwd=folder, capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['status'], 'structure_rendering_verified')

    def test_structures_preserve_charge_and_stereo(self):
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory) / 'structures'
            args = ['--output', prefix]
            for smiles in ('c1ccccc1', '[NH4+]', 'C[C@H](O)C(=O)O', 'C[C@@H](O)C(=O)O', 'C/C=C/C', 'C/C=C\\C'):
                args += ['--smiles', smiles]
            result = run_script('render_structures.py', *args)
            self.assertEqual(result.returncode, 0, result.stderr)
            mols = json.loads(prefix.with_suffix('.json').read_text(encoding='utf-8'))['molecules']
            self.assertEqual(mols[0]['formula'], 'C6H6')
            self.assertEqual(mols[1]['formal_charge'], 1)
            self.assertEqual({mols[i]['chiral_centers'][0]['assignment'] for i in (2, 3)}, {'R', 'S'})
            self.assertEqual({mols[i]['specified_bond_stereo'][0]['cip'] for i in (4, 5)}, {'E', 'Z'})
            with Image.open(prefix.with_suffix('.png')) as image:
                self.assertEqual(image.size, (1140, 580))
                image.verify()

    def test_json_input_does_not_invent_stereochemistry(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            source = folder / 'input.json'
            source.write_text(json.dumps([{'smiles': 'CC(O)C(=O)O', 'label': 'A'}]), encoding='utf-8')
            result = run_script('render_structures.py', '--input', source, '--output', folder / 'result', '--atom-indices')
            self.assertEqual(result.returncode, 0, result.stderr)
            mol = json.loads((folder / 'result.json').read_text(encoding='utf-8'))['molecules'][0]
            self.assertEqual(mol['chiral_centers'][0]['assignment'], '?')

    def test_invalid_valence_writes_no_structure(self):
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory) / 'invalid'
            result = run_script('render_structures.py', '--smiles', 'CO(C)C', '--output', prefix)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(any(prefix.with_suffix(s).exists() for s in ('.png', '.svg', '.json')))

    def test_five_mechanism_classes_and_roundtrip(self):
        for path in sorted((SKILL / 'assets/mechanisms').glob('*.json')):
            with self.subTest(mechanism=path.stem):
                spec = json.loads(path.read_text(encoding='utf-8'))
                result = render_mechanism_canvas(spec)
                self.assertEqual(result['semantic_checks']['status'], 'valid')
                self.assertFalse(result['publication_checks']['blocking_issues'])
                metadata = ET.fromstring(result['svg']).find('{http://www.w3.org/2000/svg}metadata')
                bundle = json.loads(metadata.text)
                self.assertEqual(bundle['spec'], spec)
                self.assertEqual(bundle['trace'], result['mechanism_trace'])
                digest = hashlib.sha256(json.dumps(spec, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
                self.assertEqual(bundle['trace']['source_spec_sha256'], digest)

    def test_seven_inconsistent_mechanisms_are_blocked(self):
        sn2 = json.loads((SKILL / 'assets/mechanisms/sn2.json').read_text(encoding='utf-8'))
        mutations = {
            'missing_arrow': lambda p: p['arrows'].pop(),
            'wrong_attack_target': lambda p: p['arrows'][0].update(to_atom_map=3),
            'hydrogen_charge_imbalance': lambda p: p['molecules'][2].update(smiles='[OH2+:1][CH3:2]'),
            'wrong_element': lambda p: p['molecules'][3].update(smiles='[Cl-:3]'),
            'duplicate_map': lambda p: p['molecules'][0].update(smiles='[OH-:2]'),
            'nonexistent_source_bond': lambda p: p['arrows'][1].update(from_bond=[1, 3]),
            'wrong_electron_count': lambda p: p['arrows'][0].update(electron_count=1),
        }
        for name, mutate in mutations.items():
            with self.subTest(error=name):
                spec = copy.deepcopy(sn2)
                mutate(spec['panels'][0])
                self.assertTrue(validate_mechanism_spec(spec)['blocking_issues'])

    def test_cli_blocks_inconsistent_mechanism(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            spec = json.loads((SKILL / 'assets/mechanisms/sn2.json').read_text(encoding='utf-8'))
            spec['panels'][0]['arrows'].pop()
            source = folder / 'bad.json'
            source.write_text(json.dumps(spec), encoding='utf-8')
            result = run_script('mechanism_tools.py', '--spec', source, '--output', folder / 'invalid')
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(json.loads(result.stdout)['status'], 'blocked')
            self.assertFalse((folder / 'invalid.svg').exists())


if __name__ == '__main__':
    unittest.main()
