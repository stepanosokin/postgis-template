"""Create a PostgreSQL backup bundle or verify a bundle before restoring it."""

import argparse
from datetime import datetime, timezone
from hashlib import file_digest
import json
from pathlib import Path
from shutil import copy2
import subprocess
import sys
from tempfile import TemporaryDirectory
from uuid import uuid4


FILES = ('geodata.dump', 'globals.sql')
MANIFEST = 'manifest.json'


def checksums(bundle):
    result = {}
    for name in FILES:
        with (bundle / name).open('rb') as stream:
            result[name] = file_digest(stream, 'sha256').hexdigest()
    return result


def verify(bundle):
    manifest = json.loads((bundle / MANIFEST).read_text(encoding='utf-8'))
    if not isinstance(manifest, dict) or checksums(bundle) != manifest.get('sha256'):
        raise ValueError(f'Backup checksum mismatch in {bundle}')


def publish(parent, name, populate):
    with TemporaryDirectory(prefix='.partial-', dir=parent) as temporary:
        stage = Path(temporary) / name
        stage.mkdir(mode=0o700)
        populate(stage)
        complete = parent / name
        stage.rename(complete)
        return complete


def dump(project, docker, stage):
    commands = (
        'exec pg_dump --no-password --username "$POSTGRES_USER" --dbname geodata --format custom',
        'exec pg_dumpall --no-password --username "$POSTGRES_USER" --database geodata --globals-only',
    )
    running = subprocess.check_output([docker, 'compose', 'ps', '--status', 'running', '-q', 'db'],
                                      cwd=project, text=True).split()
    if len(running) != 1:
        raise ValueError('Expected exactly one running Compose db container')
    container, = running
    for name, command in zip(FILES, commands):
        with (stage / name).open('wb') as stream:
            subprocess.run([docker, 'exec', container, 'sh', '-ec', command], cwd=project,
                           stdout=stream, check=True)
        if not (stage / name).stat().st_size:
            raise ValueError(f'PostgreSQL returned an empty {name}')

    with (stage / FILES[0]).open('rb') as archive:
        subprocess.run([docker, 'exec', '-i', container, 'pg_restore', '--list'], cwd=project, stdin=archive,
                       stdout=subprocess.DEVNULL, check=True)

    manifest = {'created_at': datetime.now(timezone.utc).isoformat(), 'sha256': checksums(stage)}
    (stage / MANIFEST).write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')


def replicate(local, external):
    external = external.resolve(strict=True)
    if not external.is_dir() or external.is_relative_to(local.parent.resolve()):
        raise ValueError('External storage must be a directory outside the local backup directory')

    def copy_bundle(stage):
        for name in (*FILES, MANIFEST):
            copy2(local / name, stage / name)
        verify(stage)

    return publish(external, local.name, copy_bundle)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--project-dir', type=Path, help='Directory containing compose.yaml')
    mode.add_argument('--verify', type=Path, help='Backup bundle directory to verify')
    parser.add_argument('--external-dir', type=Path, help='Existing mounted disk or network share')
    parser.add_argument('--docker', default='docker', help='Docker executable or absolute path')
    args = parser.parse_args()

    try:
        if args.verify:
            if args.external_dir:
                parser.error('--external-dir requires --project-dir')
            verify(args.verify)
            print(f'Checksums verified: {args.verify}')
        else:
            project = args.project_dir.resolve(strict=True)
            if not (project / 'compose.yaml').is_file():
                raise ValueError(f'Compose file not found in {project}')
            parent = project / '.backup'
            parent.mkdir(mode=0o700, exist_ok=True)
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
            name = f'{timestamp}-{uuid4().hex}'
            local = publish(parent, name, lambda stage: dump(project, args.docker, stage))
            print(f'Local backup: {local}', flush=True)
            if args.external_dir:
                print(f'External backup: {replicate(local, args.external_dir)}')
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f'Backup failed: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
