package com.iem.backend.dto.vessel;

public record VesselFilter(
        String country,
        Integer mid,
        String mmsi,
        String name,
        Double minLength,
        Double maxLength,
        Double minDraft,
        Double maxDraft,
        String search
) {
}


