package com.iem.backend.repository;

import org.springframework.data.jpa.repository.JpaRepository;

import com.iem.backend.entity.User;

public interface UserRepository extends JpaRepository<User, Integer> {
    
}
