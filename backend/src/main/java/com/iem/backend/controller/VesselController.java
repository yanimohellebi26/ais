package com.iem.backend.controller;

import com.iem.backend.dto.UserVesselRequestDto;
import com.iem.backend.service.VesselService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/vessel")
public class VesselController {

    private final VesselService vesselService;

    public VesselController(VesselService vesselService) {
        this.vesselService = vesselService;
    }

    @PostMapping("/related")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<String> relateUserToVessel(@Valid @RequestBody UserVesselRequestDto dto) {
        vesselService.relateUserToVessel(dto.userId(), dto.mmsi());
        return ResponseEntity.ok("User related to vessel successfully");
    }
}

