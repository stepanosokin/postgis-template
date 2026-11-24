# PostgreSQL 18 для базового образа

Шаблон использует `postgis/postgis:18-3.7`. На 24 ноября 2026 года PostgreSQL 19.0 был доступен пять дней, а команда PostGIS рекомендовала ветку 18 для рабочих нагрузок. Мы выбрали более зрелую ветку, поскольку переход на следующую основную версию с данными в `./postgres` потребует миграции базы.

[Релиз PostgreSQL 19.0](https://www.postgresql.org/docs/release/19.0/) · [Рекомендация команды PostGIS](https://hub.docker.com/r/postgis/postgis)
