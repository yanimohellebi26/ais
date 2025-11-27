
package com.iem.backend.dto.user;

import jakarta.validation.constraints.NotBlank;

public record UpdateUserPasswordRequest(

    @NotBlank
    String oldPassword,

    @NotBlank
    String newPassword

) {}