package com.iem.backend.mapper;

import com.iem.backend.dto.country.CountryMidDetails;
import com.iem.backend.entity.Mid;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

import java.util.List;

@Mapper(componentModel = "spring")
public interface CountryMapper {

    @Mapping(target = "name", source = "country.name")
    @Mapping(target = "alpha2", source = "country.alpha2")
    @Mapping(target = "alpha3", source = "country.alpha3")
    @Mapping(target = "mid", source = "mid")
    CountryMidDetails toMidDetails(Mid mid);

    List<CountryMidDetails> toMidDetails(List<Mid> mids);
}

