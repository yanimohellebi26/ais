package com.iem.backend.controller;

import com.iem.backend.dto.positionVessel.PositionVesselGeoJson;
import com.iem.backend.entity.CustomUserDetails;
import com.iem.backend.service.PositionVesselService;
import com.iem.backend.service.mapper.PositionVesselMapper;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;

import com.iem.backend.entity.PositionVessel;

import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@RestController
@RequestMapping("/api/v1/positions")
public class PositionVesselController {

    private final PositionVesselService service;
    private final PositionVesselMapper mapper;

    public PositionVesselController(PositionVesselService service, PositionVesselMapper mapper) {
        this.service = service;
        this.mapper = mapper;
    }

    @GetMapping
    @PreAuthorize("hasAnyRole('ADMIN','MARITIME_EXPERT','FINANCIAL_ANALYST')")
    public ResponseEntity<Map<String, Object>> getPositions(
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate dateStart,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate dateEnd,
            @RequestParam double minLat,
            @RequestParam double maxLat,
            @RequestParam double minLon,
            @RequestParam double maxLon
    ) {
        List<PositionVessel> positions = service.getPositionsByDateAndBounds(dateStart, Optional.ofNullable(dateEnd), minLat, maxLat, minLon, maxLon);
        List<PositionVesselGeoJson> features = mapper.toGeoJson(positions);

        if (features.isEmpty()) {
            return ResponseEntity.status(HttpStatus.NO_CONTENT).build();
        }

        Map<String, Object> geoJson = Map.of(
                "type", "FeatureCollection",
                "features", features
            );

        return ResponseEntity.ok(geoJson);
    }

    @GetMapping("/{vesselId}")
    public ResponseEntity<Map<String,Object>> getPositionsByVesselIdAndOptionalDate(
            @PathVariable Integer vesselId,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate dateStart,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate dateEnd,
            @AuthenticationPrincipal CustomUserDetails currentUser
    ) {
        List<PositionVessel> positions = service.getPositionsByIdAndOptionalDate(vesselId,Optional.ofNullable(dateStart),Optional.ofNullable(dateEnd),currentUser.getUser());
        List<PositionVesselGeoJson> features = mapper.toGeoJson(positions);

        if (features.isEmpty()) {
            return ResponseEntity.status(HttpStatus.NO_CONTENT).build();
        }

        Map<String, Object> geoJson = Map.of(
                "type", "FeatureCollection",
                "features", features
            );

        return ResponseEntity.ok(geoJson);
    }

    @Operation(summary = "Get latest positions from users' vessels")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Vessels Positions Retrieved Successfuly")
    })
    @GetMapping("/latest")
    public ResponseEntity<Map<String, Object>> getLatestPosition(
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "50") int size,
        @RequestParam(name = "mmsis", required = false) List<String> mmsi,
        @AuthenticationPrincipal CustomUserDetails customUserDetails) {
            Pageable pageable = PageRequest.of(page, size);
            List<PositionVessel> positions = service.getLatestPositions(customUserDetails, mmsi, pageable);
            List<PositionVesselGeoJson> features = mapper.toGeoJson(positions);

            if (features.isEmpty()) {
                return ResponseEntity.status(HttpStatus.NO_CONTENT).build();
            }

            Map<String, Object> geoJson = Map.of(
                "type", "FeatureCollection",
                "features", features
            );

            return ResponseEntity.ok(geoJson);
    }
}
