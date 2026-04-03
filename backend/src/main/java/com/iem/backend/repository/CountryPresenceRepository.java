package com.iem.backend.repository;

import com.iem.backend.entity.PositionVessel;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.sql.Timestamp;
import java.util.List;

@Repository
public interface CountryPresenceRepository extends JpaRepository<PositionVessel, Long> {

    @Query(value = """
        SELECT c.name, c.code_alpha_2, COUNT(DISTINCT p.vessel_id) AS vessel_count
        FROM latest_positions p
        JOIN vessel v ON p.vessel_id = v.id
        JOIN vessel_type vt ON v.vessel_type_id = vt.id
        JOIN mid m ON v.mid_code = m.mid
        JOIN country c ON m.country_id = c.id
        WHERE (:vesselType IS NULL OR vt.id = :vesselType)
        AND (:vesselGroup IS NULL OR vt.vessel_group = :vesselGroup)
        AND (:country IS NULL OR c.name = :country)
        GROUP BY c.id, c.name, c.code_alpha_2
        ORDER BY vessel_count DESC
        LIMIT :topN
        """, nativeQuery = true)
    List<Object[]> findTopCountries(
            @Param("vesselType") Integer vesselType,
            @Param("vesselGroup") String vesselGroup,
            @Param("country") String country,
            @Param("topN") int topN
    );

    @Query(value = """
        WITH latest AS (
            SELECT DISTINCT ON (p.vessel_id)
                p.vessel_id, p.geom
            FROM position_vessel p
            JOIN vessel v ON p.vessel_id = v.id
            JOIN vessel_type vt ON v.vessel_type_id = vt.id
            JOIN mid m ON v.mid_code = m.mid
            JOIN country c ON m.country_id = c.id
            WHERE p.base_date_time BETWEEN :startDate AND :endDate
            AND (:vesselType IS NULL OR vt.id = :vesselType)
            AND (:vesselGroup IS NULL OR vt.vessel_group = :vesselGroup)
            AND (:country IS NULL OR c.name = :country)
            ORDER BY p.vessel_id, p.base_date_time DESC
        )
        SELECT c.name, c.code_alpha_2, COUNT(DISTINCT l.vessel_id) AS vessel_count
        FROM latest l
        JOIN vessel v ON l.vessel_id = v.id
        JOIN mid m ON v.mid_code = m.mid
        JOIN country c ON m.country_id = c.id
        GROUP BY c.id, c.name, c.code_alpha_2
        ORDER BY vessel_count DESC
        LIMIT :topN
        """, nativeQuery = true)
    List<Object[]> findTopCountriesByDate(
            @Param("startDate") Timestamp startDate,
            @Param("endDate") Timestamp endDate,
            @Param("vesselType") Integer vesselType,
            @Param("vesselGroup") String vesselGroup,
            @Param("country") String country,
            @Param("topN") int topN
    );

    @Query(value = """
        SELECT c.name, c.code_alpha_2, COUNT(DISTINCT p.vessel_id) AS vessel_count
        FROM latest_positions p
        JOIN vessel v ON p.vessel_id = v.id
        JOIN vessel_type vt ON v.vessel_type_id = vt.id
        JOIN mid m ON v.mid_code = m.mid
        JOIN country c ON m.country_id = c.id
        WHERE ST_DWithin(
            p.geom::geography,
            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
            :radiusMeters
        )
        AND (:vesselType IS NULL OR vt.id = :vesselType)
        AND (:vesselGroup IS NULL OR vt.vessel_group = :vesselGroup)
        AND (:country IS NULL OR c.name = :country)
        GROUP BY c.id, c.name, c.code_alpha_2
        ORDER BY vessel_count DESC
        LIMIT :topN
        """, nativeQuery = true)
    List<Object[]> findTopCountriesInRadius(
            @Param("lat") double lat,
            @Param("lon") double lon,
            @Param("radiusMeters") double radiusMeters,
            @Param("vesselType") Integer vesselType,
            @Param("vesselGroup") String vesselGroup,
            @Param("country") String country,
            @Param("topN") int topN
    );

    @Query(value = """
        WITH latest AS (
            SELECT DISTINCT ON (p.vessel_id)
                p.vessel_id, p.geom
            FROM position_vessel p
            JOIN vessel v ON p.vessel_id = v.id
            JOIN vessel_type vt ON v.vessel_type_id = vt.id
            JOIN mid m ON v.mid_code = m.mid
            JOIN country c ON m.country_id = c.id
            WHERE p.base_date_time BETWEEN :startDate AND :endDate
            AND (:vesselType IS NULL OR vt.id = :vesselType)
            AND (:vesselGroup IS NULL OR vt.vessel_group = :vesselGroup)
            AND (:country IS NULL OR c.name = :country)
            ORDER BY p.vessel_id, p.base_date_time DESC
        )
        SELECT c.name, c.code_alpha_2, COUNT(DISTINCT l.vessel_id) AS vessel_count
        FROM latest l
        JOIN vessel v ON l.vessel_id = v.id
        JOIN mid m ON v.mid_code = m.mid
        JOIN country c ON m.country_id = c.id
        WHERE ST_DWithin(
            l.geom::geography,
            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
            :radiusMeters
        )
        GROUP BY c.id, c.name, c.code_alpha_2
        ORDER BY vessel_count DESC
        LIMIT :topN
        """, nativeQuery = true)
    List<Object[]> findTopCountriesInRadiusByDate(
            @Param("lat") double lat,
            @Param("lon") double lon,
            @Param("radiusMeters") double radiusMeters,
            @Param("startDate") Timestamp startDate,
            @Param("endDate") Timestamp endDate,
            @Param("vesselType") Integer vesselType,
            @Param("vesselGroup") String vesselGroup,
            @Param("country") String country,
            @Param("topN") int topN
    );
}