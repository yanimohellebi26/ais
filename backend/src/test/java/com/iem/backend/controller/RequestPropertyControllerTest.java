package com.iem.backend.controller;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.iem.backend.dto.RequestPropertyDto;
import com.iem.backend.entity.FileUpload;
import com.iem.backend.entity.Vessel;
import com.iem.backend.repository.FileUploadRepository;
import com.iem.backend.repository.VesselRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.http.MediaType;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.iem.backend.entity.Role;
import com.iem.backend.entity.User;
import com.iem.backend.repository.RoleRepository;
import com.iem.backend.repository.UserRepository;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.sql.Timestamp;
import java.time.LocalDateTime;
import java.util.Comparator;

@SpringBootTest
@AutoConfigureMockMvc
@TestPropertySource(properties = {
        "spring.datasource.url=jdbc:h2:mem:testdb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
        "spring.datasource.username=sa",
        "spring.datasource.password=",
        "spring.datasource.driver-class-name=org.h2.Driver",
        "spring.jpa.hibernate.ddl-auto=create-drop",
        "spring.jpa.show-sql=false"
})
public class RequestPropertyControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Value("${app.upload.dir}")
    private String uploadDir;
    @Autowired
    private FileUploadRepository fileUploadRepository;

    @Autowired
    private RoleRepository roleRepository;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private PasswordEncoder passwordEncoder;

    @Autowired
    private VesselRepository vesselRepository;

    private Role ownerRole;
    private User user;
    private Vessel vessel;
    private Vessel vesselOwner;
    private FileUpload file;

    @BeforeEach
    void setUp() throws Exception {
        fileUploadRepository.deleteAll();
        vesselRepository.deleteAll();
        userRepository.deleteAll();
        roleRepository.deleteAll();
        cleanStorageDirectory();

        ownerRole = new Role();
        ownerRole.setName("OWNER");
        roleRepository.save(ownerRole);

        user = new User();
        user.setUsername("testUser");
        user.setEmail("test@example.com");
        user.setPasswordHash(passwordEncoder.encode("oldPassword#123"));
        user.setRole(ownerRole);
        userRepository.save(user);

        vessel = new Vessel();
        vessel.setMmsi("123456789");
        vessel.setVesselName("Vessel 1");
        vessel.setBaseDateTime(Timestamp.valueOf(LocalDateTime.now()));
        vessel.setCreatedAt(Timestamp.valueOf(LocalDateTime.now()));
        vesselRepository.save(vessel);

        vesselOwner = new Vessel();
        vesselOwner.setMmsi("012345678");
        vesselOwner.setVesselName("Vessel 2");
        vesselOwner.setBaseDateTime(Timestamp.valueOf(LocalDateTime.now()));
        vesselOwner.setCreatedAt(Timestamp.valueOf(LocalDateTime.now()));
        vesselOwner.getUsers().add(user);
        vesselRepository.save(vesselOwner);

        file = new FileUpload();
        file.setStoredFilename("fileUpload");
        file.setOriginalFilename("fileUpload");
        file.setUser(user);
        file.setFileSize(10);
        fileUploadRepository.save(file);
    }

    @Test
    @WithMockUser(username = "test@example.com", roles = "USER")
    void CreateRequestPropertySuccessTest() throws Exception {
        RequestPropertyDto payload = new RequestPropertyDto(user.getId(),vessel.getMmsi(),file.getId());
        mockMvc.perform(post("/api/v1/request-property")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(payload)))
                .andExpect(status().isOk());
    }

    @Test
    @WithMockUser(username = "test@example.com", roles = "USER")
    void CreateRequestPropertyNotFoundTest() throws Exception {
        RequestPropertyDto payload = new RequestPropertyDto(user.getId(),vessel.getMmsi(),-1);
        mockMvc.perform(post("/api/v1/request-property")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(payload)))
                .andExpect(status().isNotFound());
        payload = new RequestPropertyDto(user.getId(),"mmsifaux",file.getId());
        mockMvc.perform(post("/api/v1/request-property")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(payload)))
                .andExpect(status().isNotFound());
        payload = new RequestPropertyDto(-1,vessel.getMmsi(),file.getId());
        mockMvc.perform(post("/api/v1/request-property")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(payload)))
                .andExpect(status().isNotFound());
    }

    @Test
    void CreateRequestPropertyUnauthorizedTest() throws Exception {
        RequestPropertyDto payload = new RequestPropertyDto(user.getId(),vessel.getMmsi(),file.getId());
        mockMvc.perform(post("/api/v1/request-property")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(payload)))
                .andExpect(status().isUnauthorized());
    }

    @Test
    @WithMockUser(username = "test@example.com", roles = "OWNER")
    void CreateRequestPropertyOwnerTest() throws Exception {
        RequestPropertyDto payload = new RequestPropertyDto(user.getId(),vesselOwner.getMmsi(),file.getId());
        mockMvc.perform(post("/api/v1/request-property")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(payload)))
                .andExpect(status().isBadRequest());
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
