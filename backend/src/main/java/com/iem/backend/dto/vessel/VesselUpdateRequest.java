package com.iem.backend.dto.vessel;

import com.iem.backend.entity.TransceiverClass;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.PositiveOrZero;
import jakarta.validation.constraints.Size;


public record VesselUpdateRequest (
    @Size(max = 20)
    String imo,

    @NotBlank
    @Size(max = 100)
    String vesselName,

    @Size(max = 20)
    String callSign,

    Integer vesselType,
    Integer cargoType,

    @PositiveOrZero
    Double length,

    @PositiveOrZero
    Double width,

    @PositiveOrZero
    Double draft,

    @NotNull
    TransceiverClass transceiverClass,

    Boolean locked
) {}
