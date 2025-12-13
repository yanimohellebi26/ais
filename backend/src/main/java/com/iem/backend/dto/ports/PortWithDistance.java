package com.iem.backend.dto.ports;

public record PortWithDistance(
        Integer portId,
        String name,
        String code,
        String country,
        Double distance
) {
}
