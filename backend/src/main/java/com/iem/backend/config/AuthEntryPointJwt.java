package com.iem.backend.config;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.web.AuthenticationEntryPoint;
import org.springframework.stereotype.Component;
import java.io.IOException;

@Component
public class AuthEntryPointJwt implements AuthenticationEntryPoint {

    /**
     * Handles unauthorized access attempts by sending a 401 (Unauthorized) response.
     *
     * @param request the HTTP request that triggered the exception
     * @param response the HTTP response to send the error through
     * @param authException the exception indicating authentication failure
     * @throws IOException if an input or output error occurs while writing the response
     */
    @Override
    public void commence(
            HttpServletRequest request,
            HttpServletResponse response,
            AuthenticationException authException
    ) throws IOException {
        response.sendError(HttpServletResponse.SC_UNAUTHORIZED, "Error: Unauthorized");
    }
}