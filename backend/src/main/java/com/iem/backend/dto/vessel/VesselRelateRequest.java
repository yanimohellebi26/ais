package com.iem.backend.dto.vessel;

import jakarta.validation.constraints.NotNull;

public record VesselRelateRequest(

    @NotNull
    Integer userId,

    @NotNull
    Integer vesselId
) {}

