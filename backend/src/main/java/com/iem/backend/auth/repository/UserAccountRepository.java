package com.iem.backend.auth.repository;

import com.iem.backend.auth.entity.UserAccount;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UserAccountRepository extends JpaRepository<UserAccount, Long> {

    boolean existsByEmailIgnoreCase(String email);

    boolean existsByUsernameIgnoreCase(String username);

    java.util.Optional<UserAccount> findByEmailIgnoreCase(String email);
}
