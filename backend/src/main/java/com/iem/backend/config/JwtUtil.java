package com.iem.backend.config;

import com.iem.backend.entity.Role;
import com.iem.backend.utils.ApiLogger;
import io.jsonwebtoken.*;
import io.jsonwebtoken.security.Keys;
import jakarta.annotation.PostConstruct;
import lombok.extern.slf4j.Slf4j;
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
@Slf4j
public class JwtUtil {

    @Value("${jwt.secret}")
    private String jwtSecret;

    @Value("${jwt.expiration}")
    private long jwtExpirationMs;

    private SecretKey key;

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
    public String generateToken(String email, String roleName) {
        return Jwts.builder()
                .setSubject(email)
                .claim("role", "ROLE_" + roleName) // simple et clair
                .setIssuedAt(new Date())
                .setExpiration(new Date(System.currentTimeMillis() + jwtExpirationMs))
                .signWith(key, SignatureAlgorithm.HS256)
                .compact();
    }

    /**s
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
            log.error("Invalid JWT signature: ", e);
        } catch (MalformedJwtException e) {
            log.error("Invalid JWT token: ", e);
        } catch (ExpiredJwtException e) {
            log.error("JWT token is expired: ", e);
        } catch (UnsupportedJwtException e) {
            log.error("JWT token is unsupported: ", e);
        } catch (IllegalArgumentException e) {
            log.error("JWT claims string is empty: ", e);
        }
        return false;
    }
}