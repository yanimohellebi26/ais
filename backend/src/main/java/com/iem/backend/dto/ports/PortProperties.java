package com.iem.backend.dto.ports;

public record PortProperties(
        Integer portId,
        String name,
        String code,
        String country
) {}

