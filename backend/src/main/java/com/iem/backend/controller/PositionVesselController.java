package com.iem.backend.controller;

import com.iem.backend.dto.positionVessel.PositionVesselGeoJson;
import com.iem.backend.entity.CustomUserDetails;
import com.iem.backend.service.PositionVesselService;
import com.iem.backend.service.mapper.PositionVesselMapper;
import com.iem.backend.entity.PositionVessel;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
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
    public Map<String, Object> getPositions(
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate dateStart,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate dateEnd,
            @RequestParam double minLat,
            @RequestParam double maxLat,
            @RequestParam double minLon,
            @RequestParam double maxLon
    ) {
        List<PositionVessel> positions = service.getPositionsByDateAndBounds(dateStart, Optional.ofNullable(dateEnd), minLat, maxLat, minLon, maxLon);
        List<PositionVesselGeoJson> features = mapper.toGeoJson(positions);

        return Map.of(
                "type", "FeatureCollection",
                "features", features
        );
    }

    @GetMapping("/{vesselId}")
    public Map<String,Object> getPositionsByVesselIdAndOptionalDate(
            @PathVariable Integer vesselId,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate dateStart,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate dateEnd,
            @AuthenticationPrincipal CustomUserDetails currentUser
    ) {
        List<PositionVessel> positions = service.getPositionsByIdAndOptionalDate(vesselId,Optional.ofNullable(dateStart),Optional.ofNullable(dateEnd),currentUser.getUser());
        List<PositionVesselGeoJson> features = mapper.toGeoJson(positions);
        return Map.of(
                "type", "FeatureCollection",
                "features", features
        );
    }
}
