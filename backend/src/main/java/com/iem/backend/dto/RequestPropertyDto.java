package com.iem.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotNull;

public record RequestPropertyDto(

        @NotNull(message = "User ID is required")
        @JsonProperty("userid")
        Integer userid,

        @NotNull(message = "MMSI is required")
        @JsonProperty("mmsi")
        String mmsi,

        @NotNull(message = "File ID is required")
        @JsonProperty("fileid")
        Integer fileid


)
{}
