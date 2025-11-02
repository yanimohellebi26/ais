package com.iem.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonView;
import com.iem.backend.entity.RequestProperty;
import jakarta.validation.constraints.NotNull;

import java.time.OffsetDateTime;

public record RequestPropertyDto(

        @JsonProperty("id")
        @JsonView({Views.Public.class, Views.Update.class, Views.Delete.class, Views.Admin.class})
        Integer id,

        @NotNull(message = "User ID is required")
        @JsonView({Views.Public.class, Views.Create.class, Views.Update.class, Views.Delete.class, Views.Admin.class})
        @JsonProperty("userid")
        Integer userid,

        @NotNull(message = "MMSI is required")
        @JsonView({Views.Public.class, Views.Create.class, Views.Update.class, Views.Delete.class, Views.Admin.class})
        @JsonProperty("mmsi")
        String mmsi,

        @NotNull(message = "File ID is required")
        @JsonView({Views.Public.class, Views.Create.class, Views.Update.class, Views.Delete.class, Views.Admin.class})
        @JsonProperty("fileid")
        Integer fileid,

        @JsonProperty("created_at")
        @JsonView({Views.Delete.class, Views.Admin.class})
        OffsetDateTime createdAt
)
{
    public static RequestPropertyDto fromEntity(RequestProperty r) {
        return new RequestPropertyDto(
                r.getId(),
                r.getUser().getId(),
                r.getVessel().getMmsi(),
                r.getFile().getId(),
                r.getCreatedAt()
        );
    }
}
