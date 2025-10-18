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


const Account = () => {
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
        console.log(user.token);
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


    
    return (
        <div className="min-h-screen bg-gray-100 py-10 flex flex-col items-center">
        <div className="flex justify-center w-full max-w-md mb-4 text-center">
            <Button
            onClick={() => navigate("/dashboard/")}
            className="flex gap-2 items-center bg-transparent hover:bg-gray-300 text-gray-600"
            >
            <img src={arrowLeft} alt="Back" className="w-4 h-4" />
            Back to Home
            </Button>
        </div>

        <div className="w-full max-w-md flex justify-center gap-4 items-center pb-5">
            <img src={shipIcon} alt="Ship Icon" className="w-8 h-8" />
            <TitleH1>SeaSight</TitleH1>
        </div>

        <FormWrapper>
            <TitleH2 className="mb-2 text-center text-black font-bold">Your Account</TitleH2>
            <P className="mb-4 text-center">View your account information</P>

            {loading && <P>Loading...</P>}
            {error && <P className="text-red-600">{error}</P>}

            {userData && (
            <div className="flex flex-col gap-4">
                <div className="p-4 bg-gray-50 rounded-md shadow-sm">
                <p className="font-bold">Name:</p>
                <p>{userData.username}</p>
                </div>
                <div className="p-4 bg-gray-50 rounded-md shadow-sm">
                <p className="font-bold">Email:</p>
                <p>{userData.email}</p>
                </div>
            </div>
            )}
        </FormWrapper>
        </div>
    );
};
export default Account;
