package com.iem.backend.controller;
import com.iem.backend.dto.RequestVesselDto;
import com.iem.backend.dto.ResponseVesselDto;
import com.iem.backend.dto.UserVesselRequestDto;
import com.iem.backend.dto.VesselResponseDto;
import com.iem.backend.service.VesselService;
import jakarta.validation.Valid;

import java.security.Principal;
import java.util.List;

import org.springframework.data.domain.Page;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

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
            @RequestParam(defaultValue = "id,asc") String[] sort,
            @RequestParam(required = false) String search
    ) {
        String sortField = sort[0];
        String sortDirection = sort.length > 1 ? sort[1] : "asc";

        Page<VesselResponseDto> vesselsPage = vesselService.getAllVessels(page, size, sortField, sortDirection, search);
        return ResponseEntity.ok(vesselsPage);
    }

    @GetMapping("/{id}")
    public ResponseEntity<VesselResponseDto> getVesselById(@PathVariable Integer id){
        return ResponseEntity.ok(vesselService.findById(id));
    } 

    @PostMapping() 
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ResponseVesselDto> createVessel(@Valid @RequestBody RequestVesselDto dto){
        ResponseVesselDto vesselCreated = vesselService.createVessel(dto);
        return ResponseEntity.status(HttpStatus.CREATED).body(vesselCreated);
    }

    @PutMapping("/{id}")
    @PreAuthorize("hasAnyRole('ADMIN','OWNER')")
    public ResponseEntity<VesselResponseDto> updateVessel (@PathVariable Integer id, @RequestBody RequestVesselDto dto,Principal principal){
        return ResponseEntity.ok(vesselService.updateVessel(id,dto,principal));
    }

    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Void> deleteVessel (@PathVariable Integer id){
        vesselService.deleteVessel(id);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/userId/{id}")
    @PreAuthorize("hasAnyRole('ADMIN','OWNER','CAPTAIN')")
    public ResponseEntity<List<VesselResponseDto>> getVesselsByUserID(@PathVariable Integer id, Principal principal){
        List<VesselResponseDto> vessels = vesselService.getVesselsByUserID(id,principal);
        return ResponseEntity.ok(vessels);
    }
    
}

