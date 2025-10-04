import React, { useState } from "react";
import Input from "../components/Input";
import Button from "../components/Button";
import FormWrapper from "../components/FormWrapper";
import TitleH1 from "../components/titleh1";
import TitleH2 from "../components/titleh2";
import P from "../components/p";
import arrowLeft from "../assets/arrow-left.svg"
import shipIcon from "../assets/ship-icon.svg"
import { useNavigate } from "react-router-dom";

const Login: React.FC = () => {
  const [formData, setFormData] = useState({ email: "", password: "" });
  const navigate = useNavigate(); 

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log("Login data:", formData);
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
      

      <FormWrapper >
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

        <div className="flex justify-between mt-4 text-sm text-black">
          <Button
            onClick={() => alert("Forgot password clicked")}
            className="bg-transparent text-blue-700 hover:underline px-0 py-0"
          >
            Forgot your password?
          </Button>
          <Button
            onClick={() => alert("Create account clicked")}
            className="bg-transparent text-blue-700 hover:underline px-0 py-0"
          >
            Don't have an account? Create an account
          </Button>
        </div>
      </FormWrapper>
    </div>

  );
};

export default Login;
