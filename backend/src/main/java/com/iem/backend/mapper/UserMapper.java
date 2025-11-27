package com.iem.backend.mapper;

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
}