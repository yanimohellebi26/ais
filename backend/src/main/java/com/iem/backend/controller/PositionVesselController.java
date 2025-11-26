package com.iem.backend.controller;

import com.iem.backend.common.geoJson.GeoJsonFeatureCollection;
import com.iem.backend.dto.positionVessel.PositionVesselProperties;
import com.iem.backend.dto.positionVessel.PositionVesselRadiusProperties;
import com.iem.backend.entity.CustomUserDetails;
import com.iem.backend.exception.ApiExceptions;
import com.iem.backend.mapper.PositionVesselMapper;
import com.iem.backend.service.GeoJsonService;
import com.iem.backend.service.PositionVesselService;

import com.iem.backend.entity.PositionVessel;

import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@RestController
@RequestMapping("/api/v1/positions")
public class PositionVesselController {

    private final PositionVesselService positionVesselService;
    private final PositionVesselMapper positionVesselMapper;
    private final GeoJsonService geoJsonService;

    public PositionVesselController(PositionVesselService positionVesselService, PositionVesselMapper positionVesselMapper, GeoJsonService geoJsonService) {
        this.positionVesselService = positionVesselService;
        this.positionVesselMapper = positionVesselMapper;
        this.geoJsonService = geoJsonService;
    }

    @GetMapping
    public ResponseEntity<GeoJsonFeatureCollection<PositionVesselProperties>> getPositionsVessels(
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate dateStart,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate dateEnd,
            @RequestParam double minLat,
            @RequestParam double maxLat,
            @RequestParam double minLon,
            @RequestParam double maxLon,
            @RequestParam(defaultValue = "200") int limit,
            @AuthenticationPrincipal CustomUserDetails currentUser
    ) {
        List<String> allowed = List.of("ADMIN","MARITIME_EXPERT","FINANCIAL_ANALYST");
        List<PositionVessel> positions;

        if (allowed.contains(currentUser.getUser().getRole().getName())) {
            positions = positionVesselService.getPositionsByDateAndBounds(dateStart, Optional.ofNullable(dateEnd), minLat, maxLat, minLon, maxLon, limit);
        } else {
            positions = positionVesselService.getUserVesselsPositionsByDateAndBounds(currentUser.getUser().getId(),dateStart, Optional.ofNullable(dateEnd), minLat, maxLat, minLon, maxLon, limit);
        }

        if(positions.isEmpty()) {
            return new ResponseEntity<>(HttpStatus.NO_CONTENT);
        }
        return ResponseEntity.ok(
                geoJsonService.toGeoJson(
                        positions,
                        positionVesselMapper::toProperties,
                        PositionVessel::getGeom
                )
        );
    }

    @GetMapping("/{vesselId}")
    public ResponseEntity<GeoJsonFeatureCollection<PositionVesselProperties>> getPositionsByVesselIdAndOptionalDate(
            @PathVariable Integer vesselId,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate dateStart,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate dateEnd,
            @AuthenticationPrincipal CustomUserDetails currentUser
    ) {
        List<PositionVessel> positions = positionVesselService.getPositionsByIdAndOptionalDate(vesselId,Optional.ofNullable(dateStart),Optional.ofNullable(dateEnd),currentUser.getUser());
        if (positions.isEmpty()) {
            return ResponseEntity.status(HttpStatus.NO_CONTENT).build();
        }

        return ResponseEntity.ok(
                geoJsonService.toGeoJson(
                        positions,
                        positionVesselMapper::toProperties,
                        PositionVessel::getGeom
                )
        );
    }

    @GetMapping("/latest")
    public ResponseEntity<GeoJsonFeatureCollection<PositionVesselProperties>> getLatestPositions(
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "50") int size,
        @RequestParam(name = "ids", required = false) List<Integer> ids,
        @AuthenticationPrincipal CustomUserDetails curentUser) {

        List<PositionVessel> positions = positionVesselService.getLatestPositions(curentUser, ids, page, size);
        if (positions.isEmpty()) {
            return ResponseEntity.status(HttpStatus.NO_CONTENT).build();
        }

        return ResponseEntity.ok(
                geoJsonService.toGeoJson(
                        positions,
                        positionVesselMapper::toProperties,
                        PositionVessel::getGeom
                )
        );
    }

    @GetMapping("/latest/in-bounds")
    public ResponseEntity<GeoJsonFeatureCollection<PositionVesselProperties>> getPositionsInBounds(
        @RequestParam double minLat,
        @RequestParam double maxLat,
        @RequestParam double minLon,
        @RequestParam double maxLon,
        @RequestParam(defaultValue = "200") int limit,
        @AuthenticationPrincipal CustomUserDetails currentUser
    ) {
        List<PositionVessel> positions = positionVesselService.getLatestPositionsInBounds(
            currentUser, minLat, maxLat, minLon, maxLon, limit
        );

        if (positions.isEmpty()) {
            return ResponseEntity.status(HttpStatus.NO_CONTENT).build();
        }

        return ResponseEntity.ok(
                geoJsonService.toGeoJson(
                        positions,
                        positionVesselMapper::toProperties,
                        PositionVessel::getGeom
                )
        );
    }

    @GetMapping("/radius")
    public ResponseEntity<GeoJsonFeatureCollection<PositionVesselRadiusProperties>> getPositionsAroundVessel(
            @RequestParam Integer vesselId,
            @RequestParam(required = false) String date,
            @RequestParam(required = false, defaultValue = "50.0") Double radiusKm,
            @AuthenticationPrincipal CustomUserDetails currentUser
    ) {

        Optional<Object> parsedDate = parseDate(date);

        if (parsedDate.isEmpty() && date != null && !date.isBlank()) {
            throw new ApiExceptions.BadRequestException("Invalid or future date format");
        }

        List<PositionVessel> positions = positionVesselService.getPositionsAroundVesselById(
                vesselId,
                parsedDate,
                radiusKm,
                currentUser
        );

        if (positions.isEmpty()) {
            return ResponseEntity.noContent().build();
        }

        Map<Long, PositionVesselRadiusProperties> radiusMap =
                positionVesselService.mapWithDistance(positions, vesselId, parsedDate);

        GeoJsonFeatureCollection<PositionVesselRadiusProperties> geojson =
                geoJsonService.toGeoJson(
                        positions,
                        pv -> radiusMap.get(pv.getId()),
                        PositionVessel::getGeom
                );

        return ResponseEntity.ok(geojson);
    }

    private Optional<Object> parseDate(String date) {
        if (date == null || date.isBlank()) return Optional.empty();

        date = date.trim();
        try {
            if (date.contains(" ") || date.contains(":")) {
                LocalDateTime ldt = LocalDateTime.parse(date, DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
                return ldt.isAfter(LocalDateTime.now()) ? Optional.empty() : Optional.of(ldt);
            } else {
                LocalDate ld = LocalDate.parse(date, DateTimeFormatter.ISO_LOCAL_DATE);
                return ld.isAfter(LocalDate.now()) ? Optional.empty() : Optional.of(ld);
            }
        } catch (DateTimeParseException e) {
            return Optional.empty();
        }
    }

}
