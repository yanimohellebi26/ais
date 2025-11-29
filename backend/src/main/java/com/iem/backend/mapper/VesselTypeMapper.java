package com.iem.backend.mapper;

import com.iem.backend.dto.vesselType.VesselTypeDetails;
import com.iem.backend.entity.VesselType;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

import java.util.List;

@Mapper(componentModel = "spring")
public interface VesselTypeMapper {

    @Mapping(target = "code", source = "id")
    VesselTypeDetails toDetails(VesselType vesselType);

    List<VesselTypeDetails> toDetails(List<VesselType> vesselTypes);
}
