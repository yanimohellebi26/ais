package com.iem.backend.mapper;

import com.iem.backend.dto.ports.PortProperties;
import com.iem.backend.entity.Port;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

@Mapper(componentModel = "spring")
public interface PortMapper {

    @Mapping(target = "portId", source = "id")
    PortProperties toProperties(Port port);
}

