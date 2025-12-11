package com.iem.backend.repository;

import com.iem.backend.entity.Mid;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface MidRepository extends JpaRepository<Mid, Integer> {
}

