package com.iem.backend.repository;

import com.iem.backend.entity.Trajectory;
import com.iem.backend.repository.projection.SeasonalityProjection;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.sql.Timestamp;
import java.util.List;
import java.util.UUID;

@Repository
public interface SeasonalityRepository extends JpaRepository<Trajectory, UUID>{

    @Query(value = """
        SELECT MAX(EXTRACT(YEAR FROM t.start_time))::int
        FROM trajectories t
""", nativeQuery = true)
    Integer findLatestYear();

    @Query(value = """
        SELECT
            m.month AS value,
            :year AS year,
            NULL::date AS date,
            NULL::date AS end_date,
            COALESCE(COUNT(t.id), 0) AS trajectoryCount
        FROM generate_series(1, 12) AS m(month)
        LEFT JOIN (
            SELECT t.id, t.start_time
            FROM trajectories t
            JOIN vessel v ON t.vessel_id = v.id
            JOIN vessel_type vt ON v.vessel_type_id = vt.id
            LEFT JOIN mid m2 ON v.mid_code = m2.mid
            LEFT JOIN country c ON m2.country_id = c.id
            WHERE EXTRACT(YEAR FROM t.start_time) = :year
                AND (:vesselType IS NULL OR vt.id = :vesselType)
                AND (:vesselGroup IS NULL OR vt.vessel_group = :vesselGroup)
                AND (:country IS NULL OR c.name = :country)
                AND (
                    (:lat IS NOT NULL AND :lon IS NOT NULL AND :radiusMeters IS NOT NULL
                        AND ST_DWithin(
                            t.geom::geography,
                            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                            :radiusMeters
                        )
                    )
                    OR (:lat IS NULL AND :lon IS NULL AND :radiusMeters IS NULL)
                )
            ) t ON EXTRACT(MONTH FROM t.start_time) = m.month
            GROUP BY m.month
            ORDER BY m.month
    """, nativeQuery = true)
    List<SeasonalityProjection> findSeasonalityByYear(
            @Param("year") int year,
            @Param("vesselType") Integer vesselType,
            @Param("vesselGroup") String vesselGroup,
            @Param("country") String country,
            @Param("lat") Double lat,
            @Param("lon") Double lon,
            @Param("radiusMeters") Double radiusMeters
    );

    @Query(value = """
        SELECT
            NULL::integer AS value,
            CAST(EXTRACT(YEAR FROM d.day) AS INTEGER) AS year,
            d.day::date AS date,
            NULL::date AS end_date,
            COALESCE(COUNT(t.id), 0) AS trajectoryCount
        FROM generate_series(CAST(:startDate AS timestamp), CAST(:endDate AS timestamp), '1 day') AS d(day)
        LEFT JOIN (
            SELECT t.id, t.start_time
            FROM trajectories t
            JOIN vessel v ON t.vessel_id = v.id
            JOIN vessel_type vt ON v.vessel_type_id = vt.id
            LEFT JOIN mid m2 ON v.mid_code = m2.mid
            LEFT JOIN country c ON m2.country_id = c.id
            WHERE t.start_time >= :startDate
                AND t.start_time <= :endDate
                AND (:vesselType IS NULL OR vt.id = :vesselType)
                AND (:vesselGroup IS NULL OR vt.vessel_group = :vesselGroup)
                AND (:country IS NULL OR c.name = :country)
                AND (
                    (:lat IS NOT NULL AND :lon IS NOT NULL AND :radiusMeters IS NOT NULL
                        AND ST_DWithin(
                            t.geom::geography,
                            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                            :radiusMeters
                        )
                    )
                    OR (:lat IS NULL AND :lon IS NULL AND :radiusMeters IS NULL)
                )
            ) t ON DATE_TRUNC('day', t.start_time) = d.day
            GROUP BY d.day
            ORDER BY d.day
    """, nativeQuery = true)
    List<SeasonalityProjection> findSeasonalityByDay(
            @Param("startDate") Timestamp startDate,
            @Param("endDate") Timestamp endDate,
            @Param("vesselType") Integer vesselType,
            @Param("vesselGroup") String vesselGroup,
            @Param("country") String country,
            @Param("lat") Double lat,
            @Param("lon") Double lon,
            @Param("radiusMeters") Double radiusMeters
    );

    @Query(value = """
        SELECT
        CAST(EXTRACT(MONTH FROM m.month_start) AS INTEGER) AS value,
        CAST(EXTRACT(YEAR FROM m.month_start) AS INTEGER)  AS year,
        GREATEST(m.month_start::date, CAST(:startDate AS date)) AS date,
        LEAST((m.month_start + INTERVAL '1 month - 1 day')::date, CAST(:endDate AS date)) AS end_date,
        COALESCE(COUNT(t.id), 0) AS trajectoryCount
        FROM generate_series(
            DATE_TRUNC('month', CAST(:startDate AS timestamp)),
            DATE_TRUNC('month', CAST(:endDate AS timestamp)),
            '1 month'
        ) AS m(month_start)
        LEFT JOIN (
            SELECT t.id, t.start_time
            FROM trajectories t
            JOIN vessel v ON t.vessel_id = v.id
            JOIN vessel_type vt ON v.vessel_type_id = vt.id
            LEFT JOIN mid m2 ON v.mid_code = m2.mid
            LEFT JOIN country c ON m2.country_id = c.id
            WHERE t.start_time >= :startDate
                AND t.start_time <= :endDate
                AND (:vesselType IS NULL OR vt.id = :vesselType)
                AND (:vesselGroup IS NULL OR vt.vessel_group = :vesselGroup)
                AND (:country IS NULL OR c.name = :country)
                AND (
                    (:lat IS NOT NULL AND :lon IS NOT NULL AND :radiusMeters IS NOT NULL
                        AND ST_DWithin(
                            t.geom::geography,
                            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                            :radiusMeters
                        )
                    )
                    OR (:lat IS NULL AND :lon IS NULL AND :radiusMeters IS NULL)
                )
            ) t ON DATE_TRUNC('month', t.start_time) = m.month_start
            GROUP BY m.month_start
            ORDER BY m.month_start
    """, nativeQuery = true)
    List<SeasonalityProjection> findSeasonalityByMonth(
            @Param("startDate") Timestamp startDate,
            @Param("endDate") Timestamp endDate,
            @Param("vesselType") Integer vesselType,
            @Param("vesselGroup") String vesselGroup,
            @Param("country") String country,
            @Param("lat") Double lat,
            @Param("lon") Double lon,
            @Param("radiusMeters") Double radiusMeters
    );

    @Query(value = """
        SELECT
            NULL::integer AS value,
            CAST(EXTRACT(YEAR FROM d.week_start) AS INTEGER) AS year,
            GREATEST(d.week_start, CAST(:startDate AS date)) AS date,
            LEAST(d.week_start + INTERVAL '6 days', CAST(:endDate AS date)) AS end_date,
            COALESCE(COUNT(t.id), 0) AS trajectoryCount
        FROM generate_series(
            DATE_TRUNC('week', CAST(:startDate AS timestamp)),
            DATE_TRUNC('week', CAST(:endDate AS timestamp)),
            '7 days'
        ) AS d(week_start)
        LEFT JOIN (
            SELECT t.id, t.start_time
            FROM trajectories t
            JOIN vessel v ON t.vessel_id = v.id
            JOIN vessel_type vt ON v.vessel_type_id = vt.id
            LEFT JOIN mid m2 ON v.mid_code = m2.mid
            LEFT JOIN country c ON m2.country_id = c.id
            WHERE t.start_time >= :startDate
                AND t.start_time <= :endDate
                AND (:vesselType IS NULL OR vt.id = :vesselType)
                AND (:vesselGroup IS NULL OR vt.vessel_group = :vesselGroup)
                AND (:country IS NULL OR c.name = :country)
                AND (
                    (:lat IS NOT NULL AND :lon IS NOT NULL AND :radiusMeters IS NOT NULL
                        AND ST_DWithin(
                            t.geom::geography,
                            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                            :radiusMeters
                        )
                    )
                    OR (:lat IS NULL AND :lon IS NULL AND :radiusMeters IS NULL)
                )
        ) t ON t.start_time >= d.week_start
            AND t.start_time < d.week_start + INTERVAL '7 days'
        GROUP BY d.week_start
        ORDER BY d.week_start
    """, nativeQuery = true)
    List<SeasonalityProjection> findSeasonalityByWeek(
            @Param("startDate") Timestamp startDate,
            @Param("endDate") Timestamp endDate,
            @Param("vesselType") Integer vesselType,
            @Param("vesselGroup") String vesselGroup,
            @Param("country") String country,
            @Param("lat") Double lat,
            @Param("lon") Double lon,
            @Param("radiusMeters") Double radiusMeters
    );

    @Query(value = """
        SELECT
            h.hour AS value,
            CAST(EXTRACT(YEAR FROM CAST(:day AS timestamp)) AS INTEGER) AS year,
            CAST(:day AS date) AS date,
            NULL::date AS end_date,
            COALESCE(COUNT(t.id), 0) AS trajectoryCount
        FROM generate_series(0, 23) AS h(hour)
        LEFT JOIN (
            SELECT t.id, t.start_time
            FROM trajectories t
            JOIN vessel v ON t.vessel_id = v.id
            JOIN vessel_type vt ON v.vessel_type_id = vt.id
            LEFT JOIN mid m2 ON v.mid_code = m2.mid
            LEFT JOIN country c ON m2.country_id = c.id
            WHERE DATE_TRUNC('day', t.start_time) = DATE_TRUNC('day', CAST(:day AS timestamp))
                AND (:vesselType IS NULL OR vt.id = :vesselType)
                AND (:vesselGroup IS NULL OR vt.vessel_group = :vesselGroup)
                AND (:country IS NULL OR c.name = :country)
                AND (
                    (:lat IS NOT NULL AND :lon IS NOT NULL AND :radiusMeters IS NOT NULL
                        AND ST_DWithin(
                            t.geom::geography,
                            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                            :radiusMeters
                        )
                    )
                    OR (:lat IS NULL AND :lon IS NULL AND :radiusMeters IS NULL)
                )
            ) t ON EXTRACT(HOUR FROM t.start_time) = h.hour
            GROUP BY h.hour
            ORDER BY h.hour
    """, nativeQuery = true)
    List<SeasonalityProjection> findSeasonalityByHour(
            @Param("day") Timestamp day,
            @Param("vesselType") Integer vesselType,
            @Param("vesselGroup") String vesselGroup,
            @Param("country") String country,
            @Param("lat") Double lat,
            @Param("lon") Double lon,
            @Param("radiusMeters") Double radiusMeters
    );
}