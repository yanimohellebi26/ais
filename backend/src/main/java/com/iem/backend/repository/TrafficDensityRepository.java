package com.iem.backend.repository;

import com.iem.backend.entity.PositionVessel;
import com.iem.backend.repository.projection.TrafficDensityProjection;
import org.springframework.data.jpa.repository.JpaRepository;

import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.sql.Timestamp;
import java.util.List;

public interface TrafficDensityRepository extends JpaRepository<PositionVessel, Long> {

    @Query(value = """
        WITH snapped AS (
            SELECT
                ST_SnapToGrid(lp.geom::geometry, :gridSize) AS cell
            FROM latest_positions lp
            WHERE lp.geom::geometry && ST_MakeEnvelope(:minLon, :minLat, :maxLon, :maxLat, 4326)
        )
        SELECT
            ST_Y(cell) + (:gridSize / 2) AS lat,
            ST_X(cell) + (:gridSize / 2 / COS(RADIANS(ST_Y(cell)))) AS lon,
            COUNT(*) AS density
        FROM snapped
        GROUP BY cell
        ORDER BY density DESC
        """, nativeQuery = true)
    List<TrafficDensityProjection> findTrafficDensityLatest(
            @Param("minLat") double minLat,
            @Param("maxLat") double maxLat,
            @Param("minLon") double minLon,
            @Param("maxLon") double maxLon,
            @Param("gridSize") double gridSize
    );

    @Query(value = """
        WITH latest_position_vessel AS (
            SELECT DISTINCT ON (p.vessel_id)
                p.vessel_id, p.geom, p.base_date_time
            FROM position_vessel p
            WHERE p.base_date_time BETWEEN :dateStart AND :dateEnd
                AND p.geom::geometry && ST_MakeEnvelope(:minLon, :minLat, :maxLon, :maxLat, 4326)
            ORDER BY p.vessel_id, p.base_date_time DESC
        ),
        snapped AS (
            SELECT ST_SnapToGrid(geom::geometry, :gridSize) AS cell
            FROM latest_position_vessel
        )
        SELECT
            ST_Y(cell) + (:gridSize / 2) AS lat,
            ST_X(cell) + (:gridSize / 2 / COS(RADIANS(ST_Y(cell)))) AS lon,
            COUNT(*) AS density
        FROM snapped
        GROUP BY cell
        ORDER BY density DESC
        """, nativeQuery = true)
    List<TrafficDensityProjection> findTrafficDensityByDate(
            @Param("minLat") double minLat,
            @Param("maxLat") double maxLat,
            @Param("minLon") double minLon,
            @Param("maxLon") double maxLon,
            @Param("dateStart") Timestamp dateStart,
            @Param("dateEnd") Timestamp dateEnd,
            @Param("gridSize") double gridSize
    );
}