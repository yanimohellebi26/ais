package com.iem.backend.mapper;

import com.iem.backend.dto.requestProperty.RequestPropertyDetails;
import com.iem.backend.entity.RequestProperty;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

@Mapper(componentModel = "spring")
public interface RequestPropertyMapper {

    @Mapping(target = "userId", source = "user.id")
    @Mapping(target = "username", source = "user.username")
    @Mapping(target = "userEmail", source = "user.email")
    @Mapping(target = "userRole", source = "user.role.name")
    @Mapping(target = "fileId", source = "file.id")
    @Mapping(target = "fileName", source = "file.originalFilename")
    @Mapping(target = "mmsi", source = "vessel.mmsi")
    RequestPropertyDetails toDetails(RequestProperty entity);
}

