package com.iem.backend.mapper;

import com.iem.backend.dto.fileUpload.FileUploadDetails;
import com.iem.backend.dto.fileUpload.FileUploadResponse;
import com.iem.backend.entity.FileUpload;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

@Mapper(componentModel = "spring")
public interface FileUploadMapper {

    @Mapping(target = "id", source = "fileUpload.id")
    @Mapping(target = "path", expression = "java(path)")
    @Mapping(target = "originalFilename", source = "fileUpload.originalFilename")
    @Mapping(target = "sizeBytes", source = "fileUpload.fileSize")
    FileUploadResponse toResponse(FileUpload fileUpload, String path);

    @Mapping(target = "userId", source = "fileUpload.user.id")
    FileUploadDetails toFileUploadDetails(FileUpload fileUpload);
}


