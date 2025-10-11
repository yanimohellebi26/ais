package com.iem.backend.config;

import com.iem.backend.service.UserService;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.security.config.annotation.authentication.configuration.AuthenticationConfiguration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;

@Configuration
@EnableMethodSecurity
public class AuthConfig {

    private final AuthEntryPointJwt unauthorizedHandler;
    private final JwtUtil jwtUtil;
    private final UserService userService;

    private static final String[] PUBLIC_ENDPOINTS = {
            "/api/v1/auth/**",
            "/swagger-ui/**",
            "/v3/api-docs/**"
    };

    public AuthConfig(AuthEntryPointJwt unauthorizedHandler,
                      JwtUtil jwtUtil,
                      UserService userService) {
        this.unauthorizedHandler = unauthorizedHandler;
        this.jwtUtil = jwtUtil;
        this.userService = userService;
    }

    /**
     * Provides the password encoder bean using BCrypt.
     *
     * @return a BCrypt-based password encoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * Provides the JWT authentication filter bean.
     *
     * @return an AuthTokenFilter instance
     */
    @Bean
    public AuthTokenFilter authenticationJwtTokenFilter(JwtUtil jwtUtils, UserService userDetailsService) {
        return new AuthTokenFilter(userService, jwtUtil);
    }

    /**
     * Provides the authentication manager bean used by Spring Security.
     *
     * @param authenticationConfiguration the authentication configuration
     * @return an authentication manager
     * @throws Exception if an error occurs during configuration
     */
    @Bean
    public AuthenticationManager authenticationManager(AuthenticationConfiguration authenticationConfiguration) throws Exception {
        return authenticationConfiguration.getAuthenticationManager();
    }

    /**
     * Configures the security filter chain, including permitted endpoints and JWT authentication.
     *
     * @param http the HTTP security configuration
     * @return the configured security filter chain
     * @throws Exception if an error occurs during setup
     */
    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
                .csrf(AbstractHttpConfigurer::disable)
                .exceptionHandling(ex -> ex.authenticationEntryPoint(unauthorizedHandler))
                .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .authorizeHttpRequests(auth -> auth
                        .requestMatchers(PUBLIC_ENDPOINTS).permitAll()
                        .requestMatchers("/actuator/health").permitAll()
                        .requestMatchers("/actuator/**").hasRole("ADMIN")
                        .anyRequest().authenticated()
                )
                .httpBasic(AbstractHttpConfigurer::disable)
                .formLogin(AbstractHttpConfigurer::disable);

        http.addFilterBefore(authenticationJwtTokenFilter(jwtUtil, userService),
                UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }
}
