package com.iem.backend.config;

import com.iem.backend.entity.Role;
import com.iem.backend.entity.User;
import com.iem.backend.repository.RoleRepository;
import com.iem.backend.repository.UserRepository;
import jakarta.annotation.PostConstruct;
import lombok.Getter;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Profile;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@Component
@Profile({"dev","local"})
@RequiredArgsConstructor
public class DevApiKeyInitializer {

    private final RoleRepository roleRepository;
    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    @Getter
    private final Map<String, String> apiKeyToEmailMap = new HashMap<>();

    @PostConstruct
    public void init() {
        List<Role> roles = roleRepository.findAll();
        if (roles.isEmpty()) {
            return;
        }

        roles.forEach((role) -> {
            String roleName = role.getName().replace("ROLE_", "").toLowerCase();
            String email = "dev_" + roleName + "@sea.com";

            // create user if missing
            if (userRepository.findByEmailIgnoreCase(email).isEmpty()) {
                User user = new User();
                user.setUsername(email.split("@")[0]);
                user.setEmail(email);
                user.setPasswordHash(passwordEncoder.encode("Sea@1234"));
                user.setRole(role);
                userRepository.save(user);
            }

            String apiKey = "apikey_"+roleName;

            apiKeyToEmailMap.put(apiKey, email);
        });
        log.info("Api key generated for all dev users");

    }

}
