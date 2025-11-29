package com.iem.backend.controller;

import com.iem.backend.dto.vesselType.VesselTypeDetails;
import com.iem.backend.service.VesselTypeService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/v1/vessel-type")
public class VesselTypeController {
    private final VesselTypeService vesselTypeService;

    public VesselTypeController(VesselTypeService vesselTypeService) {
        this.vesselTypeService = vesselTypeService;
    }

    @GetMapping
    public ResponseEntity<List<VesselTypeDetails>> getAll() {
        return ResponseEntity.ok(vesselTypeService.getAll());
    }
}
