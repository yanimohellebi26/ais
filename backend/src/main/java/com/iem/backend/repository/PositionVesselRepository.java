package com.iem.backend.repository;

import java.util.Collection;
import java.util.List;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import com.iem.backend.entity.PositionVessel;
import java.sql.Timestamp;
import java.util.Optional;

public interface PositionVesselRepository extends JpaRepository<PositionVessel, Long>{

    @Query(
        value = """
            SELECT * FROM latest_positions
            WHERE vessel_id IN :ids
            """,
        countQuery = "SELECT COUNT(*) FROM latest_positions WHERE id IN :ids",
        nativeQuery = true
        )
    Page<PositionVessel> findLatestPositionVesselsByIdIn(@Param("ids") Collection<Integer> ids, Pageable pageable);

    @Query(
            value = """
                SELECT * FROM position_vessel p
                    WHERE p.base_date_time BETWEEN :start AND :end
                    AND p.geom && ST_MakeEnvelope(:minLon, :minLat, :maxLon, :maxLat, 4326)::geography
                    AND ST_Within(p.geom::geometry, ST_MakeEnvelope(:minLon, :minLat, :maxLon, :maxLat, 4326))
                    LIMIT :limit
            """,
            nativeQuery = true
        )
    List<PositionVessel> findByDateAndBounds(
            @Param("start") java.sql.Timestamp start,
            @Param("end") java.sql.Timestamp end,
            @Param("minLat") double minLat,
            @Param("maxLat") double maxLat,
            @Param("minLon") double minLon,
            @Param("maxLon") double maxLon,
            @Param("limit") int limit
    );
    @Query(
            value = """
                SELECT DISTINCT ON (p.vessel_id) * FROM position_vessel p
                    WHERE p.base_date_time BETWEEN :start AND :end
                    AND p.geom && ST_MakeEnvelope(:minLon, :minLat, :maxLon, :maxLat, 4326)::geography
                    AND ST_Within(p.geom::geometry, ST_MakeEnvelope(:minLon, :minLat, :maxLon, :maxLat, 4326))
                    LIMIT :limit
            """,
            nativeQuery = true
    )
    List<PositionVessel> findByDateAndBoundsDistinct(
            @Param("start") java.sql.Timestamp start,
            @Param("end") java.sql.Timestamp end,
            @Param("minLat") double minLat,
            @Param("maxLat") double maxLat,
            @Param("minLon") double minLon,
            @Param("maxLon") double maxLon,
            @Param("limit") int limit
    );

    @Query(
            value = """
                SELECT p.* FROM position_vessel p
                    JOIN vessel v ON p.vessel_id = v.id
                    JOIN user_vessel uv ON uv.vessel_id = p.vessel_id
                    WHERE uv.user_id = :userId
                    AND p.base_date_time BETWEEN :start AND :end
                    AND p.geom && ST_MakeEnvelope(:minLon, :minLat, :maxLon, :maxLat, 4326)::geography
                    AND ST_Within(p.geom::geometry, ST_MakeEnvelope(:minLon, :minLat, :maxLon, :maxLat, 4326))
                    LIMIT :limit
            """,
            nativeQuery = true
    )
    List<PositionVessel> findByDateAndBoundsAndUserId(
            @Param("userId") int userId,
            @Param("start") java.sql.Timestamp start,
            @Param("end") java.sql.Timestamp end,
            @Param("minLat") double minLat,
            @Param("maxLat") double maxLat,
            @Param("minLon") double minLon,
            @Param("maxLon") double maxLon,
            @Param("limit") int limit
    );

    @Query(
        value = """
            SELECT * FROM latest_positions pv
            WHERE pv.geom && ST_MakeEnvelope(:minLon, :minLat, :maxLon, :maxLat, 4326)
            AND ST_Within(
                pv.geom::geometry,
                ST_MakeEnvelope(:minLon, :minLat, :maxLon, :maxLat, 4326)
            )
            LIMIT :limit;
        """,
        nativeQuery = true
    )
    List<PositionVessel> findLatestPositionWithinBounds(
        @Param("minLat") double minLat,
        @Param("maxLat") double maxLat,
        @Param("minLon") double minLon,
        @Param("maxLon") double maxLon,
        @Param("limit") int limit
    );

    @Query(
        value = """
            SELECT * FROM latest_positions pv
            WHERE pv.geom && ST_MakeEnvelope(:minLon, :minLat, :maxLon, :maxLat, 4326)
            AND ST_Within(
                pv.geom::geometry,
                ST_MakeEnvelope(:minLon, :minLat, :maxLon, :maxLat, 4326)
            )
            AND pv.vessel_id IN (:vesselIds)
        """,
        nativeQuery = true
    )
    List<PositionVessel> findLatestPositionWithinBoundsForVessels(
        @Param("minLat") double minLat,
        @Param("maxLat") double maxLat,
        @Param("minLon") double minLon,
        @Param("maxLon") double maxLon,
        @Param("vesselIds") List<Integer> vesselIds
    );

    List<PositionVessel> findPositionVesselsByVesselId(Integer vesselId);

    List<PositionVessel> findPositionVesselsByVesselIdAndBaseDateTimeBetween(Integer vesselId, Timestamp start, Timestamp end);

    @Query(value = """
        SELECT * FROM latest_positions lp
        WHERE lp.vessel_id = :vesselId
        """,
        nativeQuery = true)
    Optional<PositionVessel> findLatestPositionByVesselId(@Param("vesselId") Integer vesselId);

    @Query(value = """
        SELECT * FROM latest_positions lp
        WHERE lp.vessel_id = :vesselId
        AND lp.base_date_time = :ts
        """,
            nativeQuery = true)
    Optional<PositionVessel> findPositionByVesselIdAndExactTime(@Param("vesselId") Integer vesselId, @Param("ts") Timestamp ts);

    @Query(value = """
        SELECT * FROM latest_positions lp
        WHERE lp.vessel_id = :vesselId
        AND lp.base_date_time BETWEEN :start AND :end
        """,
            nativeQuery = true)
    Optional<PositionVessel> findLastPositionInDay(@Param("vesselId") Integer vesselId, @Param("start") Timestamp start, @Param("end") Timestamp end);

    @Query(value = """
                SELECT *
                FROM position_vessel p
                WHERE p.base_date_time BETWEEN :start AND :end
                  AND p.vessel_id <> :targetVessel
                  AND ST_DWithin(
                        p.geom::geography,
                        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                        :radiusMeters
                  )
               """,
            nativeQuery = true
    )
    List<PositionVessel> findPositionsAround(
            @Param("lat") double lat,
            @Param("lon") double lon,
            @Param("radiusMeters") double radiusMeters,
            @Param("start") Timestamp start,
            @Param("end") Timestamp end,
            @Param("targetVessel") Integer targetVessel
    );

    @Query(value = """
        SELECT DISTINCT ON (p.vessel_id) *
        FROM position_vessel p
        WHERE p.base_date_time BETWEEN :start AND :end
          AND p.vessel_id <> :targetVessel
          AND ST_DWithin(
                p.geom::geography,
                ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                :radiusMeters
          )
        ORDER BY p.vessel_id, p.base_date_time DESC
       """,
            nativeQuery = true
    )
    List<PositionVessel> findLastPositionsAround(
            @Param("lat") double lat,
            @Param("lon") double lon,
            @Param("radiusMeters") double radiusMeters,
            @Param("start") Timestamp start,
            @Param("end") Timestamp end,
            @Param("targetVessel") Integer targetVessel
    );


}
