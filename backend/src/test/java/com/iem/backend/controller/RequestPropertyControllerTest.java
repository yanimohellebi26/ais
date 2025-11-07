package com.iem.backend.controller;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.iem.backend.dto.RequestPropertyDto;
import com.iem.backend.entity.FileUpload;
import com.iem.backend.entity.RequestProperty;
import com.iem.backend.entity.Vessel;
import com.iem.backend.repository.FileUploadRepository;
import com.iem.backend.repository.RequestPropertyRepository;
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
import java.time.OffsetDateTime;
import java.util.Comparator;

import static org.assertj.core.api.Assertions.assertThat;

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
    private RequestPropertyRepository requestPropertyRepository;

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
    requestPropertyRepository.deleteAll();
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
        RequestPropertyDto payload = new RequestPropertyDto(1,user.getId(),vessel.getMmsi(),file.getId(),null);
        mockMvc.perform(post("/api/v1/request-property")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(payload)))
                .andExpect(status().isOk());
    }

    @Test
    @WithMockUser(username = "test@example.com", roles = "USER")
    void CreateRequestPropertyNotFoundTest() throws Exception {
        RequestPropertyDto payload = new RequestPropertyDto(1,user.getId(),vessel.getMmsi(),-1,null);
        mockMvc.perform(post("/api/v1/request-property")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(payload)))
                .andExpect(status().isNotFound());
        payload = new RequestPropertyDto(1,user.getId(),"mmsifaux",file.getId(),null);
        mockMvc.perform(post("/api/v1/request-property")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(payload)))
                .andExpect(status().isNotFound());
        payload = new RequestPropertyDto(1,-1,vessel.getMmsi(),file.getId(),null);
        mockMvc.perform(post("/api/v1/request-property")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(payload)))
                .andExpect(status().isNotFound());
    }

    @Test
    void CreateRequestPropertyUnauthorizedTest() throws Exception {
        RequestPropertyDto payload = new RequestPropertyDto(1,user.getId(),vessel.getMmsi(),file.getId(),null);
        mockMvc.perform(post("/api/v1/request-property")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(payload)))
                .andExpect(status().isUnauthorized());
    }

    @Test
    @WithMockUser(username = "test@example.com", roles = "OWNER")
    void CreateRequestPropertyOwnerTest() throws Exception {
        RequestPropertyDto payload = new RequestPropertyDto(1,user.getId(),vesselOwner.getMmsi(),file.getId(),null);
        mockMvc.perform(post("/api/v1/request-property")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(payload)))
                .andExpect(status().isBadRequest());
    }

    @Test
    @WithMockUser(username = "admin@example.com", roles = "ADMIN")
    void GetAllRequestPropertyReturnsAdminDto() throws Exception {
        RequestProperty requestProperty = persistRequestProperty();

        mockMvc.perform(get("/api/v1/request-property"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content[0].id").value(requestProperty.getId()))
                .andExpect(jsonPath("$.content[0].username").value(user.getUsername()))
                .andExpect(jsonPath("$.content[0].user_email").value(user.getEmail()))
                .andExpect(jsonPath("$.content[0].mmsi").value(vessel.getMmsi()))
                .andExpect(jsonPath("$.content[0].file_name").value(file.getOriginalFilename()));
    }

    @Test
    @WithMockUser(username = "admin@example.com", roles = "ADMIN")
    void DeleteRequestPropertyRemovesEntryAndFile() throws Exception {
        RequestProperty requestProperty = persistRequestProperty();

        mockMvc.perform(delete("/api/v1/request-property/{id}", requestProperty.getId()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(requestProperty.getId()))
                .andExpect(jsonPath("$.fileid").value(file.getId()));

        assertThat(requestPropertyRepository.existsById(requestProperty.getId())).isFalse();
        assertThat(fileUploadRepository.existsById(file.getId())).isFalse();
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

    private RequestProperty persistRequestProperty() {
        RequestProperty requestProperty = new RequestProperty();
        requestProperty.setUser(user);
        requestProperty.setVessel(vessel);
        requestProperty.setFile(file);
        requestProperty.setCreatedAt(OffsetDateTime.now());
        return requestPropertyRepository.save(requestProperty);
    }
}
