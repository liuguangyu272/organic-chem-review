"""Render validated SMILES as SVG + PNG, with an assistant-side audit record.

Requires RDKit. This generates molecular depictions, not reaction predictions.
"""

import argparse
import json
import math
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--smiles', action='append', help='Repeat for multiple molecules')
    source.add_argument('--input', type=Path, help='UTF-8 JSON array of smiles/label objects')
    parser.add_argument('--label', action='append', help='Short legend; one per SMILES')
    parser.add_argument('--output', type=Path, required=True, help='Output filename prefix')
    parser.add_argument('--columns', type=int, default=3)
    parser.add_argument('--atom-indices', action='store_true')
    args = parser.parse_args()
    if not 1 <= args.columns <= 6:
        parser.error('--columns must be between 1 and 6')
    if args.input and args.label:
        parser.error('Put labels in the JSON when using --input')
    try:
        from rdkit import Chem, rdBase
        from rdkit.Chem import rdDepictor, rdMolDescriptors, rdCIPLabeler
        from rdkit.Chem.Draw import rdMolDraw2D
    except ImportError as exc:
        parser.exit(2, f'RDKit is required in this Python environment: {exc}\n')

    if args.input:
        try:
            entries = json.loads(args.input.read_text(encoding='utf-8-sig'))
        except (OSError, ValueError) as exc:
            parser.error(f'Cannot read input JSON: {exc}')
    else:
        if args.label and len(args.label) != len(args.smiles):
            parser.error('Supply one --label per --smiles, or omit all labels')
        labels = args.label or [str(i + 1) for i in range(len(args.smiles))]
        entries = [dict(smiles=s, label=l) for s, l in zip(args.smiles, labels)]
    if not isinstance(entries, list) or not entries or len(entries) > 30:
        parser.error('Input must be a nonempty array of at most 30 molecules')

    molecules, legends, audit = [], [], []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            parser.error(f'Entry {index + 1} must be an object')
        smiles = entry.get('smiles')
        label = entry.get('label', str(index + 1))
        if not isinstance(smiles, str) or not smiles.strip():
            parser.error(f'Entry {index + 1} needs a nonempty SMILES string')
        if not isinstance(label, str) or len(label) > 60 or '\n' in label:
            parser.error(f'Entry {index + 1} needs a single-line label of at most 60 characters')
        # Disable trailing-name parsing so a malformed input is not silently truncated.
        options = Chem.SmilesParserParams()
        options.parseName = False
        mol = Chem.MolFromSmiles(smiles, options)
        if mol is None or not mol.GetNumAtoms():
            parser.error(f'Entry {index + 1}: invalid SMILES; no structures were written')
        Chem.AssignStereochemistry(mol, cleanIt=True, force=True)
        chiral = Chem.FindMolChiralCenters(mol, includeUnassigned=True, useLegacyImplementation=False)
        rdCIPLabeler.AssignCIPLabels(mol)
        rdDepictor.Compute2DCoords(mol)
        audit.append({
            'label': label,
            'input_smiles': smiles,
            'isomeric_smiles': Chem.MolToSmiles(mol, isomericSmiles=True),
            'formula': rdMolDescriptors.CalcMolFormula(mol),
            'formal_charge': Chem.GetFormalCharge(mol),
            'chiral_centers': [{'atom_index': i, 'assignment': tag} for i, tag in chiral],
            'specified_bond_stereo': [
                {'bond_index': b.GetIdx(), 'stereo': str(b.GetStereo()),
                 'cip': b.GetProp('_CIPCode') if b.HasProp('_CIPCode') else None}
                for b in mol.GetBonds() if b.GetStereo() != Chem.BondStereo.STEREONONE
            ],
        })
        molecules.append(mol)
        legends.append(label)

    # All input structures are validated before creating output files.
    columns = min(args.columns, len(molecules))
    rows = math.ceil(len(molecules) / columns)
    panel_width, panel_height = 380, 290
    size = (columns * panel_width, rows * panel_height, panel_width, panel_height)
    svg_drawer = rdMolDraw2D.MolDraw2DSVG(*size)
    png_drawer = rdMolDraw2D.MolDraw2DCairo(*size)
    for drawer in (svg_drawer, png_drawer):
        drawer.drawOptions().addAtomIndices = args.atom_indices
        drawer.drawOptions().padding = 0.12
        drawer.DrawMolecules(molecules, legends=legends)
        drawer.FinishDrawing()

    prefix = args.output
    prefix.parent.mkdir(parents=True, exist_ok=True)
    svg_path, png_path, audit_path = [Path(str(prefix) + suffix) for suffix in ('.svg', '.png', '.json')]
    svg_path.write_text(svg_drawer.GetDrawingText(), encoding='utf-8')
    png_path.write_bytes(png_drawer.GetDrawingText())
    audit_path.write_text(json.dumps({
        'rdkit_version': rdBase.rdkitVersion,
        'note': 'Parsed structures only; verify against the question. Not reaction validation.',
        'atom_index_base': 0,
        'molecules': audit,
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'svg': str(svg_path.resolve()), 'png': str(png_path.resolve()),
                      'audit': str(audit_path.resolve())}, ensure_ascii=False))


if __name__ == '__main__':
    main()
