package com.iem.backend.repository;

import org.springframework.data.jpa.repository.Query;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.repository.query.Param;

import com.iem.backend.entity.PositionVessel;

import java.sql.Timestamp;
import java.util.List;

public interface PositionVesselRepository extends JpaRepository<PositionVessel, Long> {

    @Query(
            value = """
                SELECT * FROM position_vessel p
                    WHERE p.base_date_time BETWEEN :start AND :end
                    AND p.geom && ST_MakeEnvelope(:minLon, :minLat, :maxLon, :maxLat, 4326)::geography
                    AND ST_Within(p.geom::geometry, ST_MakeEnvelope(:minLon, :minLat, :maxLon, :maxLat, 4326))                                                \s
            """,
            nativeQuery = true
        )
    List<PositionVessel> findByDateAndBounds(
            @Param("start") java.sql.Timestamp start,
            @Param("end") java.sql.Timestamp end,
            @Param("minLat") double minLat,
            @Param("maxLat") double maxLat,
            @Param("minLon") double minLon,
            @Param("maxLon") double maxLon
    );

    List<PositionVessel> findPositionVesselsByVesselId(Integer vesselId);

    List<PositionVessel> findPositionVesselsByVesselIdAndBaseDateTimeBetween(Integer vesselId, Timestamp start, Timestamp end);

}
