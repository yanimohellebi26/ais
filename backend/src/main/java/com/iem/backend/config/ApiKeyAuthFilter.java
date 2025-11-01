package com.iem.backend.config;

import com.iem.backend.service.UserService;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Profile;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.Map;

@Slf4j
@Component
@Profile({"dev","local"})
public class ApiKeyAuthFilter extends OncePerRequestFilter {

    private final UserService userService;
    private final DevApiKeyInitializer devApiKeyInitializer;

    public ApiKeyAuthFilter(UserService userService, DevApiKeyInitializer devApiKeyInitializer) {
        this.userService = userService;
        this.devApiKeyInitializer = devApiKeyInitializer;
    }

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain
    ) throws ServletException, IOException {

        String apiKey = request.getHeader("X-API-KEY");
        Map<String, String> apiKeyMap = devApiKeyInitializer.getApiKeyToEmailMap();

        try {
            if (apiKey != null && apiKeyMap.containsKey(apiKey)) {
                String email = apiKeyMap.get(apiKey);
                var userDetails = userService.loadUserByUsername(email);

                var authentication = new UsernamePasswordAuthenticationToken(
                        userDetails,
                        null,
                        userDetails.getAuthorities()
                );

                authentication.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
                SecurityContextHolder.getContext().setAuthentication(authentication);
                log.debug("Authenticated via API key as {}", email);
            }
        } catch (Exception e) {
            log.error("API Key filter error: ", e);
        }

        filterChain.doFilter(request, response);
    }
}
