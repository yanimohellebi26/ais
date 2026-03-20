package com.iem.backend.controller;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.iem.backend.repository.ProtectedAreaRepository;

@RestController
@RequestMapping("/api/v1/protected-area")
public class ProtectedAreaController {
    
    private final ProtectedAreaRepository repository;

    public ProtectedAreaController(ProtectedAreaRepository repository) {
        this.repository = repository;
    }

    @GetMapping
    public ResponseEntity<String> getProtectedAreasInBbox(
        double minLong,
        double minLat,
        double maxLong,
        double maxLat
    ) {
        String geoJson = repository.findProtectedAreaInBboxAsGeoJson(minLong, minLat, maxLong, maxLat);
        return ResponseEntity.ok(geoJson);
    }
}
