"""Build a portable skill ZIP and a SHA-256 checksum without local runtime data."""
import argparse
import hashlib
from pathlib import Path
import re
import shutil
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
    package = {'organic-chem-review/' + name: path for name, path in entries.items()}
    def write_zip(path, files):
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
            for name, source in sorted(files.items()):
                info = zipfile.ZipInfo(name, date_time=(2026, 11, 12, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                z.writestr(info, source.read_bytes())
        with zipfile.ZipFile(path) as z:
            if z.testzip() is not None:
                raise RuntimeError('ZIP integrity check failed')
    write_zip(archive, package)
    chat_archive = output / f'organic-chem-review-chat-v{version}.zip'
    chat_files = {**package, 'CHAT_START.md': root / 'chat/CHAT_START.md'}
    chat_files.update({'examples/' + p.name: p for p in (root / 'examples').glob('*.png')})
    write_zip(chat_archive, chat_files)
    starter = output / 'CHAT_START.md'
    shutil.copy2(root / 'chat/CHAT_START.md', starter)
    artifacts = [archive, chat_archive, starter]
    checksums = []
    for path in artifacts:
        checksums.append(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n')
        print(path)
    (output / 'SHA256SUMS.txt').write_text(''.join(checksums), encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', default='1.1.0')
    build(parser.parse_args().version)
