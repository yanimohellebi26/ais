package com.iem.backend.repository;
import java.time.LocalDate;
import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import com.iem.backend.entity.PortRoute;
import com.iem.backend.repository.projection.PortRouteProjection;

public interface PortRouteRepository extends JpaRepository<PortRoute, Integer> {
    
    @Query(value = """
        SELECT 
            r.src_port_id AS srcPortId, 
            ps.name AS srcPortName, 
            r.dest_port_id AS destPortId, 
            pd.name AS destPortName, 
            SUM(r.ship_count) AS shipCount, 
            AVG(r.avg_duration_minutes) AS avgDuration, 
            ST_AsGeoJSON(ST_Simplify(r.geom::geometry, :tolerance)) AS geojson
        FROM port_routes r
        JOIN port ps ON r.src_port_id = ps.id
        JOIN port pd ON r.dest_port_id = pd.id
        WHERE (CAST(:startDate AS date) IS NULL OR r.route_date >= CAST(:startDate AS date))
        AND (CAST(:endDate AS date) IS NULL OR r.route_date <= CAST(:endDate AS date))
        AND r.geom && ST_MakeEnvelope(:minLon, :minLat, :maxLon, :maxLat, 4326)
        AND (
            (CAST(:lat AS double precision) IS NULL OR CAST(:lon AS double precision) IS NULL OR CAST(:radius AS double precision) IS NULL)
            OR 
            ST_DWithin(
                r.geom::geography, 
                ST_SetSRID(ST_MakePoint(CAST(:lon AS double precision), CAST(:lat AS double precision)), 4326)::geography, 
                CAST(:radius AS double precision)
            )
        )
        GROUP BY r.src_port_id, ps.name, r.dest_port_id, pd.name, r.geom
        HAVING (:zoom > 7 OR SUM(r.ship_count) > 2)
        """, nativeQuery = true)
    List<PortRouteProjection> getRoutesGeoJson(
        @Param("startDate") LocalDate startDate, 
        @Param("endDate") LocalDate endDate, 
        @Param("lat") Double lat,
        @Param("lon") Double lon,
        @Param("radius") Double radius,
        @Param("minLat") double minLat,
        @Param("maxLat") double maxLat,
        @Param("minLon") double minLon,
        @Param("maxLon") double maxLon,
        @Param("zoom") int zoom,
        @Param("tolerance") double tolerance
    );
}
