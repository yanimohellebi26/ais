import Swal from "sweetalert2";
import { useApi } from "../utils/api"; 
import React from "react";

const validPassword = (password: string) => {
  return (
    password.length >= 8 &&
    /[A-Z]/.test(password) &&
    /[a-z]/.test(password) &&
    /\d/.test(password) &&
    /[!@#$%^&*]/.test(password)
  );
};

type newPass = {
    oldPassword:string,
    newPassword:string
};



export const useChangePassword = (userId?: number | null) => {
    const api = useApi();
    const handleChangePassword = async () => {
        const { value: formValues } = await Swal.fire({
        title: "Change your password",
        html: `
            <style>
            .swal2-input { width: 100%; box-sizing: border-box; margin: 0.5rem 0; }
            .swal2-popup { overflow-x: hidden; }
            .password-rules { text-align: left; font-size: 13px; margin-top: 0.5rem; line-height: 1.4; }
            .rule { display: flex; align-items: center; gap: 6px; }
            .rule span { font-weight: 500; }
            .rule.valid { color: #16a34a; }
            .rule.invalid { color: #dc2626; }
            </style>

            <input id="oldPassword" type="password" class="swal2-input" placeholder="Old password">
            <input id="newPassword" type="password" class="swal2-input" placeholder="New password">

            <div class="password-rules">
            <div id="rule-length" class="rule invalid">✗ At least 8 characters</div>
            <div id="rule-upper" class="rule invalid">✗ One uppercase letter</div>
            <div id="rule-lower" class="rule invalid">✗ One lowercase letter</div>
            <div id="rule-number" class="rule invalid">✗ One number</div>
            <div id="rule-special" class="rule invalid">✗ One special character (!@#$%^&*)</div>
            </div>
        `,
        confirmButtonText: "Update password",
        showCancelButton: true,
        focusConfirm: false,
        didOpen: () => {
            const newPasswordInput = document.getElementById("newPassword") as HTMLInputElement;
            newPasswordInput.addEventListener("input", () => {
            const val = newPasswordInput.value;
            const updateRule = (id: string, valid: boolean) => {
                const el = document.getElementById(id);
                if (!el) return;
                el.classList.toggle("valid", valid);
                el.classList.toggle("invalid", !valid);
                el.textContent = valid
                ? "✓ " + el.textContent?.replace(/^✗|✓/, "").trim()
                : "✗ " + el.textContent?.replace(/^✗|✓/, "").trim();
            };

            updateRule("rule-length", val.length >= 8);
            updateRule("rule-upper", /[A-Z]/.test(val));
            updateRule("rule-lower", /[a-z]/.test(val));
            updateRule("rule-number", /\d/.test(val));
            updateRule("rule-special", /[!@#$%^&*]/.test(val));
            });
        },
        preConfirm: () => {
            const oldPassword = (document.getElementById("oldPassword") as HTMLInputElement)?.value;
            const newPassword = (document.getElementById("newPassword") as HTMLInputElement)?.value;

            if (!oldPassword || !newPassword) {
            Swal.showValidationMessage("Both fields are required");
            return false;
            }
            if (!validPassword(newPassword)) {
            Swal.showValidationMessage(
                "Password must contain at least 8 characters, including uppercase, lowercase, number, and special character"
            );
            return false;
            }
            return { oldPassword, newPassword };
        },
        });

        if (formValues) {
        try {
            await api<newPass>(`/api/v1/users/${userId}/password`, {
            method: "PUT",
            body: JSON.stringify({
                oldPassword: formValues.oldPassword,
                newPassword: formValues.newPassword,
            }),
            headers: { "Content-Type": "application/json" },
            });

            Swal.fire({
            icon: "success",
            title: "Password updated!",
            text: "Your password has been successfully changed",
            confirmButtonColor: "#3085d6",
            });
        } catch (error: any) {
            Swal.fire({
            icon: "error",
            title: "Error",
            text: error.message || "Failed to change password.",
            });
        }
        }
    };

    return { handleChangePassword };
};