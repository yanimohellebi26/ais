package com.iem.backend.repository;

import com.iem.backend.entity.Vessel;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface VesselRepository extends JpaRepository<Vessel, Integer> {

    Optional<Vessel> findByMmsi(String mmsi);
}
