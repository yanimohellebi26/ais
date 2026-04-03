package com.iem.backend.dto.analytics;

public record CountryPresenceDetails(
        String countryName,
        String alpha2,
        Long vesselCount
) {}
