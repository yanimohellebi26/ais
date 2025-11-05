package com.iem.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonView;
import com.iem.backend.entity.RequestProperty;

import java.time.OffsetDateTime;

public record RequestPropertyAdminDto(

        @JsonProperty("id")
        @JsonView({Views.Admin.class})
        Integer id,

        @JsonProperty("userid")
        @JsonView({Views.Admin.class})
        Integer userId,

        @JsonProperty("username")
        @JsonView({Views.Admin.class})
        String username,

        @JsonProperty("user_email")
        @JsonView({Views.Admin.class})
        String userEmail,

        @JsonProperty("user_role")
        @JsonView({Views.Admin.class})
        String userRole,

        @JsonProperty("mmsi")
        @JsonView({Views.Admin.class})
        String mmsi,

        @JsonProperty("fileid")
        @JsonView({Views.Admin.class})
        Integer fileId,

        @JsonProperty("file_name")
        @JsonView({Views.Admin.class})
        String fileName,

        @JsonProperty("created_at")
        @JsonView({Views.Admin.class})
        OffsetDateTime createdAt
)
{
    public static RequestPropertyAdminDto fromEntity(RequestProperty requestProperty) {
        return new RequestPropertyAdminDto(
                requestProperty.getId(),
                requestProperty.getUser().getId(),
                requestProperty.getUser().getUsername(),
                requestProperty.getUser().getEmail(),
                requestProperty.getUser().getRole().getName(),
                requestProperty.getVessel().getMmsi(),
                requestProperty.getFile().getId(),
                requestProperty.getFile().getOriginalFilename(),
                requestProperty.getCreatedAt()
        );
    }
}
