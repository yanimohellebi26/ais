package com.iem.backend.repository;

import com.iem.backend.dto.ports.PortWithDistance;
import com.iem.backend.entity.Port;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface PortRepository extends JpaRepository<Port, Integer>{

    @Query(
            value = """
                SELECT * FROM port p
                    WHERE p.geom && ST_MakeEnvelope(:minLon, :minLat, :maxLon, :maxLat, 4326)::geography
                    AND ST_Within(p.geom::geometry, ST_MakeEnvelope(:minLon, :minLat, :maxLon, :maxLat, 4326))
                    LIMIT :limit
            """,
            nativeQuery = true
    )
    List<Port> findByBounds(
            @Param("minLat") double minLat,
            @Param("maxLat") double maxLat,
            @Param("minLon") double minLon,
            @Param("maxLon") double maxLon,
            @Param("limit") int limit
    );

    @Query(
        value = """
            SELECT
                p.id AS id,
                p.code AS code,
                p.name AS name,
                c.name AS country,
                ST_Distance(geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography) AS distance
            FROM port p
            LEFT JOIN country c ON p.country_code = c.id
            ORDER BY distance
            LIMIT 1
        """,
        nativeQuery = true
    )
    PortWithDistance findNearestPort(
        @Param("lon") double lon,
        @Param("lat") double lat
    );

    @Query(
        value = """
        SELECT
            p.id AS id,
            p.code AS code,
            p.name AS name,
            c.name AS country,
            ST_Distance(lp.geom, p.geom) AS distance
        FROM latest_positions lp
        JOIN port p ON TRUE
        LEFT JOIN country c ON p.country_code = c.id
        WHERE lp.vessel_id = :vesselId
        ORDER BY lp.geom <-> p.geom
        LIMIT 1
        """,
        nativeQuery = true
    )
    PortWithDistance findNearestPortFromVessel(@Param("vesselId") Integer vesselId);
}
