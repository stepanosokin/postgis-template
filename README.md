# PostgreSQL / PostGIS

Один контейнер с PostgreSQL 18.7, PostGIS 3.7 и базой `geodata`. Шаблон рассчитан на Linux и Windows с Docker Desktop в режиме Linux-контейнеров на x86‑64. Нужен Docker Compose 2.30 или новее для `env_file` с `format: raw`.

## Запуск

1. В корне проекта создайте папку `.secrets` и UTF-8-файл `.secrets/.postgres` со следующим содержимым.

   ```dotenv
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=<ваш-длинный-уникальный-пароль>
   ```

   Замените значение пароля целиком. Compose читает его буквально, поэтому добавляйте кавычки только если они входят в пароль.

2. Запустите сервис из корня проекта. Команда при первом запуске соберёт образ.

   ```sh
   docker compose up -d
   docker compose ps
   ```

3. После появления статуса `healthy` подключитесь к базе `geodata` на порту `5432` под пользователем `postgres`. На том же компьютере используйте `localhost`, на другом — адрес Docker-хоста. Порт публикуется на всех интерфейсах хоста. Для доступа из сети ограничьте входящие подключения доверенными клиентами на границе сети.

Чтобы остановить сервер и сохранить контейнер, выполните `docker compose stop db`. Для повторного запуска используйте `docker compose start db`.

Чтобы удалить контейнер и сеть проекта, выполните `docker compose down`. Данные в `./postgres`, секреты и резервные копии останутся на диске. Команда `docker compose up -d` заново создаст контейнер с сохранёнными данными.

## Как устроен сервер

`docker/Dockerfile` расширяет Debian-образ `postgis/postgis:18-3.7` пакетом `postgresql-18-h3`. При первом запуске на пустой папке данных образ создаёт `geodata` с `postgis` и `postgis_topology`, а `docker/20-extensions.sql` включает `postgis_raster`, `h3` и `h3_postgis` в той же базе. В комплекте нет набора Tiger.

Папка проекта `./postgres` подключается к `/var/lib/postgresql`. При следующих запусках PostgreSQL использует уже созданную базу. Файл `.secrets/.postgres` задаёт пароль при создании базы. Для существующей базы смените пароль средствами PostgreSQL и обновите файл. Основную версию PostgreSQL меняйте через [миграцию данных](https://www.postgresql.org/support/versioning/#upgrading).

Git игнорирует `./postgres` и `.secrets`. В контекст сборки попадают только файлы из `./docker`.

## Пример `test_h3`

Запустите `examples/test_h3.sql` в базе `geodata`, когда нужен пример работы H3. Из корня проекта это можно сделать так:

```sh
docker compose cp examples/test_h3.sql db:/tmp/test_h3.sql
docker compose exec -T db psql -X -U postgres -d geodata -v ON_ERROR_STOP=1 -f /tmp/test_h3.sql
```

Схема содержит одно представление `test_h3.cell`. Оно возвращает исходную точку WGS 84 (`point_geom`), разрешение H3 (`resolution`), индекс ячейки (`h3_index`) и геометрию её границы (`cell_geom`). Достаточно выполнить `SELECT * FROM test_h3.cell;`. Координаты и ожидаемый индекс взяты из [примера H3](https://github.com/uber/h3-go#quickstart).

## Память и файловая система Docker

- На Windows для более быстрой работы bind mount разместите проект в файловой системе WSL 2 и запускайте Compose из WSL. Если сервер уже работает, остановите его перед переносом проекта вместе с папкой `postgres`. При нехватке памяти проверьте лимиты WSL 2 в `%UserProfile%\.wslconfig`. После изменения лимитов перезапустите WSL и Docker Desktop. [Рекомендации Docker по WSL 2](https://docs.docker.com/desktop/features/wsl/best-practices/) · [Настройки памяти WSL](https://learn.microsoft.com/en-us/windows/wsl/wsl-config#wslconfig)
- На Linux храните `postgres` на локальной файловой системе. При завершении контейнера по OOM проверьте доступную память хоста и потребление через `docker stats`.
- Сервису выделено 128 МБ для `/dev/shm`. Если PostgreSQL сообщает `could not resize shared memory segment` и `No space left on device` при запросах, проверьте `/dev/shm` и при необходимости увеличьте `shm_size` в `compose.yaml`.

## Локальная проверка

На свежем экземпляре дождитесь статуса `healthy` и запустите проверку.

```sh
docker compose cp examples/test_h3.sql db:/tmp/test_h3.sql
docker compose cp tests/smoke.sql db:/tmp/smoke.sql
docker compose exec -T db psql -X -U postgres -d geodata -f /tmp/smoke.sql
```

Тест проверяет расширения, отсутствие демонстрационных схем при запуске и результат примера H3. Изменения теста откатываются транзакцией.

## Обслуживание

- [`$postgres-lifecycle`](.agents/skills/postgres-lifecycle/SKILL.md) выполняет первоначальное развёртывание, запуск, остановку и удаление развёртывания.

- [`$postgres-upgrade`](.agents/skills/postgres-upgrade/SKILL.md) сверяет версии, анализирует рекомендации и отзывы, готовит решение и выполняет согласованное обновление с пробным восстановлением и возможностью отката.
- [`$postgres-backup`](.agents/skills/postgres-backup/SKILL.md) создаёт проверяемые копии в `.backup`, поддерживает внешнее хранилище, восстановление и расписания через cron или Планировщик заданий Windows. Для скрипта резервного копирования нужен Python 3.11 или новее.
- [`$postgres-access`](.agents/skills/postgres-access/SKILL.md) локально создаёт личные логины для чтения `geodata` из QGIS и, по явному запросу, персональный вход суперпользователя. Права и новые подключения проверяются на той же площадке.

Отдельный тест резервного копирования запускается командой `python tests/backup_restore.py`. Он создаёт временный Compose-проект без публикации порта и восстанавливает геоданные из внешней копии в отдельную базу.

Тест `python tests/access.py` проверяет подключение и права читателей и персонального администратора на временном Compose-экземпляре.
