package com.iem.backend.controller;

import com.iem.backend.dto.fileUpload.FileUploadDetails;
import com.iem.backend.dto.fileUpload.FileUploadResponse;
import com.iem.backend.entity.CustomUserDetails;
import com.iem.backend.entity.FileUpload;
import com.iem.backend.service.FileUploadService;

import org.springframework.core.io.Resource;
import org.springframework.http.ContentDisposition;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.nio.charset.StandardCharsets;

@RestController
@RequestMapping("/api/v1")
public class FileUploadController {

    private final FileUploadService fileUploadService;

    public FileUploadController(FileUploadService fileUploadService) {
        this.fileUploadService = fileUploadService;
    }

    @PostMapping(path = "/uploads",
            consumes = MediaType.MULTIPART_FORM_DATA_VALUE,
            produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<FileUploadResponse> uploadFile (
            @RequestParam("file") MultipartFile file,
            @AuthenticationPrincipal CustomUserDetails currentUser) {
        FileUploadResponse response = fileUploadService.store(file, currentUser);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @GetMapping(path = "/uploads/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<FileUploadDetails> getFileDetails(@PathVariable Integer id) {
        return ResponseEntity.ok(fileUploadService.getFileDetails(id));
    }

    @GetMapping(path = "/uploads/{id}/download")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Resource> downloadFile(@PathVariable Integer id) {
        FileUpload fileUpload = fileUploadService.getFileById(id);
        Resource resource = fileUploadService.loadAsResource(fileUpload);

        ContentDisposition contentDisposition = ContentDisposition.attachment()
                .filename(fileUpload.getOriginalFilename(), StandardCharsets.UTF_8)
                .build();

        return ResponseEntity.ok()
                .contentLength(fileUpload.getFileSize())
                .contentType(MediaType.APPLICATION_OCTET_STREAM)
                .header(HttpHeaders.CONTENT_DISPOSITION, contentDisposition.toString())
                .body(resource);
    }
}
