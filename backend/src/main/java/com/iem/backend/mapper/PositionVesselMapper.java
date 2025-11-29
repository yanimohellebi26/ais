package com.iem.backend.mapper;

import com.iem.backend.dto.positionVessel.PositionVesselProperties;
import com.iem.backend.dto.positionVessel.PositionVesselRadiusProperties;
import com.iem.backend.entity.PositionVessel;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

@Mapper(componentModel = "spring")
public interface PositionVesselMapper {

    @Mapping(target = "status", source = "status.description")
    @Mapping(target = "mmsi", source="vessel.mmsi")
    @Mapping(target = "vesselId", source = "vessel.id")
    PositionVesselProperties toProperties(PositionVessel positionVessel);

    @Mapping(target = "id", source = "id")
    @Mapping(target = "status", source = "status.description")
    @Mapping(target = "mmsi", source="vessel.mmsi")
    @Mapping(target = "distanceKm", ignore = true)
    PositionVesselRadiusProperties toRadiusProperties(PositionVessel positionVessel);
}

