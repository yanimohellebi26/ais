import React, { ChangeEvent, FormEvent, useEffect, useState } from "react";
import Input from "../components/BaseComponents/Input";
import Button from "../components/BaseComponents/Button";
import FormWrapper from "../components/BaseComponents/FormWrapper";
import TitleH1 from "../components/BaseComponents/TitleH1";
import TitleH2 from "../components/BaseComponents/TitleH2";
import P from "../components/BaseComponents/P";
import arrowLeft from "../assets/arrow-left.svg";
import shipIcon from "../assets/ship-icon.svg";
import { useNavigate } from "react-router-dom";
import {useAuth} from "../context/AuthContext"
import {useApi} from "../utils/api";
import { toast } from 'react-toastify';

type LoginForm = {
  email: string;
  password: string;
};

type LoginResponse = {
  token?: string;
  message?: string;
};

const Login = () => {
  const [formData, setFormData] = useState<LoginForm>({ email: "", password: "" });
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const { login, user } = useAuth();
  const api = useApi();

  useEffect(() => {
    if (user.token && user.role) {
      if (user.role === "ROLE_ADMIN") navigate("/dashboard");
      else navigate("/dashboard");
    }
  }, [user, navigate]);


  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setError(null);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    try {

      const data = await api<LoginResponse>(`/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (!data.token) {
        toast.error("Wrong mail or password");
        throw new Error(data.message || "Wrong mail or password.");
      }

      login(data.token);
      toast.success("Login successfully");

    } catch (err) {
      toast.error("Error while login");
      const message = err instanceof Error ? err.message : "Error, try again";
      setError(message);
    }
  };


  return (
    <div className="min-h-screen bg-gray-100  py-10 flex flex-col items-center">
      <div className="flex justify-center w-full max-w-md mb-4 text-center ">
        <Button
          onClick={() => navigate("/")}
          className="flex gap-2 items-center bg-transparent hover:bg-gray-300 text-gray-600 "
        >
          <img src={arrowLeft} alt="Back" className="w-4 h-4" />
          Back to Home
        </Button>
      </div>
      <div className="w-full max-w-md flex justify-center gap-4 items-center pb-5">
        <img src={shipIcon} alt="Back" className="w-8 h-8 " />
        <TitleH1 className="">SeaSight</TitleH1>
      </div>

      <FormWrapper>
        <TitleH2 className="mb-2 text-center text-black font-bold">Welcome Back</TitleH2>
        <P className="mb-4 text-center">
          Sign in to your maritime tracking account
        </P>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <Input
            label="Email"
            type="email"
            name="email"
            value={formData.email}
            placeholder="Enter your mail"
            onChange={handleChange}
          />
          <Input
            label="Password"
            type="password"
            name="password"
            value={formData.password}
            placeholder="Enter your password"
            onChange={handleChange}
          />
          <Button
            type="submit"
            className="w-full px-4 py-2 rounded-md bg-blue-600 text-white hover:bg-blue-700"
          >
            Sign In
          </Button>
        </form>

        {error && (
          <p className="mt-4 text-center text-sm text-red-600">{error}</p>
        )}

        <div className="flex font-bold mt-4 items-center text-sm text-black">
          <Button
            onClick={() => alert("Forgot password clicked")}
            className="bg-transparent text-blue-700 hover:underline px-0 py-0"
          >
            Forgot your password?
          </Button>
          <div className="hidden sm:block h-4 w-px bg-gray-300 mx-4"></div>
          <div className="flex items-center gap-0 ">
            <P className="m-0 p-0 gap-0">No account?</P>
            <Button
              onClick={() => navigate("/register")}
              className="bg-transparent text-blue-700 hover:underline px-0 py-0"
            >
              Create an account
            </Button>
          </div>
        </div>
      </FormWrapper>
    </div>
  );
};

export default Login;
