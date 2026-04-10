package com.iem.backend.repository;

import com.iem.backend.entity.Trajectory;
import com.iem.backend.repository.projection.VesselTypeStatsProjection;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.sql.Timestamp;
import java.util.List;
import java.util.UUID;

@Repository
public interface VesselTypeStatsRepository extends JpaRepository<Trajectory, UUID> {

    @Query(value = """
        SELECT
            vt.id AS vesselTypeId,
            vt.description AS vesselTypeDescription,
            vt.vessel_group AS vesselGroup,
            COUNT(t.id) AS trajectoryCount,
            ROUND(COALESCE(SUM(t.distance_nm) * 1.852,0)::numeric,2) AS totalDistanceKm,
            ROUND(COALESCE(AVG(t.avg_speed) * 1.852,0)::numeric,2) AS avgSpeedKmh,
            ROUND(COALESCE(AVG(t.distance_nm) * 1.852,0)::numeric,2) AS avgDistanceKm,
            ROUND(COALESCE(SUM(t.duration_minutes) / 60,0)::numeric,2) AS totalDurationHours,
            ROUND(COALESCE(AVG(t.duration_minutes) / 60,0)::numeric,2) AS avgDurationHours,
            ROUND(
                COALESCE(
                    (SUM(t.distance_nm) * 1.852)
                        /
                        NULLIF(SUM(t.duration_minutes) / 60, 0),0
                )::numeric,2
            ) AS efficiencyKmh
        FROM trajectories t
        JOIN vessel v ON t.vessel_id = v.id
        JOIN vessel_type vt ON v.vessel_type_id = vt.id
        LEFT JOIN mid m ON v.mid_code = m.mid
        LEFT JOIN country c ON m.country_id = c.id
        WHERE (:vesselType IS NULL OR vt.id = :vesselType)
        AND (:vesselGroup IS NULL OR vt.vessel_group = :vesselGroup)
        AND (:country IS NULL OR c.name = :country)
        GROUP BY vt.id, vt.description, vt.vessel_group
        ORDER BY totalDistanceKm DESC
        LIMIT :topN
    """, nativeQuery = true)
    List<VesselTypeStatsProjection> getVesselTypeStatsAll(
            @Param("vesselType") Integer vesselType,
            @Param("vesselGroup") String vesselGroup,
            @Param("country") String country,
            @Param("topN") int topN
    );

    @Query(value = """
        SELECT
            vt.id AS vesselTypeId,
            vt.description AS vesselTypeDescription,
            vt.vessel_group AS vesselGroup,
            COUNT(t.id) AS trajectoryCount,
            ROUND(COALESCE(SUM(t.distance_nm) * 1.852,0)::numeric,2) AS totalDistanceKm,
            ROUND(COALESCE(AVG(t.avg_speed) * 1.852,0)::numeric,2) AS avgSpeedKmh,
            ROUND(COALESCE(AVG(t.distance_nm) * 1.852,0)::numeric,2) AS avgDistanceKm,
            ROUND(COALESCE(SUM(t.duration_minutes) / 60,0)::numeric,2) AS totalDurationHours,
            ROUND(COALESCE(AVG(t.duration_minutes) / 60,0)::numeric,2) AS avgDurationHours,
            ROUND(
                COALESCE(
                    (SUM(t.distance_nm) * 1.852)
                        /
                        NULLIF(SUM(t.duration_minutes) / 60, 0),0
                )::numeric,2
            ) AS efficiencyKmh
        FROM trajectories t
        JOIN vessel v ON t.vessel_id = v.id
        JOIN vessel_type vt ON v.vessel_type_id = vt.id
        LEFT JOIN mid m ON v.mid_code = m.mid
        LEFT JOIN country c ON m.country_id = c.id
        WHERE t.start_time >= :startDate AND t.end_time <= :endDate
            AND (:vesselType IS NULL OR vt.id = :vesselType)
            AND (:vesselGroup IS NULL OR vt.vessel_group = :vesselGroup)
            AND (:country IS NULL OR c.name = :country)
        GROUP BY vt.id, vt.description, vt.vessel_group
        ORDER BY totalDistanceKm DESC
        LIMIT :topN
    """, nativeQuery = true)
    List<VesselTypeStatsProjection> getVesselTypeStatsByDate(
            @Param("startDate") Timestamp startDate,
            @Param("endDate") Timestamp endDate,
            @Param("vesselType") Integer vesselType,
            @Param("vesselGroup") String vesselGroup,
            @Param("country") String country,
            @Param("topN") int topN
    );

    @Query(value = """
        SELECT
            vt.id AS vesselTypeId,
            vt.description AS vesselTypeDescription,
            vt.vessel_group AS vesselGroup,
            COUNT(t.id) AS trajectoryCount,
            ROUND(COALESCE(SUM(t.distance_nm) * 1.852,0)::numeric,2) AS totalDistanceKm,
            ROUND(COALESCE(AVG(t.avg_speed) * 1.852,0)::numeric,2) AS avgSpeedKmh,
            ROUND(COALESCE(AVG(t.distance_nm) * 1.852,0)::numeric,2) AS avgDistanceKm,
            ROUND(COALESCE(SUM(t.duration_minutes) / 60,0)::numeric,2) AS totalDurationHours,
            ROUND(COALESCE(AVG(t.duration_minutes) / 60,0)::numeric,2) AS avgDurationHours,
            ROUND(
                COALESCE(
                    (SUM(t.distance_nm) * 1.852)
                        /
                        NULLIF(SUM(t.duration_minutes) / 60, 0),0
                )::numeric,2
            ) AS efficiencyKmh
        FROM trajectories t
        JOIN vessel v ON t.vessel_id = v.id
        JOIN vessel_type vt ON v.vessel_type_id = vt.id
        LEFT JOIN mid m ON v.mid_code = m.mid
        LEFT JOIN country c ON m.country_id = c.id
        WHERE ST_DWithin(
            t.geom::geography,
            ST_SetSRID(ST_MakePoint(:lon,:lat),4326)::geography,
            :radiusMeters)
            AND (:vesselType IS NULL OR vt.id = :vesselType)
            AND (:vesselGroup IS NULL OR vt.vessel_group = :vesselGroup)
            AND (:country IS NULL OR c.name = :country)
        GROUP BY vt.id, vt.description, vt.vessel_group
        ORDER BY totalDistanceKm DESC
        LIMIT :topN
    """, nativeQuery = true)
    List<VesselTypeStatsProjection> getVesselTypeStatsInRadius(
            @Param("lat") Double lat,
            @Param("lon") Double lon,
            @Param("radiusMeters") Double radius,
            @Param("vesselType") Integer vesselType,
            @Param("vesselGroup") String vesselGroup,
            @Param("country") String country,
            @Param("topN") int topN
    );

    @Query(value = """
        SELECT
            vt.id AS vesselTypeId,
            vt.description AS vesselTypeDescription,
            vt.vessel_group AS vesselGroup,
            COUNT(t.id) AS trajectoryCount,
            ROUND(COALESCE(SUM(t.distance_nm) * 1.852,0)::numeric,2) AS totalDistanceKm,
            ROUND(COALESCE(AVG(t.avg_speed) * 1.852,0)::numeric,2) AS avgSpeedKmh,
            ROUND(COALESCE(AVG(t.distance_nm) * 1.852,0)::numeric,2) AS avgDistanceKm,
            ROUND(COALESCE(SUM(t.duration_minutes) / 60,0)::numeric,2) AS totalDurationHours,
            ROUND(COALESCE(AVG(t.duration_minutes) / 60,0)::numeric,2) AS avgDurationHours,
            ROUND(
                COALESCE(
                    (SUM(t.distance_nm) * 1.852)
                        /
                        NULLIF(SUM(t.duration_minutes) / 60, 0),0
                )::numeric,2
            ) AS efficiencyKmh
        FROM trajectories t
        JOIN vessel v ON t.vessel_id = v.id
        JOIN vessel_type vt ON v.vessel_type_id = vt.id
        LEFT JOIN mid m ON v.mid_code = m.mid
        LEFT JOIN country c ON m.country_id = c.id
        WHERE t.start_time >= :startDate AND t.end_time <= :endDate
          AND ST_DWithin(
              t.geom::geography,
                  ST_SetSRID(ST_MakePoint(:lon,:lat),4326)::geography,
                      :radiusMeters
                  )
          AND (:vesselType IS NULL OR vt.id = :vesselType)
          AND (:vesselGroup IS NULL OR vt.vessel_group = :vesselGroup)
          AND (:country IS NULL OR c.name = :country)
        GROUP BY vt.id, vt.description, vt.vessel_group
        ORDER BY totalDistanceKm DESC
        LIMIT :topN
    """, nativeQuery = true)
    List<VesselTypeStatsProjection> getVesselTypeStatsByDateInRadius(
            @Param("startDate") Timestamp startDate,
            @Param("endDate") Timestamp endDate,
            @Param("lat") Double lat,
            @Param("lon") Double lon,
            @Param("radiusMeters") Double radius,
            @Param("vesselType") Integer vesselType,
            @Param("vesselGroup") String vesselGroup,
            @Param("country") String country,
            @Param("topN") int topN
    );
}