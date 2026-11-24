from hashlib import sha256
import json
import os
from pathlib import Path
from shutil import copy2, copytree
import subprocess
import sys
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
BACKUP = ROOT / '.agents/skills/postgres-backup/scripts/backup.py'


def main():
    with TemporaryDirectory(prefix='postgis-backup-test-') as temporary:
        project = Path(temporary) / 'project'
        environment = dict(os.environ, COMPOSE_PROJECT_NAME=Path(temporary).name.lower())
        project.mkdir()
        copy2(ROOT / 'compose.yaml', project)
        copytree(ROOT / 'docker', project / 'docker')
        (project / 'compose.override.yaml').write_text(
            'services:\n  db:\n    ports: !reset []\n', encoding='utf-8'
        )
        (project / '.secrets').mkdir()
        (project / '.secrets/.postgres').write_text(
            'POSTGRES_USER=postgres\nPOSTGRES_PASSWORD=temporary-test-password\n', encoding='utf-8'
        )

        def compose(*arguments, **options):
            return subprocess.run(['docker', 'compose', *arguments], cwd=project, env=environment,
                                  check=True, **options)

        def sql(database, statement):
            return compose('exec', '-T', 'db', 'psql', '-XAt', '-v', 'ON_ERROR_STOP=1',
                           '-U', 'postgres', '-d', database, '-c', statement,
                           capture_output=True, text=True).stdout.strip()

        try:
            compose('up', '-d', '--wait', '--wait-timeout', '90')
            sql('geodata', 'CREATE TABLE sample (location geometry(Point, 4326)); '
                "INSERT INTO sample VALUES (ST_GeomFromText('POINT(7 51)', 4326));")
            external = Path(temporary) / 'external'
            external.mkdir()
            subprocess.run([sys.executable, str(BACKUP), '--project-dir', str(project),
                            '--external-dir', str(external)], env=environment, check=True)
            local, = (project / '.backup').iterdir()
            replica, = external.iterdir()
            assert local.name == replica.name
            manifest = json.loads((replica / 'manifest.json').read_text(encoding='utf-8'))
            assert set(manifest['sha256']) == {'geodata.dump', 'globals.sql'}
            for name, digest in manifest['sha256'].items():
                assert (local / name).read_bytes() == (replica / name).read_bytes()
                assert sha256((replica / name).read_bytes()).hexdigest() == digest

            sql('postgres', 'CREATE DATABASE restore_probe TEMPLATE template0;')
            with (replica / 'geodata.dump').open('rb') as archive:
                compose('exec', '-T', 'db', 'pg_restore', '-U', 'postgres', '-d', 'restore_probe',
                        '--exit-on-error', '--single-transaction', stdin=archive)
            assert sql('restore_probe', 'SELECT ST_AsEWKT(location) FROM sample;') == 'SRID=4326;POINT(7 51)'
            assert sql('restore_probe', "SELECT count(*) FROM pg_extension WHERE extname IN "
                       "('postgis', 'postgis_raster', 'postgis_topology', 'h3', 'h3_postgis');") == '5'
            print('PostgreSQL backup and external-copy restore passed.')
        finally:
            compose('down', '--rmi', 'local')


if __name__ == '__main__':
    main()
