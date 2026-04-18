package com.iem.backend.repository;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import com.iem.backend.entity.PortRoute;

public interface PortRouteRepository extends JpaRepository<PortRoute, Integer> {
    
    @Query(value = """
        SELECT 
            r.src_port_id AS srcPortId, 
            ps.name AS srcPortName,
            r.dest_port_id AS destPortId, 
            pd.name AS destPortName,
            COUNT(*) AS ship_count,
            AVG(r.duration_minutes) AS avg_duration,
            ST_AsGeoJSON(ST_Simplify(r.geom::geometry, 0.01)) AS geojson
        FROM port_routes r
        JOIN port ps ON r.src_port_id = ps.id
        JOIN port pd ON r.dest_port_id = pd.id
        WHERE (:startDate IS NULL OR r.route_date >= :startDate)
          AND (:endDate IS NULL OR r.route_date <= :endDate)
          AND (
                (:lat IS NOT NULL AND :lon IS NOT NULL AND :radius IS NOT NULL
                    AND ST_DWithin(r.geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :radius)
                ) OR (:lat IS NULL)
          )
        GROUP BY r.src_port_id, ps.name, r.dest_port_id, pd.name, r.geom
    """, nativeQuery = true)
    String getRoutesGeoJson(
        @Param("startDate") String startDate, 
        @Param("endDate") String endDate, 
        @Param("lat") Double lat,
        @Param("lon") Double lon,
        @Param("radius") Double radius
    );
}
