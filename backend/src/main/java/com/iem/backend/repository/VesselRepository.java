package com.iem.backend.repository;

import com.iem.backend.entity.Vessel;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.Optional;

public interface VesselRepository extends JpaRepository<Vessel, Integer> {

    Optional<Vessel> findByMmsi(String mmsi);

    @Query("SELECT v FROM Vessel v WHERE UPPER(v.vesselName) LIKE UPPER(CONCAT('%', :name, '%'))")
    Page<Vessel> searchByVesselName(@Param("name") String name, Pageable pageable);

    @Query("SELECT v FROM Vessel v WHERE v.mmsi = :mmsi OR UPPER(v.vesselName) LIKE UPPER(CONCAT('%', :mmsi, '%'))")
    Page<Vessel> searchByMmsiOrVesselName(@Param("mmsi") String mmsi, Pageable pageable);

}
