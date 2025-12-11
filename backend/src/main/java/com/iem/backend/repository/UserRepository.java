package com.iem.backend.repository;

import org.springframework.data.jpa.repository.JpaRepository;

import com.iem.backend.entity.User;

import java.util.List;

public interface UserRepository extends JpaRepository<User, Integer> {
    boolean existsByEmailIgnoreCase(String email);

    boolean existsByUsernameIgnoreCase(String username);

    java.util.Optional<User> findByEmailIgnoreCase(String email);

    List<User> findByRole_Name(String role);
}
