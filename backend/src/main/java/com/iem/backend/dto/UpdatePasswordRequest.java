
package com.iem.backend.dto;

import jakarta.validation.constraints.NotBlank;

public record UpdatePasswordRequest(

    @NotBlank(message = "Old password is required")
    String oldPassword,

    @NotBlank(message = "New password is required")
    String newPassword

) {}