package com.iem.backend.controller;

import com.iem.backend.dto.RequestPropertyDto;
import com.iem.backend.service.RequestPropertyService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/request-property")
public class RequestPropertyController {

    RequestPropertyService requestPropertyService;

    public RequestPropertyController(RequestPropertyService requestPropertyService) {
        this.requestPropertyService = requestPropertyService;
    }

    @Operation(
            summary = "Create a request property",
            description = "An user can create a request property"
    )
    @ApiResponses(
            value = {
                    @ApiResponse(responseCode = "200", description = "Request Property created"),
                    @ApiResponse(responseCode = "400", description = "Invalid Request"),
                    @ApiResponse(responseCode = "401", description = "Unauthorized"),
                    @ApiResponse(responseCode = "404", description = "User, Vessel or File Not Found")
            }
    )
    @PostMapping
    public ResponseEntity<String> postRequestProperty(@Valid @RequestBody RequestPropertyDto dto) {
        Integer userid = dto.userid();
        String mmsi = dto.mmsi();
        Integer fileid = dto.fileid();
        requestPropertyService.postRequestProperty(userid, mmsi, fileid);
        return ResponseEntity.ok("Request property created");
    }

}
