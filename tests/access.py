from pathlib import Path
from secrets import token_hex
from shutil import copy2, copytree
import subprocess
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / '.agents/skills/postgres-access/scripts'


def main():
    with TemporaryDirectory(prefix='postgis-access-') as temporary:
        project = Path(temporary)
        copy2(ROOT / 'compose.yaml', project)
        copytree(ROOT / 'docker', project / 'docker')
        (project / 'compose.override.yaml').write_text(
            'services:\n  db:\n    ports: !reset []\n', encoding='utf-8'
        )
        (project / '.secrets').mkdir()
        (project / '.secrets/.postgres').write_text(
            f'POSTGRES_USER=postgres\nPOSTGRES_PASSWORD={token_hex(32)}\n', encoding='utf-8'
        )

        command = ['docker', 'compose', '-p', f'postgis-access-{token_hex(6)}',
                   '-f', 'compose.yaml', '-f', 'compose.override.yaml']

        def compose(*arguments, **options):
            return subprocess.run([*command, *arguments], cwd=project, **options)

        def psql(login, *arguments, password=None, prompt_input=None, check=True):
            authentication = [] if password is None else [
                '-W', '-d', 'host=db dbname=geodata require_auth=scram-sha-256',
            ]
            return compose('exec', '-T', 'db', 'psql', '-XAt', '-v', 'ON_ERROR_STOP=1',
                           '-d', 'geodata', '-U', login, *authentication, *arguments,
                           input=prompt_input if password is None else password + '\n',
                           capture_output=True, text=True, check=check)

        def assert_denied(login, password, *statements):
            for statement in statements:
                result = psql(login, '-c', statement, password=password, check=False)
                assert result.returncode and 'permission denied' in result.stderr, (statement, result.stderr)

        def provision(login, *scripts, check=True, **variables):
            password = token_hex(32)
            settings = [part for key, value in variables.items() for part in ('-v', f'{key}={value}')]
            result = compose('exec', '-T', 'db', 'psql', '-X', '-v', 'ON_ERROR_STOP=1',
                             '-1', '-d', 'geodata', '-U', 'postgres', '-v', f'login={login}', *settings,
                             '-f', '/tmp/create-login.sql', *scripts,
                             input=f'{password}\n{password}\n', text=True, check=check)
            return password, result.returncode

        try:
            compose('up', '-d', '--wait', '--wait-timeout', '90', check=True)
            psql('postgres', '-c', '''
                CREATE SCHEMA maps;
                CREATE TABLE maps.layer (label text);
                INSERT INTO maps.layer VALUES ('allowed');
                CREATE TABLE maps.internal (label text);
            ''')
            for name in ('create-login.sql', 'grant-reader.sql'):
                compose('cp', str(SCRIPTS / name), f'db:/tmp/{name}', check=True)

            grants = ('-f', '/tmp/grant-reader.sql')
            password, _ = provision('reader_one', *grants, reader='reader_one', schema='maps', relation='layer')
            assert psql('reader_one', '-c', 'SELECT label FROM maps.layer;',
                        password=password).stdout.strip() == 'allowed'
            assert_denied('reader_one', password, 'SELECT * FROM maps.internal;',
                          "INSERT INTO maps.layer VALUES ('denied');", 'CREATE TABLE maps.denied (id int);')
            print('Personal geodata reader passed.')

            psql('postgres', '-c', '''
                CREATE ROLE shared_maps NOLOGIN;
                CREATE SCHEMA shared;
                CREATE TABLE shared.layer (label text);
                INSERT INTO shared.layer VALUES ('shared');
                CREATE SCHEMA current_only;
                CREATE TABLE current_only.layer (label text);
                INSERT INTO current_only.layer VALUES ('current');
            ''')
            psql('postgres', '-1', '-v', 'reader=shared_maps', '-v', 'schema=shared',
                 '-v', 'creator=postgres', '-c', 'CREATE TEMP TABLE pg_roles (id int);',
                 *grants, '-c', r'\set schema current_only', *grants)
            members = {
                login: provision(login, *grants, reader='shared_maps', member=login)[0]
                for login in ('reader_two', 'reader_three')
            }
            psql('postgres', '-c', '''
                CREATE TABLE shared.future (label text);
                INSERT INTO shared.future VALUES ('future');
                CREATE TABLE current_only.future (label text);
                CREATE TABLE maps.future (label text);
            ''')
            for login, password in members.items():
                assert psql(login, '-c', 'SELECT label FROM shared.layer;',
                            password=password).stdout.strip() == 'shared'
                assert psql(login, '-c', 'SELECT label FROM shared.future;',
                            password=password).stdout.strip() == 'future'
                assert psql(login, '-c', 'SELECT label FROM current_only.layer;',
                            password=password).stdout.strip() == 'current'
                assert_denied(login, password, 'SELECT * FROM maps.future;', 'SET ROLE shared_maps;',
                              'SELECT * FROM current_only.future;', "INSERT INTO shared.layer VALUES ('denied');")
            group = psql('postgres', '-c', "SELECT rolcanlogin FROM pg_roles WHERE rolname = 'shared_maps';")
            assert group.stdout.strip() == 'f'
            print('Shared geodata reader role passed.')

            password = token_hex(32)
            next_password = token_hex(32)
            create_login = ('-f', '/tmp/create-login.sql')
            psql('postgres', '-1', '-v', 'login=personal_admin', '-v', 'administrator=on',
                 '-c', 'CREATE TEMP TABLE pg_authid (id int);', *create_login,
                 '-c', r'\set login next_login', *create_login,
                 prompt_input=f'{password}\n{password}\n{next_password}\n{next_password}\n')
            admin = psql('personal_admin', '-c', 'SHOW is_superuser;', password=password)
            assert admin.stdout.strip() == 'on', admin.stdout
            next_login = psql('next_login', '-c', 'SHOW is_superuser;', password=next_password)
            assert next_login.stdout.strip() == 'off', next_login.stdout
            owner = psql('personal_admin', '-c', "SELECT pg_get_userbyid(datdba) FROM pg_database "
                         "WHERE datname = current_database();", password=password)
            assert owner.stdout.strip() == 'postgres'
            _, status = provision('failed_reader', *grants, check=False,
                                  reader='failed_reader', schema='maps', relation='missing')
            assert status != 0
            missing = psql('postgres', '-c', "SELECT 1 FROM pg_roles WHERE rolname = 'failed_reader';")
            assert not missing.stdout.strip()
            _, status = provision('reader_one', administrator='on', check=False)
            assert status != 0
            unchanged = psql('postgres', '-c', "SELECT rolsuper FROM pg_roles WHERE rolname = 'reader_one';")
            assert unchanged.stdout.strip() == 'f'
            print('Personal administrator and rollback boundaries passed.')
        finally:
            compose('down', '--rmi', 'local', check=True)


if __name__ == '__main__':
    main()
