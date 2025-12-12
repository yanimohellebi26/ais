package com.iem.backend.controller;

import com.iem.backend.common.geoJson.GeoJsonFeatureCollection;
import com.iem.backend.dto.ports.PortProperties;
import com.iem.backend.entity.Port;
import com.iem.backend.mapper.PortMapper;
import com.iem.backend.service.GeoJsonService;
import com.iem.backend.service.PortService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/ports")
public class PortController {

    private final PortService portService;
    private final PortMapper portMapper;
    private final GeoJsonService geoJsonService;

    public PortController(PortService portService, PortMapper portMapper, GeoJsonService geoJsonService) {
        this.portService = portService;
        this.portMapper = portMapper;
        this.geoJsonService = geoJsonService;
    }

    @GetMapping
    public ResponseEntity<GeoJsonFeatureCollection<PortProperties>> getAllPorts() {
        List<Port> ports = portService.getPorts();
        if (ports.isEmpty()) return ResponseEntity.noContent().build();

        return ResponseEntity.ok(
                geoJsonService.toGeoJson(
                        ports,
                        Port::getId,
                        portMapper::toProperties,
                        Port::getGeom
                )
        );
    }

    @GetMapping("/bounds")
    public ResponseEntity<GeoJsonFeatureCollection<PortProperties>> getPortsByBounds(
            @RequestParam double minLat,
            @RequestParam double maxLat,
            @RequestParam double minLon,
            @RequestParam double maxLon,
            @RequestParam(defaultValue = "200") int limit
    ) {
        List<Port> ports = portService.getPortByBounds(minLat, maxLat, minLon, maxLon, limit);
        if (ports.isEmpty()) return ResponseEntity.noContent().build();

        return ResponseEntity.ok(
                geoJsonService.toGeoJson(
                        ports,
                        Port::getId,
                        portMapper::toProperties,
                        Port::getGeom
                )
        );
    }

    @GetMapping("/nearest")
    public ResponseEntity<GeoJsonFeatureCollection<PortProperties>> getNearestPort(
        @RequestParam double lat,
        @RequestParam double lon
    ) {
        Port port = portService.getNearestPort(lon, lat);
        if (port == null) return ResponseEntity.notFound().build();

        return ResponseEntity.ok(
                geoJsonService.toGeoJson(
                        List.of(port), 
                        Port::getId, 
                        portMapper::toProperties,
                        Port::getGeom
                )
        );
    }
}
