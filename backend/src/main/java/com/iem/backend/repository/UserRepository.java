package com.iem.backend.repository;

import org.springframework.data.jpa.repository.JpaRepository;

import com.iem.backend.model.User;

public interface UserRepository extends JpaRepository<User, Long> {
    
}
