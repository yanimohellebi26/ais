package com.iem.backend.repository;

import com.iem.backend.entity.FileUpload;
import org.springframework.data.jpa.repository.JpaRepository;

public interface FileUploadRepository extends JpaRepository<FileUpload, Integer> {
    int countByUser_Id(Integer userId);
}
