package com.iem.backend.controller;

import com.fasterxml.jackson.annotation.JsonView;
import com.iem.backend.dto.RequestPropertyDto;
import com.iem.backend.dto.UpdateRequestPropertyDto;
import com.iem.backend.dto.Views;
import com.iem.backend.service.RequestPropertyService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import jakarta.validation.Valid;
import org.springframework.data.domain.Page;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

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
    @JsonView(Views.Create.class)
    @PostMapping
    public ResponseEntity<String> postRequestProperty(@Valid @RequestBody RequestPropertyDto dto) {
        Integer userid = dto.userid();
        String mmsi = dto.mmsi();
        Integer fileid = dto.fileid();
        requestPropertyService.postRequestProperty(userid, mmsi, fileid);
        return ResponseEntity.ok("Request property created");
    }

    @Operation(
            summary = "Get all request property",
            description = "An admin can get all request property"
    )
    @ApiResponses(
            value = {
                    @ApiResponse(responseCode = "200", description = "Page of request property"),
                    @ApiResponse(responseCode = "400", description = "Invalid Request"),
                    @ApiResponse(responseCode = "401", description = "Unauthorized")
            }
    )
    @GetMapping
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Page<RequestPropertyDto>> getAllRequestProperty(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "100") int size,
            @RequestParam(defaultValue = "id,asc") String[] sort,
            @RequestParam(required = false) String search
    ) {
        String sortField = sort[0];
        String sortDirection = sort.length > 1 ? sort[1] : "asc";

        Page<RequestPropertyDto> requestPropertyPage = requestPropertyService.getAllRequestProperty(page, size, sortField, sortDirection, search);
        return ResponseEntity.ok(requestPropertyPage);
    }

    @Operation(
            summary = "Get request property by id",
            description = "An admin can get request property by id"
    )
    @ApiResponses(
            value = {
                    @ApiResponse(responseCode = "200", description = "Get request property"),
                    @ApiResponse(responseCode = "400", description = "Invalid Request"),
                    @ApiResponse(responseCode = "401", description = "Unauthorized"),
                    @ApiResponse(responseCode = "404", description = "Request Property Not Found")
            }
    )
    @GetMapping("/{id}")
    @JsonView(Views.Admin.class)
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<RequestPropertyDto> getRequestPropertyById(@PathVariable Integer id) {
        RequestPropertyDto requestPropertyResponseDto = requestPropertyService.getRequestPropertyById(id);
        return ResponseEntity.ok(requestPropertyResponseDto);
    }

    @Operation(
            summary = "Delete request property by id",
            description = "An admin can delete request property by id"
    )
    @ApiResponses(
            value = {
                    @ApiResponse(responseCode = "200", description = "Request property are deleted"),
                    @ApiResponse(responseCode = "400", description = "Invalid Request"),
                    @ApiResponse(responseCode = "401", description = "Unauthorized"),
                    @ApiResponse(responseCode = "404", description = "Request Property Not Found")
            }
    )
    @DeleteMapping("/{id}")
    @JsonView(Views.Admin.class)
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<RequestPropertyDto> deleteRequestPropertyById(@PathVariable Integer id) {
        RequestPropertyDto requestPropertyResponseDto = requestPropertyService.deleteRequestPropertyById(id);
        return ResponseEntity.ok(requestPropertyResponseDto);
    }

    @Operation(
            summary = "Update a request property",
            description = "An admin can update a request property"
    )
    @ApiResponses(
            value = {
                    @ApiResponse(responseCode = "200", description = "Request Property updated"),
                    @ApiResponse(responseCode = "400", description = "Invalid Request"),
                    @ApiResponse(responseCode = "401", description = "Unauthorized"),
                    @ApiResponse(responseCode = "404", description = "User, Vessel or File Not Found")
            }
    )
    @PutMapping
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<RequestPropertyDto> updateRequestPropertyById(@Valid @RequestBody UpdateRequestPropertyDto dto) {
        RequestPropertyDto requestPropertyResponseDto = requestPropertyService.updateRequestProperty(dto);
        return ResponseEntity.ok(requestPropertyResponseDto);
    }

}
