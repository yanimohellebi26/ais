import Swal from "sweetalert2";
import { useApi } from "../../hooks/useApi";
import React from "react";
import {toast} from "react-toastify";
import {useLoading} from "../../context/LoadingContext";

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
    const {setLoading} = useLoading();

    const handleChangePassword = async () => {
        const { value: formValues } = await Swal.fire({
        title: "Change your password",
        html: `
            <input id="oldPassword" type="password" class="input input-bordered w-full text-base-content mb-2" placeholder="Old password">
            <input id="newPassword" type="password" class="input input-bordered w-full text-base-content" placeholder="New password">

            <div class="password-rules flex flex-col items-start">
                <span id="rule-length" class="rule invalid text-error">✗ At least 8 characters</span>
                <span id="rule-upper" class="rule invalid text-error">✗ One uppercase letter</span>
                <span id="rule-lower" class="rule invalid text-error">✗ One lowercase letter</span>
                <span id="rule-number" class="rule invalid text-error">✗ One number</span>
                <span id="rule-special" class="rule invalid text-error">✗ One special character (!@#$%^&*)</span>
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
                el.classList.toggle("text-success", valid);
                el.classList.toggle("text-error", !valid);
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
                setLoading(true);
                await api<newPass>(`/api/v1/users/${userId}/password`, {
                method: "PUT",
                body: JSON.stringify({
                    oldPassword: formValues.oldPassword,
                    newPassword: formValues.newPassword,
                }),
                headers: { "Content-Type": "application/json" },
                });
                toast.success("Your password has been successfully changed");
            } catch (error: any) {
                toast.error(error.message || "Failed to change password.");
            } finally {
                setLoading(false);
            }
        }
    };

    return { handleChangePassword };
};