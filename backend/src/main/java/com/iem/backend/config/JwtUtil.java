package com.iem.backend.config;

import com.iem.backend.utils.ApiLogger;
import io.jsonwebtoken.*;
import io.jsonwebtoken.security.Keys;
import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.PropertySource;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Date;
@PropertySource({"classpath:application-docker.properties","classpath:application.properties"})
@Component
public class JwtUtil {

    private final ApiLogger apiLogger;
    @Value("${jwt.secret}")
    private String jwtSecret;

    @Value("${jwt.expiration}")
    private int jwtExpirationMs;

    private SecretKey key;

    public JwtUtil(ApiLogger apiLogger) {
        this.apiLogger = apiLogger;
    }

    /**
     * Initializes the key
     */
    @PostConstruct
    public void init() {
        this.key = Keys.hmacShaKeyFor(jwtSecret.getBytes(StandardCharsets.UTF_8));
    }

    /**
     * Generate JWT token
     *
     * @param email To generate Token from user's email
     * @return Token
     */
    public String generateToken(String email) {
        return Jwts.builder()
                .setSubject(email)
                .setIssuedAt(new Date())
                .setExpiration(new Date((new Date()).getTime() + jwtExpirationMs))
                .signWith(key, SignatureAlgorithm.HS256)
                .compact();
    }

    /**
     * Get email from JWT token
     *
     * @param token To connect
     * @return user's email
     */
    public String getEmailFromToken(String token) {
        return Jwts.parserBuilder()
                .setSigningKey(key).build()
                .parseClaimsJws(token)
                .getBody()
                .getSubject();
    }

    /**
     * Validate JWT token
     *
     * @param token
     * @return True if Token is valid, false else
     */
    public boolean validateJwtToken(String token) {
        try {
            Jwts.parserBuilder().setSigningKey(key).build().parseClaimsJws(token);
            return true;
        } catch (SecurityException e) {
            apiLogger.error("Invalid JWT signature: ", e);
        } catch (MalformedJwtException e) {
            apiLogger.error("Invalid JWT token: ", e);
        } catch (ExpiredJwtException e) {
            apiLogger.error("JWT token is expired: ", e);
        } catch (UnsupportedJwtException e) {
            apiLogger.error("JWT token is unsupported: ", e);
        } catch (IllegalArgumentException e) {
            apiLogger.error("JWT claims string is empty: ", e);
        }
        return false;
    }
}