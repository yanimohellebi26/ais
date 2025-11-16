package com.iem.backend.controller;

import com.iem.backend.dto.ports.PortGeoJson;
import com.iem.backend.entity.Port;
import com.iem.backend.service.PortService;
import com.iem.backend.service.mapper.PortMapper;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/ports")
public class PortController {

    private final PortService service;
    private final PortMapper mapper;

    public PortController(PortService service, PortMapper mapper) {
        this.service = service;
        this.mapper = mapper;
    }

    @GetMapping
    public ResponseEntity<Map<String,Object>> getPorts() {
        List<Port> ports = service.getPorts();
        List<PortGeoJson> features = mapper.toGeoJson(ports);

        if (features.isEmpty()) {
            return ResponseEntity.status(HttpStatus.NO_CONTENT).build();
        }

        Map<String, Object> geoJson = Map.of(
                "type", "FeatureCollection",
                "features", features
        );

        return ResponseEntity.ok(geoJson);
    }

    @GetMapping("/bounds")
    public ResponseEntity<Map<String, Object>> getPorts(
            @RequestParam double minLat,
            @RequestParam double maxLat,
            @RequestParam double minLon,
            @RequestParam double maxLon,
            @RequestParam(defaultValue = "200") int limit
    ) {
        List<Port> ports = service.getPortByBounds(minLat, maxLat, minLon, maxLon, limit);
        List<PortGeoJson> features = mapper.toGeoJson(ports);

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
