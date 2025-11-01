package com.iem.backend.repository;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import com.iem.backend.entity.PositionVessel;

public interface PositionVesselRepository extends JpaRepository<PositionVessel, Long>{
    
    @Query("""
        SELECT p FROM PositionVessel p
        WHERE (:vesselIds IS NULL OR p.vessel.id IN :vesselIds)
        AND p.baseDateTime = (
            SELECT MAX(p2.baseDateTime)
            FROM PositionVessel p2
            WHERE p2.vessel.id = p.vessel.id
        )
    """)
    List<PositionVessel> findLatestPositions(@Param("vesselIds") List<Integer> vesselIds);
}
