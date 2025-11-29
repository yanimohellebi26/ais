package com.iem.backend.controller;
import com.iem.backend.dto.vessel.*;
import com.iem.backend.entity.CustomUserDetails;
import com.iem.backend.service.VesselService;
import jakarta.validation.Valid;

import java.util.List;

import org.springdoc.core.annotations.ParameterObject;
import org.springframework.data.domain.Page;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/vessels")
public class VesselController {

    private final VesselService vesselService;

    public VesselController(VesselService vesselService) {
        this.vesselService = vesselService;
    }

    @GetMapping
    public ResponseEntity<Page<VesselDetails>> getAllVessels(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "100") int size,
            @RequestParam(defaultValue = "id,asc") String[] sort,
            @ParameterObject VesselFilter filter
    ) {
        String sortField = sort[0];
        String sortDirection = sort.length > 1 ? sort[1] : "asc";

        return ResponseEntity.ok(
                vesselService.getAllVessels(page, size, sortField, sortDirection, filter)
        );
    }


    @GetMapping("/{id}")
    public ResponseEntity<VesselDetails> getVesselById(@PathVariable Integer id) {
        return ResponseEntity.ok(vesselService.findById(id));
    }

    @PostMapping()
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<VesselDetails> createVessel(@Valid @RequestBody VesselCreateRequest dto) {
        return ResponseEntity.status(HttpStatus.CREATED).body(
                vesselService.createVessel(dto)
        );
    }

    @PutMapping("/{id}")
    @PreAuthorize("hasAnyRole('ADMIN','OWNER')")
    public ResponseEntity<VesselDetails> updateVessel(
            @PathVariable Integer id,
            @RequestBody VesselUpdateRequest dto,
            @AuthenticationPrincipal CustomUserDetails currentUser) {
        return ResponseEntity.ok(vesselService.updateVessel(id, dto, currentUser));
    }

    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Void> deleteVessel(@PathVariable Integer id) {
        vesselService.deleteVessel(id);
        return ResponseEntity.noContent().build();
    }

    @PostMapping("/related")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<VesselDetails> relateUserToVessel(@Valid @RequestBody VesselRelateRequest dto) {
        return ResponseEntity.ok(
                vesselService.relateUserToVessel(dto)
        );
    }

    @PostMapping("/unrelate")
    @PreAuthorize("hasAnyRole('ADMIN','OWNER')")
    public ResponseEntity<Void> unrelateUserFromVessel(
            @Valid @RequestBody VesselRelateRequest dto,
            @AuthenticationPrincipal CustomUserDetails currentUser) {
        vesselService.unrelate(dto,currentUser);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/userId/{id}")
    @PreAuthorize("hasAnyRole('ADMIN','OWNER','CAPTAIN')")
    public ResponseEntity<List<VesselUsersDetails>> getVesselsByUserId(
            @PathVariable Integer id,
            @AuthenticationPrincipal CustomUserDetails currentUser) {
        List<VesselUsersDetails> vessels = vesselService.getVesselsByUserId(id,currentUser);
        return ResponseEntity.ok(vessels);
    }

}
