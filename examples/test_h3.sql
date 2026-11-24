CREATE SCHEMA IF NOT EXISTS test_h3;

CREATE OR REPLACE VIEW test_h3.cell AS
WITH sample AS (
    SELECT ST_SetSRID(ST_MakePoint(-122.41795063018799, 37.775938728915946), 4326) AS point_geom,
           9 AS resolution
), indexed AS (
    SELECT point_geom, resolution, h3_latlng_to_cell(point_geom, resolution) AS h3_index
    FROM sample
)
SELECT point_geom, resolution, h3_index, h3_cell_to_boundary_geometry(h3_index) AS cell_geom
FROM indexed;
