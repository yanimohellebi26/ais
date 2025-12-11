package com.iem.backend.dto.requestProperty;

import jakarta.validation.constraints.NotNull;

public record RequestPropertyRequest (
        @NotNull
        Integer vesselId,

        @NotNull
        Integer fileId
) {}
