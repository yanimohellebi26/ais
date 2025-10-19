import React, { ChangeEvent, FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { useApi } from "../../utils/api";
import { defaultEasing } from "framer-motion";
import FormWrapper from "../../components/BaseComponents/FormWrapper";
import Button from "../../components/BaseComponents/Button";
import { P } from "framer-motion/dist/types.d-BJcRxCew";
import TitleH2 from "../../components/BaseComponents/TitleH2";
import Input from "../../components/BaseComponents/Input";
import { UpdateUserRequest } from "../../types";
import { toast } from 'react-toastify';


type newPass = {
    oldPassword: string,
    newPassword: string
}

type userAcc = {
    id: number,
    username?: string,
    email?: string,
    password?: string,
    role?: string
}

const Password = () => {
    const [formData, setFormData] = useState<newPass>({ oldPassword: "", newPassword: "" });
    const navigate = useNavigate();
    const [error, setError] = useState<string | null>(null);
    //const [message, setMessage] = useState<string |null>(null);
    const api = useApi();
    const { user } = useAuth();

    const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
        setError(null);
    };

    const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> =>{
        event.preventDefault();
        setError(null);

        try {
            const data = await api<newPass>(`/api/v1/users/${user.id}/password`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(formData),

            });
            
            toast.success("Password updated succesfully")
            navigate("/dashboard");
                   
        } catch (err:any) {
            setError(err.message || "An error occured while updating the password")
            
        }
    };

    return (
        <div className="flex items-center justify-center w-full h-screen p-4 ">
            <FormWrapper>
                <TitleH2 className="text-2xl font-bold text-center mb-2">Change your password</TitleH2>
                
                

                <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                    <Input
                        label="Old Password"
                        type="password"
                        name="oldPassword"
                        value={formData.oldPassword}
                        placeholder="Enter your old password"
                        onChange={handleChange}
                    />
                    <Input
                        label="New Password"
                        type="password"
                        name="newPassword"
                        value={formData.newPassword}
                        placeholder="Enter your new password"
                        onChange={handleChange}
                    />
                    {error && <p className="text-red-600 text-sm text-center">{error}</p>}
                    <Button
                        type="submit"
                        className="w-full px-4 py-2 rounded-md bg-blue-600 text-white hover:bg-blue-700"
                    >
                        Change password
                    </Button>
                </form>
            </FormWrapper>
        </div>

    );
} ;

export default Password