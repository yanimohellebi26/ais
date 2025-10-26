package com.iem.backend.controller;

import java.util.List;

import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.fasterxml.jackson.annotation.JsonView;
import com.iem.backend.dto.PositionVesselDTO;
import com.iem.backend.dto.Views;
import com.iem.backend.service.PositionService;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;

@RestController
@RequestMapping("/api/v1/positions")
public class PositionsController {
    
    private final PositionService positionService;

    public PositionsController(PositionService positionService) {
        this.positionService = positionService;
    }

    @Operation(summary = "Get latest positions from users' vessels")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Vessels Positions Retrieved Successfuly")
    })
    @JsonView(Views.Public.class)
    @GetMapping("/latest")
    public ResponseEntity<List<PositionVesselDTO>> getLatestPosition(
        @RequestParam(name = "mmsi", required = false) List<String> mmsi,
        @AuthenticationPrincipal UserDetails userDetails) {
            List<PositionVesselDTO> positions = positionService.getLatestPositions(userDetails, mmsi);
            return ResponseEntity.ok(positions);
    }
}
