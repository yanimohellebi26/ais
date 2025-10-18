package com.iem.backend.controller;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.http.MediaType;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.iem.backend.dto.UpdateUserRequest;
import com.iem.backend.entity.Role;
import com.iem.backend.entity.User;
import com.iem.backend.repository.RoleRepository;
import com.iem.backend.repository.UserRepository;

import ch.qos.logback.core.encoder.EchoEncoder;

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
public class UserControllerTest {
    
    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private RoleRepository roleRepository;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private PasswordEncoder passwordEncoder;

    private Role adminRole;
    private Role ownerRole;
    private User existingUser;
    private User otherUser;

    @BeforeEach
    void setUp() {
        userRepository.deleteAll();
        roleRepository.deleteAll();

        adminRole = new Role();
        adminRole.setName("ADMIN");
        roleRepository.save(adminRole);

        ownerRole = new Role();
        ownerRole.setName("OWNER");
        roleRepository.save(ownerRole);

        existingUser = new User();
        existingUser.setUsername("testUser");
        existingUser.setEmail("test@example.com");
        existingUser.setPasswordHash(passwordEncoder.encode("oldPassword#123"));
        existingUser.setRole(ownerRole);
        userRepository.save(existingUser);

        otherUser = new User();
        otherUser.setUsername("adminUser");
        otherUser.setEmail("test2@example.com");
        otherUser.setPasswordHash(passwordEncoder.encode("oldPassword#123"));
        otherUser.setRole(adminRole);
        userRepository.save(otherUser);
    }

    // ============ UPDATE USER ============ //

    @Test
    @WithMockUser(username = "admin@test.fr", roles = {"ADMIN"})
    @DisplayName("should update user password successfully")
    void updateUserPasswordSuccess() throws Exception {
        UpdateUserRequest payload = new UpdateUserRequest(existingUser.getId(), "newPassword@456", null);

        mockMvc.perform(put("/api/v1/users")
            .contentType(MediaType.APPLICATION_JSON)
            .content(objectMapper.writeValueAsString(payload)))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.id").value(existingUser.getId()))
        .andExpect(jsonPath("$.email").value(existingUser.getEmail()));

        User updated = userRepository.findById(existingUser.getId()).orElseThrow();
        assertThat(passwordEncoder.matches("newPassword@456", updated.getPasswordHash())).isTrue();
    
    }

    @Test
    @WithMockUser(username = "admin@test.fr", roles = {"ADMIN"})
    @DisplayName("should update user role successfully")
    void updateUserRoleSuccess() throws Exception {
        UpdateUserRequest payload = new UpdateUserRequest(existingUser.getId(), null, "ADMIN");

        mockMvc.perform(put("/api/v1/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(payload)))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.id").value(existingUser.getId()))
        .andExpect(jsonPath("$.role").value("ADMIN"));

        User updated = userRepository.findById(existingUser.getId()).orElseThrow();
        assertThat(updated.getRole().getName()).isEqualTo("ADMIN");
    }

    @Test
    @WithMockUser(username = "admin@test.fr", roles = {"ADMIN"})
    @DisplayName("should update user passsword and role successfully")
    void updateUserRoleAndPasswordSuccess() throws Exception {
        UpdateUserRequest payload = new UpdateUserRequest(existingUser.getId(), "newPassword@456", "ADMIN");

        mockMvc.perform(put("/api/v1/users")
            .contentType(MediaType.APPLICATION_JSON)
            .content(objectMapper.writeValueAsString(payload)))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.id").value(existingUser.getId()))
        .andExpect(jsonPath("$.email").value(existingUser.getEmail()))
        .andExpect(jsonPath("$.role").value("ADMIN"));

        User updated = userRepository.findById(existingUser.getId()).orElseThrow();
        assertThat(passwordEncoder.matches("newPassword@456", updated.getPasswordHash())).isTrue();
        assertThat(updated.getRole().getName()).isEqualTo("ADMIN");
    }

    @Test
    @WithMockUser(username = "admin@test.fr", roles = {"ADMIN"})
    @DisplayName("should return not found for non-existing user")
    void updateUserNonExistingUser() throws Exception {
        UpdateUserRequest payload = new UpdateUserRequest(0, "newPassword@456", null);

        mockMvc.perform(put("/api/v1/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(payload)))
        .andExpect(status().isNotFound());
    }

    @Test
    @WithMockUser(username = "admin@test.fr", roles = {"ADMIN"})
    @DisplayName("should return not found for invalid role")
    void updateUserWithInvalidRole() throws Exception {
        UpdateUserRequest payload = new UpdateUserRequest(existingUser.getId(), null, "INVALID_ROLE");

        mockMvc.perform(put("/api/v1/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(payload)))
        .andExpect(status().isNotFound());
    }

    // ============ VISUALIZE USERS ============ //

    @Test
    @WithMockUser(username = "admin@test.fr", roles = {"ADMIN"})
    @DisplayName("should return all users with admin role")
    void getAllUsersByAdminSuccess() throws Exception {
        mockMvc.perform(get("/api/v1/users"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.length()").value(2))
            .andExpect(jsonPath("$[0].username").value("testUser"))
            .andExpect(jsonPath("$[1].username").value("adminUser"));
    }

    // ============ DELETE USERS ============ //

    @Test
    @WithMockUser(username = "admin@test.fr", roles = {"ADMIN"})
    @DisplayName("should delete user successfuly")
    void deleteUserByAdminSuccess() throws Exception {

        mockMvc.perform(delete("/api/v1/users/{id}", existingUser.getId()))
            .andExpect(status().isOk());

        assertThat(userRepository.findById(existingUser.getId())).isNotPresent();
    }

    @Test
    @WithMockUser(username = "admin@test.fr", roles = {"ADMIN"})
    @DisplayName("should return not found when deleting non-existing user")
    void deleteNonExistingUser() throws Exception {
        mockMvc.perform(delete("/api/v1/users/{id}", 9999))
                .andExpect(status().isNotFound());
    }
}
