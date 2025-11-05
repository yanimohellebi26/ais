package com.iem.backend.service;

import com.iem.backend.dto.FileUploadDetailsDto;
import com.iem.backend.dto.FileUploadResponse;
import com.iem.backend.entity.FileUpload;
import com.iem.backend.entity.User;
import com.iem.backend.exception.FileNotFoundException;
import com.iem.backend.exception.UserNotFoundException;
import com.iem.backend.repository.FileUploadRepository;
import com.iem.backend.repository.UserRepository;
import com.iem.backend.utils.ApiLogger;
import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;

import java.io.IOException;
import java.io.InputStream;
import java.net.MalformedURLException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.HexFormat;
import java.util.Objects;
import java.util.UUID;

@Service
public class FileUploadService {

    private final Path storageLocation;
    private final long maxFileSize;
    private final int perUserLimit;
    private final FileUploadRepository fileUploadRepository;
    private final UserRepository userRepository;
    private final ApiLogger apiLogger;
    private final String originalUploadDirProperty;

    public FileUploadService(
            @Value("${app.upload.dir:uploads}") String uploadDir,
            @Value("${app.upload.max-size-bytes:10485760}") long maxFileSize,
            @Value("${app.upload.per-user-limit:10}") int perUserLimit,
            FileUploadRepository fileUploadRepository,
            UserRepository userRepository,
            ApiLogger apiLogger
    ) {
        this.storageLocation = Paths.get(uploadDir).toAbsolutePath().normalize();
        this.originalUploadDirProperty = uploadDir;
        this.maxFileSize = maxFileSize;
        this.perUserLimit = perUserLimit;
        this.fileUploadRepository = fileUploadRepository;
        this.userRepository = userRepository;
        this.apiLogger = apiLogger;
    }

    @PostConstruct
    void initStorage() {
        try {
            Files.createDirectories(storageLocation);
            apiLogger.success("Upload directory ready at " + storageLocation);
        } catch (IOException e) {
            apiLogger.error("Failed to initialize upload directory", e);
            throw new IllegalStateException("Cannot create upload directory", e);
        }
    }

    @Transactional
    public FileUploadResponse store(MultipartFile file, String userEmail) {
        if (file == null || file.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "File is empty or missing");
        }

        if (file.getSize() > maxFileSize) {
            throw new ResponseStatusException(HttpStatus.PAYLOAD_TOO_LARGE, "Maximum upload size exceeded (10 MB)");
        }

        User user = userRepository.findByEmailIgnoreCase(userEmail)
        .orElseThrow(UserNotFoundException::new);

        enforcePerUserLimit(user);

        String originalName = StringUtils.hasText(file.getOriginalFilename())
        ? Objects.requireNonNull(file.getOriginalFilename()).trim()
        : "file";
        String extension = extractExtension(originalName);
        String hashedName = hashFilename(originalName);
        String storedFilename = hashedName + extension;
        Path targetLocation = storageLocation.resolve(storedFilename);

        try (InputStream inputStream = file.getInputStream()) {
            Files.copy(inputStream, targetLocation, StandardCopyOption.REPLACE_EXISTING);
        } catch (IOException e) {
            apiLogger.error("Failed to store uploaded file", e);
            throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, "Unable to store the uploaded file", e);
        }

        FileUpload upload = new FileUpload();
        upload.setUser(user);
        upload.setOriginalFilename(originalName);
        upload.setStoredFilename(storedFilename);
        upload.setFileSize(file.getSize());

        fileUploadRepository.save(upload);
        apiLogger.success("File " + originalName + " stored for user " + userEmail);

        String pathToReturn = buildResponsePath(storedFilename);

        return new FileUploadResponse(pathToReturn, originalName, file.getSize());
    }

    @Transactional(readOnly = true)
    public FileUpload getFileEntity(Integer id) {
        return fileUploadRepository.findById(id)
                .orElseThrow(FileNotFoundException::new);
    }

    @Transactional(readOnly = true)
    public FileUploadDetailsDto getFileDetails(Integer id) {
        FileUpload fileUpload = getFileEntity(id);
        return FileUploadDetailsDto.fromEntity(fileUpload);
    }

    @Transactional(readOnly = true)
    public Resource loadAsResource(FileUpload fileUpload) {
        try {
            Path filePath = storageLocation.resolve(fileUpload.getStoredFilename()).normalize();
            if (!Files.exists(filePath)) {
                throw new FileNotFoundException();
            }
            Resource resource = new UrlResource(filePath.toUri());
            if (resource.exists() && resource.isReadable()) {
                return resource;
            }
            throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, "File is not readable");
        } catch (MalformedURLException e) {
            throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, "Unable to read the stored file", e);
        }
    }

    @Transactional(readOnly = true)
    public Resource loadAsResource(Integer id) {
        FileUpload fileUpload = getFileEntity(id);
        return loadAsResource(fileUpload);
    }

    @Transactional
    public void deleteFile(FileUpload fileUpload) {
        Path filePath = storageLocation.resolve(fileUpload.getStoredFilename()).normalize();
        try {
            Files.deleteIfExists(filePath);
        } catch (IOException e) {
            apiLogger.error("Failed to delete stored file " + filePath, e);
        }
        fileUploadRepository.delete(fileUpload);
    }

    private void enforcePerUserLimit(User user) {
        if (perUserLimit <= 0) {
            return;
        }

        long uploadsCount = fileUploadRepository.countByUser_Id(user.getId());
        if (uploadsCount >= perUserLimit) {
            throw new ResponseStatusException(HttpStatus.TOO_MANY_REQUESTS,
                    "Per-user upload limit of " + perUserLimit + " files reached");
        }
    }

    private String buildResponsePath(String storedFilename) {
        if (Paths.get(originalUploadDirProperty).isAbsolute()) {
            return storageLocation.resolve(storedFilename).toString();
        }
        return Paths.get(originalUploadDirProperty, storedFilename).toString().replace('\\', '/');
    }

    private String extractExtension(String filename) {
        int lastDot = filename.lastIndexOf('.');
        if (lastDot == -1 || lastDot == filename.length() - 1) {
            return "";
        }
        return filename.substring(lastDot);
    }

    private String hashFilename(String originalName) {
        String seed = originalName + ":" + Instant.now() + ":" + UUID.randomUUID();
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hashed = digest.digest(seed.getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(hashed);
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException("SHA-256 algorithm not available", e);
        }
    }
}
