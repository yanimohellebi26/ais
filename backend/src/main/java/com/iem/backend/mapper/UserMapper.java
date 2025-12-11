package com.iem.backend.mapper;

import com.iem.backend.dto.user.UserPublicDetails;
import com.iem.backend.dto.user.UserResponse;
import com.iem.backend.entity.User;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

import java.util.List;

@Mapper(componentModel = "spring")
public interface UserMapper {

    @Mapping(source = "role.name", target = "role")
    UserResponse toResponse(User user);

    List<UserResponse> toResponseList(List<User> users);

    @Mapping(source = "role.name", target = "role")
    UserPublicDetails toPublicDetails(User user);

    List<UserPublicDetails> toPublicDetails(List<User> users);
}