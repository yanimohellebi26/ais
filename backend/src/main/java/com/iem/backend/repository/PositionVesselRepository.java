package com.iem.backend.repository;

import java.util.List;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import com.iem.backend.entity.LatestPosition;

public interface PositionVesselRepository extends JpaRepository<LatestPosition, Long>{
    
    @Query("SELECT lp FROM LatestPosition lp WHERE (COALESCE(:vesselIds, NULL) IS NULL OR lp.vesselId IN :vesselIds)")
    Page<LatestPosition> findByVesselIds(@Param("vesselIds") List<Integer> vesselIds, Pageable pageable);

}
