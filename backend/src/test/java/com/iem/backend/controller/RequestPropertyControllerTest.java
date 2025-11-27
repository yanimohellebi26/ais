package com.iem.backend.controller;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.iem.backend.dto.requestProperty.RequestPropertyRequest;
import com.iem.backend.entity.*;
import com.iem.backend.repository.FileUploadRepository;
import com.iem.backend.repository.RequestPropertyRepository;
import com.iem.backend.repository.RoleRepository;
import com.iem.backend.repository.UserRepository;
import com.iem.backend.repository.VesselRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.http.MediaType;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.sql.Timestamp;
import java.time.LocalDateTime;
import java.time.OffsetDateTime;
import java.util.Comparator;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class RequestPropertyControllerTest {

    @Autowired private MockMvc mockMvc;
    @Autowired private ObjectMapper objectMapper;

    @Autowired private FileUploadRepository fileUploadRepository;
    @Autowired private RequestPropertyRepository requestPropertyRepository;
    @Autowired private VesselRepository vesselRepository;
    @Autowired private RoleRepository roleRepository;
    @Autowired private UserRepository userRepository;

    @Value("${app.upload.dir}") private String uploadDir;

    private User user;
    private User admin;
    private Vessel vessel;
    private Vessel vesselOwner;
    private FileUpload file;

    @BeforeEach
    void setUp() throws Exception {
        requestPropertyRepository.deleteAll();
        fileUploadRepository.deleteAll();
        vesselRepository.deleteAll();
        userRepository.deleteAll();
        roleRepository.deleteAll();
        cleanStorageDirectory();

        user = persistUser("test@example.com", "OWNER");
        admin = persistUser("admin@example.com", "ADMIN");

        vessel = new Vessel();
        vessel.setMmsi("123456789");
        vessel.setVesselName("Vessel 1");
        vessel.setBaseDateTime(Timestamp.valueOf(LocalDateTime.now()));
        vessel.setCreatedAt(Timestamp.valueOf(LocalDateTime.now()));
        vesselRepository.save(vessel);

        vesselOwner = new Vessel();
        vesselOwner.setMmsi("987654321");
        vesselOwner.setVesselName("Vessel 2");
        vesselOwner.setBaseDateTime(Timestamp.valueOf(LocalDateTime.now()));
        vesselOwner.setCreatedAt(Timestamp.valueOf(LocalDateTime.now()));
        vesselOwner.getUsers().add(user);
        vesselRepository.save(vesselOwner);

        file = new FileUpload();
        file.setStoredFilename("fileUpload");
        file.setOriginalFilename("fileUpload");
        file.setUser(user);
        file.setFileSize(10L);
        fileUploadRepository.save(file);
    }

    private User persistUser(String email, String roleName) {
        Role role = roleRepository.findByNameIgnoreCase(roleName)
                .orElseGet(() -> {
                    Role newRole = new Role();
                    newRole.setName(roleName);
                    return roleRepository.save(newRole);
                });

        User user = new User();
        user.setUsername(email);
        user.setEmail(email);
        user.setPasswordHash("secret");
        user.setRole(role);
        return userRepository.save(user);
    }

    private void authenticate(User user) {
        CustomUserDetails userDetails = new CustomUserDetails(user);
        SecurityContextHolder.getContext().setAuthentication(
                new UsernamePasswordAuthenticationToken(userDetails, null, userDetails.getAuthorities())
        );
    }

    @Test
    void CreateRequestPropertySuccessTest() throws Exception {
        authenticate(user);
        RequestPropertyRequest payload = new RequestPropertyRequest(vessel.getId(), file.getId());
        mockMvc.perform(post("/api/v1/request-property")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(payload)))
                .andExpect(status().is2xxSuccessful());
    }

    @Test
    void CreateRequestPropertyNotFoundTest() throws Exception {
        authenticate(user);
        RequestPropertyRequest payload = new RequestPropertyRequest(vessel.getId(), -1);
        mockMvc.perform(post("/api/v1/request-property")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(payload)))
                .andExpect(status().isNotFound());

        payload = new RequestPropertyRequest(-1, file.getId());
        mockMvc.perform(post("/api/v1/request-property")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(payload)))
                .andExpect(status().isNotFound());
    }

    @Test
    void CreateRequestPropertyUnauthorizedTest() throws Exception {
        RequestPropertyRequest payload = new RequestPropertyRequest(vessel.getId(), file.getId());
        mockMvc.perform(post("/api/v1/request-property")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(payload)))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void GetAllRequestPropertyReturnsAdminDto() throws Exception {
        authenticate(admin);
        RequestProperty rp = persistRequestProperty();

        mockMvc.perform(get("/api/v1/request-property"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content[0].id").value(rp.getId()))
                .andExpect(jsonPath("$.content[0].username").value(user.getUsername()))
                .andExpect(jsonPath("$.content[0].userEmail").value(user.getEmail()))
                .andExpect(jsonPath("$.content[0].mmsi").value(vessel.getMmsi()))
                .andExpect(jsonPath("$.content[0].fileName").value(file.getOriginalFilename()));
    }

    @Test
    void DeleteRequestPropertyRemovesEntryAndFile() throws Exception {
        authenticate(admin);
        RequestProperty rp = persistRequestProperty();

        mockMvc.perform(delete("/api/v1/request-property/{id}", rp.getId()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(rp.getId()))
                .andExpect(jsonPath("$.fileId").value(file.getId()));

        assertThat(requestPropertyRepository.existsById(rp.getId())).isFalse();
        assertThat(fileUploadRepository.existsById(file.getId())).isFalse();
    }

    private RequestProperty persistRequestProperty() {
        RequestProperty rp = new RequestProperty();
        rp.setUser(user);
        rp.setVessel(vessel);
        rp.setFile(file);
        rp.setCreatedAt(OffsetDateTime.now());
        return requestPropertyRepository.save(rp);
    }

    private void cleanStorageDirectory() throws Exception {
        Path root = Paths.get(uploadDir).toAbsolutePath().normalize();
        if (!Files.exists(root)) Files.createDirectories(root);

        try (var paths = Files.walk(root)) {
            paths.filter(path -> !path.equals(root))
                    .sorted(Comparator.reverseOrder())
                    .forEach(p -> { try { Files.deleteIfExists(p); } catch (Exception ignored) {} });
        }
    }
}

