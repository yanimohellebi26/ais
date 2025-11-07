package com.iem.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonView;
import com.iem.backend.entity.FileUpload;

import java.time.OffsetDateTime;

public record FileUploadDetailsDto(

        @JsonProperty("id")
        @JsonView({Views.Admin.class})
        Integer id,

        @JsonProperty("user_id")
        @JsonView({Views.Admin.class})
        Integer userId,

        @JsonProperty("original_filename")
        @JsonView({Views.Admin.class})
        String originalFilename,

        @JsonProperty("file_size")
        @JsonView({Views.Admin.class})
        long sizeBytes,

        @JsonProperty("uploaded_at")
        @JsonView({Views.Admin.class})
        OffsetDateTime uploadedAt
)
{
    public static FileUploadDetailsDto fromEntity(FileUpload upload) {
        return new FileUploadDetailsDto(
                upload.getId(),
                upload.getUser().getId(),
                upload.getOriginalFilename(),
                upload.getFileSize(),
                upload.getUploadedAt()
        );
    }
}
