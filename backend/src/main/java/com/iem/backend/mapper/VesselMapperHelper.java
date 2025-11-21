package com.iem.backend.mapper;

import com.iem.backend.entity.VesselType;
import com.iem.backend.repository.VesselTypeRepository;
import org.mapstruct.Named;
import org.springframework.stereotype.Component;

@Component
public class VesselMapperHelper {

    private final VesselTypeRepository vesselTypeRepository;

    public VesselMapperHelper(VesselTypeRepository vesselTypeRepository) {
        this.vesselTypeRepository = vesselTypeRepository;
    }

    @Named("resolveVesselType")
    public VesselType resolveVesselType(Integer id) {
        return id == null ? null : vesselTypeRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Invalid vesselType id: " + id));
    }

    @Named("resolveCargoType")
    public VesselType resolveCargoType(Integer id) {
        return id == null ? null : vesselTypeRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Invalid cargoType id: " + id));
    }
}
