package com.iem.backend.auth.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.iem.backend.entity.Role;
import com.iem.backend.entity.User;
import com.iem.backend.repository.RoleRepository;
import com.iem.backend.repository.UserAccountRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.servlet.MockMvc;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
@TestPropertySource(properties = {
        "spring.datasource.url=jdbc:h2:mem:authdb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
        "spring.datasource.username=sa",
        "spring.datasource.password=",
        "spring.jpa.hibernate.ddl-auto=create-drop",
        "spring.jpa.show-sql=false"
})
class AuthControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private RoleRepository roleRepository;

    @Autowired
    private UserAccountRepository userAccountRepository;

    @Autowired
    private PasswordEncoder passwordEncoder;

    @BeforeEach
    void setUp() {
        userAccountRepository.deleteAll();
        roleRepository.deleteAll();
        Role admin = new Role();
        admin.setName("admin");
        roleRepository.save(admin);
    }

    @Test
    @DisplayName("should register user successfully")
    void register_successful() throws Exception {
        String payload = objectMapper.writeValueAsString(new RegisterPayload(
                "captain_john",
                "john.doe@example.com",
                "StrongPass1!",
                "admin"
        ));

        mockMvc.perform(post("/api/v1/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(payload))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id").isNumber())
                .andExpect(jsonPath("$.username").value("captain_john"))
                .andExpect(jsonPath("$.email").value("john.doe@example.com"))
                .andExpect(jsonPath("$.role").value("admin"));

        User saved = userAccountRepository.findByEmailIgnoreCase("john.doe@example.com").orElseThrow();
        assertThat(saved.getPasswordHash()).isNotEqualTo("StrongPass1!");
        assertThat(passwordEncoder.matches("StrongPass1!", saved.getPasswordHash())).isTrue();
    }

    @Test
    @DisplayName("should reject duplicate email")
    void register_conflict_email() throws Exception {
        Role adminRole = roleRepository.findByNameIgnoreCase("admin").orElseThrow();
        User existing = new User();
        existing.setUsername("existingUser");
        existing.setEmail("john.doe@example.com");
        existing.setPasswordHash(passwordEncoder.encode("StrongPass1!"));
        existing.setRole(adminRole);
        userAccountRepository.save(existing);

        String payload = objectMapper.writeValueAsString(new RegisterPayload(
                "anotherUser",
                "john.doe@example.com",
                "StrongPass1!",
                "admin"
        ));

        mockMvc.perform(post("/api/v1/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(payload))
                .andExpect(status().isConflict());
    }

    @Test
    @DisplayName("should validate password policy")
    void register_invalid_password() throws Exception {
        String payload = objectMapper.writeValueAsString(new RegisterPayload(
                "captain_john",
                "captain.john@example.com",
                "weakpass",
                "admin"
        ));

        mockMvc.perform(post("/api/v1/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(payload))
                .andExpect(status().isBadRequest());
    }

    private record RegisterPayload(String username, String email, String password, String role) {
    }
}
