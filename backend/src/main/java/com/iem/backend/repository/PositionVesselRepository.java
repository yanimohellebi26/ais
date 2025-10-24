package com.iem.backend.repository;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import com.iem.backend.entity.PositionVessel;

public interface PositionVesselRepository extends JpaRepository<PositionVessel, Long>{
    

    @Query(
        """
        SELECT position FROM PositionVessel pv
        WHERE pv.baseDateTime = (
            SELECT MAX(p2.baseDateTime)
            FROM PositionVessel p2
            WHERE p2.vesselId = pv.vesselId
        )
        AND (:vesselIds IS NULL OR pv.vesselId IN :vessels)
        """
    )
    List<PositionVessel> findLatestPositions(@Param("vesselIds") List<Integer> vesselIds);
}
