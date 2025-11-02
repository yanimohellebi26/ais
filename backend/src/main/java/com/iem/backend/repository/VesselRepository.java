package com.iem.backend.repository;

import com.iem.backend.entity.Vessel;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface VesselRepository extends JpaRepository<Vessel, Integer> {

    Optional<Vessel> findByMmsi(String mmsi);

    @Query("SELECT v FROM Vessel v WHERE UPPER(v.vesselName) LIKE UPPER(CONCAT('%', :name, '%'))")
    Page<Vessel> searchByVesselName(@Param("name") String name, Pageable pageable);

    @Query("SELECT v FROM Vessel v WHERE v.mmsi = :mmsi OR UPPER(v.vesselName) LIKE UPPER(CONCAT('%', :mmsi, '%'))")
    Page<Vessel> searchByMmsiOrVesselName(@Param("mmsi") String mmsi, Pageable pageable);
    
    @Query("SELECT v FROM Vessel v JOIN v.users u WHERE u.id = :userId")
    List<Vessel> findByUserId(@Param("userId") Integer userId);

    @Query("SELECT CASE WHEN COUNT(v) > 0 THEN TRUE ELSE FALSE END FROM Vessel v JOIN v.users u WHERE v.id = :vesselId AND u.id = :userId")
    boolean existsByIdAndUserId(@Param("vesselId") Integer vesselId, @Param("userId") Integer userId);

}
