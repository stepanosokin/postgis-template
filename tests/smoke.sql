\set ON_ERROR_STOP on

BEGIN;

DO $$
BEGIN
    IF current_database() <> 'geodata' OR current_setting('server_version_num')::integer / 10000 <> 18 THEN
        RAISE EXCEPTION 'Expected geodata on PostgreSQL 18';
    END IF;

    IF (SELECT count(*) FROM pg_extension
        WHERE extname IN ('postgis', 'postgis_raster', 'postgis_topology', 'h3', 'h3_postgis')) <> 5 THEN
        RAISE EXCEPTION 'Expected all five spatial extensions';
    END IF;

    IF to_regnamespace('tiger') IS NOT NULL OR to_regnamespace('test_h3') IS NOT NULL THEN
        RAISE EXCEPTION 'Expected a fresh database without demo schemas';
    END IF;
END;
$$;

\ir test_h3.sql

DO $$
BEGIN
    -- Reference point and expected index: https://github.com/uber/h3-go#quickstart
    IF (SELECT count(*) FROM test_h3.cell) <> 1 OR NOT EXISTS (
        SELECT FROM test_h3.cell
        WHERE h3_index::text = '8928308280fffff'
          AND resolution = 9
          AND ST_SRID(cell_geom) = 4326
          AND ST_IsValid(cell_geom)
          AND ST_Covers(cell_geom, point_geom)
    ) THEN
        RAISE EXCEPTION 'Expected the reference H3 cell to cover its input point';
    END IF;
END;
$$;

ROLLBACK;
