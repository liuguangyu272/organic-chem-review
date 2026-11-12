"""Build a portable skill ZIP and a SHA-256 checksum without local runtime data."""
import argparse
import hashlib
from pathlib import Path
import re
import zipfile


def build(version):
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise ValueError('Version must use major.minor.patch')
    root = Path(__file__).resolve().parents[1]
    skill = root / 'skills/organic-chem-review'
    output = root / 'dist'
    output.mkdir(exist_ok=True)
    archive = output / f'organic-chem-review-v{version}.zip'
    entries = {p.relative_to(skill).as_posix(): p for p in skill.rglob('*')
               if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
    entries.update({'LICENSE': root / 'LICENSE', 'THIRD_PARTY_NOTICES.md': root / 'THIRD_PARTY_NOTICES.md'})
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, path in sorted(entries.items()):
            info = zipfile.ZipInfo('organic-chem-review/' + name, date_time=(2026, 11, 12, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, path.read_bytes())
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise RuntimeError('ZIP integrity check failed')
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (output / 'SHA256SUMS.txt').write_text(f'{digest}  {archive.name}\n', encoding='utf-8')
    print(archive)
    print(digest)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', default='1.0.0')
    build(parser.parse_args().version)
