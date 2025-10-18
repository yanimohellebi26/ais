package com.iem.backend.controller;

import com.iem.backend.entity.FileUpload;
import com.iem.backend.entity.Role;
import com.iem.backend.entity.User;
import com.iem.backend.repository.FileUploadRepository;
import com.iem.backend.repository.RoleRepository;
import com.iem.backend.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.ResultActions;
import org.springframework.util.StringUtils;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Comparator;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class FileUploadControllerTest {

    private static final long TEN_MB = 10 * 1024 * 1024;

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private FileUploadRepository fileUploadRepository;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private RoleRepository roleRepository;

    @Value("${app.upload.dir}")
    private String uploadDir;

    @BeforeEach
    void setUp() throws Exception {
        fileUploadRepository.deleteAll();
        userRepository.deleteAll();
        roleRepository.deleteAll();
        cleanStorageDirectory();
    }

    @Test
    @WithMockUser(username = "captain@example.com", roles = "USER")
    void uploadFile_successfullyStoresFileAndMetadata() throws Exception {
        User user = persistUser("captain@example.com");
        MockMultipartFile file = new MockMultipartFile(
                "file",
                "notes.txt",
                "text/plain",
                "ahoy".getBytes()
        );

        ResultActions result = mockMvc.perform(multipart("/api/v1/uploads").file(file));

        result.andExpect(status().isCreated())
                .andExpect(jsonPath("$.path").isNotEmpty())
                .andExpect(jsonPath("$.originalFilename").value("notes.txt"))
                .andExpect(jsonPath("$.sizeBytes").value(file.getSize()));

        List<FileUpload> uploads = fileUploadRepository.findAll();
        assertThat(uploads).hasSize(1);

        FileUpload upload = uploads.get(0);
        assertThat(upload.getUser().getId()).isEqualTo(user.getId());
        assertThat(upload.getStoredFilename()).isNotEqualTo("notes.txt");
        assertThat(upload.getStoredFilename()).endsWith(".txt");
        assertThat(upload.getStoredFilename().length()).isEqualTo(64 + ".txt".length());

        Path storedPath = Paths.get(uploadDir).toAbsolutePath().normalize().resolve(upload.getStoredFilename());
        assertThat(Files.exists(storedPath)).isTrue();
    }

    @Test
    @WithMockUser(username = "limit@example.com", roles = "USER")
    void uploadFile_respectsPerUserLimit() throws Exception {
        persistUser("limit@example.com");

        for (int i = 0; i < 10; i++) {
            MockMultipartFile file = new MockMultipartFile(
                    "file",
                    "doc" + i + ".txt",
                    "text/plain",
                    ("content" + i).getBytes()
            );

            mockMvc.perform(multipart("/api/v1/uploads").file(file))
                    .andExpect(status().isCreated());
        }

        MockMultipartFile overflowFile = new MockMultipartFile(
                "file",
                "overflow.txt",
                "text/plain",
                "too-many".getBytes()
        );

        mockMvc.perform(multipart("/api/v1/uploads").file(overflowFile))
                .andExpect(status().isTooManyRequests());

        assertThat(fileUploadRepository.count()).isEqualTo(10);
    }

    @Test
    @WithMockUser(username = "size@example.com", roles = "USER")
    void uploadFile_rejectsPayloadAboveConfiguredLimit() throws Exception {
        persistUser("size@example.com");

        byte[] oversized = new byte[(int) (TEN_MB + 1)];
        MockMultipartFile file = new MockMultipartFile(
                "file",
                "huge.bin",
                "application/octet-stream",
                oversized
        );

        mockMvc.perform(multipart("/api/v1/uploads").file(file))
                .andExpect(status().isPayloadTooLarge());

        assertThat(fileUploadRepository.count()).isZero();
    }

    private User persistUser(String email) {
        Role role = roleRepository.findByNameIgnoreCase("USER")
                .orElseGet(() -> {
                    Role newRole = new Role();
                    newRole.setName("USER");
                    return roleRepository.save(newRole);
                });

        User user = new User();
        user.setUsername(extractUsername(email));
        user.setEmail(email);
        user.setPasswordHash("secret");
        user.setRole(role);
        return userRepository.save(user);
    }

    private String extractUsername(String email) {
        return StringUtils.hasText(email) && email.contains("@")
                ? email.substring(0, email.indexOf('@'))
                : email;
    }

    private void cleanStorageDirectory() throws Exception {
        Path root = Paths.get(uploadDir).toAbsolutePath().normalize();
        if (!Files.exists(root)) {
            Files.createDirectories(root);
            return;
        }

        try (var paths = Files.walk(root)) {
            paths.filter(path -> !path.equals(root))
                    .sorted(Comparator.reverseOrder())
                    .forEach(path -> {
                        try {
                            Files.deleteIfExists(path);
                        } catch (Exception ignored) {
                            // best effort cleanup for test isolation
                        }
                    });
        }
    }
}
