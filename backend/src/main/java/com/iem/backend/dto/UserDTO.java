package com.iem.backend.dto;

import java.time.OffsetDateTime;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonView;

public record UserDTO (

    @JsonView({Views.Public.class, Views.Create.class, Views.Update.class, Views.Delete.class, Views.Admin.class})
    @JsonProperty("id")
    Integer id,

    @JsonView({Views.Public.class, Views.Create.class, Views.Update.class, Views.Delete.class, Views.Admin.class})
    @JsonProperty("username")
    String username,

    @JsonView({Views.Public.class, Views.Create.class, Views.Update.class, Views.Delete.class, Views.Admin.class})
    @JsonProperty("email")
    String email,

    @JsonView({Views.Public.class, Views.Create.class, Views.Update.class, Views.Delete.class, Views.Admin.class})
    @JsonProperty("role")
    String role,

    @JsonView({Views.Create.class, Views.Admin.class})
    @JsonProperty("created_at")
    OffsetDateTime createdAt,

    @JsonView({Views.Update.class, Views.Admin.class})
    @JsonProperty("last_update")
    OffsetDateTime lastUpdate,

    @JsonView({Views.Delete.class})
    @JsonProperty("deleted_at")
    OffsetDateTime deletedAt

) {  
}
