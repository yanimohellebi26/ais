package com.iem.backend.controller;

import com.iem.backend.dto.UserVesselRequestDto;
import com.iem.backend.dto.VesselResponseDto;
import com.iem.backend.entity.Vessel;
import com.iem.backend.service.VesselService;
import jakarta.validation.Valid;
import org.springframework.data.domain.Page;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/vessels")
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

    @GetMapping
    public ResponseEntity<Page<VesselResponseDto>> getAllVessels(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "100") int size,
            @RequestParam(defaultValue = "id,asc") String[] sort
    ) {
        String sortField = sort[0];
        String sortDirection = sort.length > 1 ? sort[1] : "asc";

        Page<VesselResponseDto> vesselsPage = vesselService.getAllVessels(page, size, sortField, sortDirection);
        return ResponseEntity.ok(vesselsPage);
    }
}

