package com.iem.backend.repository;

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
}
