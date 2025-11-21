package com.iem.backend.mapper;

import com.iem.backend.dto.vessel.VesselCreateRequest;
import com.iem.backend.dto.vessel.VesselDetails;
import com.iem.backend.dto.vessel.VesselUpdateRequest;

import com.iem.backend.entity.Vessel;
import org.mapstruct.*;

import java.util.List;

@Mapper(
        componentModel = "spring",
        uses = {VesselMapperHelper.class}
)
public interface VesselMapper {

    // entity -> details dto
    @Mapping(target = "vesselType", source = "vessel.vesselType.id")
    @Mapping(target = "vesselTypeName", source = "vessel.vesselType.description")
    @Mapping(target = "cargoType", source = "vessel.cargoType.id")
    @Mapping(target = "cargoTypeName", source = "vessel.cargoType.description")
    @Mapping(target = "country", expression = "java(vessel.getCountryName())")
    VesselDetails toDetails(Vessel vessel);

    List<VesselDetails> toDetails(List<Vessel> vessels);

    // create dto -> entity
    @Mapping(target = "vesselType", source = "vesselType", qualifiedByName = "resolveVesselType")
    @Mapping(target = "cargoType", source = "cargoType", qualifiedByName = "resolveCargoType")
    @Mapping(target = "id", ignore = true)
    @Mapping(target = "mid", ignore = true)
    @Mapping(target = "users", ignore = true)
    @Mapping(target = "createdAt", ignore = true)
    @Mapping(target = "lastUpdate", ignore = true)
    Vessel fromCreateRequest(VesselCreateRequest dto);

    @BeanMapping(nullValuePropertyMappingStrategy = NullValuePropertyMappingStrategy.IGNORE)
    @Mapping(target = "vesselType", source = "vesselType", qualifiedByName = "resolveVesselType")
    @Mapping(target = "cargoType", source = "cargoType", qualifiedByName = "resolveCargoType")
    @Mapping(target = "id", ignore = true)
    @Mapping(target = "mid", ignore = true)
    @Mapping(target = "users", ignore = true)
    @Mapping(target = "createdAt", ignore = true)
    @Mapping(target = "baseDateTime", ignore = true)
    @Mapping(target = "lastUpdate", ignore = true)
    void updateEntityFromRequest(VesselUpdateRequest dto, @MappingTarget Vessel vessel);
}
