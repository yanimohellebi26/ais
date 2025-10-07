package com.iem.backend.repository;

import com.iem.backend.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UserAccountRepository extends JpaRepository<User, Long> {

    boolean existsByEmailIgnoreCase(String email);

    boolean existsByUsernameIgnoreCase(String username);

    java.util.Optional<User> findByEmailIgnoreCase(String email);
}
