import  React,{ ChangeEvent, FormEvent, use, useEffect, useState } from "react";
import Input from "../../components/BaseComponents/Input";
import Button from "../../components/BaseComponents/Button";
import FormWrapper from "../../components/BaseComponents/FormWrapper";
import TitleH1 from "../../components/BaseComponents/TitleH1";
import TitleH2 from "../../components/BaseComponents/TitleH2";
import P from "../../components/BaseComponents/P";
import arrowLeft from "../../assets/arrow-left.svg";
import shipIcon from "../../assets/ship-icon.svg";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { useApi } from "../../utils/api";
import type { UserAccount } from "../../types";
import Breadcrumbs from "../../components/BaseComponents/Breadcrumbs";
import Card from "../../components/BaseComponents/Card";
import {Mail,CircleUserRound} from "lucide-react";
import Swal from "sweetalert2";


type newPass = {
    oldPassword:string,
    newPassword:string
};

const DashboardHome: React.FC = () => {
    const navigate = useNavigate();
      const { user } = useAuth();
      const api = useApi();
    
      const [userData, setUserData] = useState<UserAccount | null>(null);
      const [loading, setLoading] = useState(false);
      const [error, setError] = useState<string | null>(null);
    
      useEffect(() => { //hook
        const fetchUser = async () => {
          if (!user.id) return;
    
          setLoading(true);
          setError(null);
    
          try {
            const data = await api<UserAccount>(`/api/v1/users/${user.id}`);
            setUserData(data);
          } catch (err: any) {
            setError(err.message || "Error while retrieving your data");
          } finally {
            setLoading(false);
          }
        };
    
        fetchUser();
    }, [user.id]);

    const validPassword = (password: string) => {
        const regex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*]).{8,}$/;
        return regex.test(password);
    };

    const handleChangePassword = async() => {
        const {value: formValues} = await Swal.fire({
            title: "Change your password",
            html: `
            <style>
                .swal2-input { width: 100%; box-sizing: border-box; margin: 0.5rem 0; }
                .swal2-popup { overflow-x: hidden; }
                .password-rules {
                text-align: left;
                font-size: 13px;
                margin-top: 0.5rem;
                line-height: 1.4;
                }
                .rule {
                display: flex;
                align-items: center;
                gap: 6px;
                }
                .rule span {
                font-weight: 500;
                }
                .rule.valid { color: #16a34a; } /* vert ✓ */
                .rule.invalid { color: #dc2626; } /* rouge ✗ */
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
                    "Password must contain at least 8 characters, including uppercase, lowercase, number, and special character");
                    return false;
                }
                return { oldPassword, newPassword };
            },
        });
        if (formValues){
            try {
                await api<newPass>(`/api/v1/users/${user.id}/password`, {
                    method:"PUT",
                    body: JSON.stringify({
                        oldPassword: formValues.oldPassword,
                        newPassword: formValues.newPassword
                    }),
                    headers: {"Content-Type" : "application/json"},
                });

                Swal.fire({
                    icon:"success",
                    title:"Password updated !",
                    text: "Your password has been successfully changed",
                    confirmButtonColor:"#3085d6",
                });
            } catch (error:any) {
                Swal.fire({
                    icon: "error",
                    title: "Error",
                    text: error.message || "Failed to change password.",
                });
            }
        }
    }

    return (
        <div>
            <Breadcrumbs/>
            <TitleH1 className="text-2xl font-bold mb-4">Welcome in, {userData?.username}</TitleH1>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-3xl mx-auto p-4">
                
                
                <Card >
                    <figure className="w-full h-48">
                        <img
                        src="https://pixabay.com/get/gf6f5c141b2df09798efa44804cbe67f7a494bc4a9d977a07e4d89ffb74676cccd43bf738414df1962155d7a9fdbdc2b7.svg"
                        alt="decorative illustration"
                        className="w-full h-full object-cover"
                        />
                    </figure>

                    <div className="card-body">
                        <TitleH2 className="card-title ">
                        Personnal data
                        </TitleH2>
                            {loading && (
                            <p className="text-center text-gray-500">Loading...</p>
                        )}

                        {error && (
                            <p className="text-center text-red-600 font-medium">{error}</p>
                        )}
                        {userData && (
                            <div className="py-3 text-base">
                                <div className="flex items-center py-2 gap-2">
                                    <Mail className="w-4 h-4" />
                                    <span>{userData.email}</span>
                                </div>
                                <div className="flex items-center py-2 gap-2 ">
                                    <CircleUserRound className="w-4 h-4" />
                                    <span>{userData.username}</span>
                                </div>
                            </div>
                        )}
                        <div className="card-actions justify-end">
                            <Button onClick={handleChangePassword} className="btn btn-primary " >Change password</Button>
                        </div>
                    </div>
                    
                    
                </Card>
                <Card>
                    exemple
                </Card>
                
            </div>
        </div>
    );
};

export default DashboardHome;
