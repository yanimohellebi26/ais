package com.iem.backend.controller;

import com.iem.backend.dto.RequestPropertyDto;
import com.iem.backend.service.RequestPropertyService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/request")
public class RequestPropertyController {

    RequestPropertyService requestPropertyService;

    public RequestPropertyController(RequestPropertyService requestPropertyService) {
        this.requestPropertyService = requestPropertyService;
    }

    @PostMapping
    public ResponseEntity<String> postRequestProperty(@Valid @RequestBody RequestPropertyDto dto) {
        Integer userid = dto.userid();
        String mmsi = dto.mmsi();
        Integer fileid = dto.fileid();
        requestPropertyService.postRequestProperty(userid, mmsi, fileid);
        return ResponseEntity.ok("Request property posted");
    }

}
