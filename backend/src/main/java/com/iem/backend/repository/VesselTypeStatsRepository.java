package com.iem.backend.repository;

import com.iem.backend.entity.Trajectory;
import com.iem.backend.repository.projection.VesselTypeStatsProjection;
import org.springframework.data.jpa.repository.JpaRepository;

import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.UUID;
import java.sql.Timestamp;
import java.util.List;

public interface VesselTypeStatsRepository extends JpaRepository<Trajectory, UUID> {

    @Query(value = """
        SELECT
            vt.id AS vesselTypeId,
            vt.description AS vesselTypeDescription,
            vt.vessel_group AS vesselGroup,
            COUNT(t.id) AS trajectoryCount,
            ROUND(COALESCE(SUM(t.distance_nm) * 1.852, 0), 2) AS totalDistanceKm,
            ROUND(COALESCE(AVG(t.avg_speed) * 1.852, 0), 2) AS avgSpeedKmH
        FROM trajectories t
        JOIN vessel v ON t.vessel_id = v.id
        JOIN vessel_type vt ON v.vessel_type_id = vt.id
        LEFT JOIN mid m ON v.mid_code = m.id
        LEFT JOIN country c ON m.country_id = c.id
        WHERE 1=1

        AND (:startDate IS NULL OR t.start_time >= :startDate)
        AND (:endDate IS NULL OR t.end_time <= :endDate)
        AND (:vesselType IS NULL OR vt.id = :vesselType)
        AND (:vesselGroup IS NULL OR vt.vessel_group = :vesselGroup)
        AND (:country IS NULL OR c.name = :country)
        AND (
                :latitude IS NULL OR :longitude IS NULL OR :radius IS NULL
                    OR ST_DWithin(
                        t.geom::geography,
                        ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)::geography,
                        :radius * 1000
                    )
            )
        GROUP BY vt.id, vt.description, vt.vessel_group
        ORDER BY totalDistanceKm DESC
    """, nativeQuery = true)
    List<VesselTypeStatsProjection> getVesselTypeStatistics(
            @Param("startDate") Timestamp startDate,
            @Param("endDate") Timestamp endDate,
            @Param("vesselType") Integer vesselType,
            @Param("vesselGroup") String vesselGroup,
            @Param("country") String country,
            @Param("latitude") Double latitude,
            @Param("longitude") Double longitude,
            @Param("radius") Double radius
    );
}