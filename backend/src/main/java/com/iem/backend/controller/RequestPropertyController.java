package com.iem.backend.controller;

import com.iem.backend.dto.requestProperty.RequestPropertyDetails;
import com.iem.backend.dto.requestProperty.RequestPropertyRequest;
import com.iem.backend.entity.CustomUserDetails;
import com.iem.backend.service.RequestPropertyService;

import jakarta.validation.Valid;
import org.springframework.data.domain.Page;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/request-property")
public class RequestPropertyController {

    RequestPropertyService requestPropertyService;

    public RequestPropertyController(RequestPropertyService requestPropertyService) {
        this.requestPropertyService = requestPropertyService;
    }

    @PostMapping
    @PreAuthorize("hasAnyRole('OWNER','ADMIN')")
    public ResponseEntity<Void> createRequestProperty(
            @Valid @RequestBody RequestPropertyRequest dto,
            @AuthenticationPrincipal CustomUserDetails currentUser
    ) {
        requestPropertyService.createRequestProperty(dto, currentUser);
        return ResponseEntity.noContent().build();
    }

    @GetMapping
    @PreAuthorize("hasRole('ADMIN')")
        public ResponseEntity<Page<RequestPropertyDetails>> getAllRequestProperty(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "100") int size,
            @RequestParam(defaultValue = "id,asc") String[] sort,
            @RequestParam(required = false) String search
    ) {
        String sortField = sort[0];
        String sortDirection = sort.length > 1 ? sort[1] : "asc";

        return ResponseEntity.ok(
                requestPropertyService.getAllRequestProperty(page, size, sortField, sortDirection, search)
        );
    }

    @GetMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
        public ResponseEntity<RequestPropertyDetails> getRequestPropertyById(@PathVariable Integer id) {
        return ResponseEntity.ok(requestPropertyService.getRequestPropertyById(id));
    }

    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
        public ResponseEntity<RequestPropertyDetails> deleteRequestPropertyById(@PathVariable Integer id) {
        return ResponseEntity.ok(requestPropertyService.deleteRequestPropertyById(id));
    }

    @PutMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
        public ResponseEntity<RequestPropertyDetails> updateRequestPropertyById(
                @PathVariable Integer id,
                @Valid @RequestBody RequestPropertyRequest dto
    ) {
        return ResponseEntity.ok(requestPropertyService.updateRequestProperty(id, dto));
    }

}
