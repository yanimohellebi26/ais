import React, { useState } from "react";
import Input from "../components/BaseComponents/Input";
import Button from "../components/BaseComponents/Button";
import FormWrapper from "../components/BaseComponents/FormWrapper";
import TitleH1 from "../components/BaseComponents/TitleH1";
import TitleH2 from "../components/BaseComponents/TitleH2";
import P from "../components/BaseComponents/P";
import SelectRole from "../components/SelectRole";
import arrowLeft from "../assets/arrow-left.svg"
import shipIcon from "../assets/ship-icon.svg"
import { useNavigate } from "react-router-dom";

const Register: React.FC = () => {
  const [formData, setFormData] = useState({ email: "", password: "",username:"",role:""});
  const navigate = useNavigate(); 
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleRoleChange = (e:React.ChangeEvent<HTMLSelectElement>)=>{
    setFormData({...formData, role:e.target.value})
  };

  const validPassword = (password:string)=> {
    const regex = 
      /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*]).{8,}$/; //8caracteres
    return regex.test(password);
  };

  const validEmail = (email:string)=>{
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!formData.username || !formData.email || !formData.password || !formData.role) {
      setError("Fill all the fields");
      return;
    }

    if (!validEmail(formData.email)) {
      setError("Enter a valid email");
      return;
    }

    if (!validPassword(formData.password)) {
      setError(
        "Password must contain at least 8 characters, including uppercase, lowercase, number, and special character"
      );
      return;
    }
    
    //envoie a L'api
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8080/api/v1/auth/register", {
        method:"POST",
        headers: {"Content-Type":"application/json"},
        body:JSON.stringify({
          username: formData.username,
          email: formData.email,
          password: formData.password,
          role: formData.role,
        }),
      });
      if (!res.ok){
        const DataError = await res.json();
        throw new Error(DataError.message || "Registration failed");
      }
      //const data = await res.json();

      alert("Account created");
      navigate("/login"); 
    } 
    catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }    
  

  return (

    <div className="min-h-screen bg-gray-100 py-10 flex flex-col items-center">
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
        <TitleH2 className="mb-2 text-center text-black font-bold">Create Account</TitleH2>
        <P className="mb-4 text-center">
          Join the maritime tracking platform


        </P>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div>
              <Input
                  label="Username"
                  type="text"
                  name="username"
                  value={formData.username}
                  placeholder="Lucas"
                  onChange={handleChange}
              />
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
                  placeholder="Create your password"
                  onChange={handleChange}
              />

              <SelectRole
                name="role"
                value={formData.role}
                onChange={handleRoleChange}
              />
              <Button
                  type="submit"
                  className="w-full px-4 py-2 rounded-md bg-blue-600 text-white hover:bg-blue-700"
              >
                  Create Account
              </Button>
            </div>
        </form>

        <div className="flex  mt-4 text-sm font-bold items-center text-black">
          
          <P>Already have an account ?</P>
          <Button
            onClick={() => navigate("/login")}
            className="bg-transparent text-blue-700 hover:underline px-0 py-0"
          >
             Sign in
          </Button>
        </div>
      </FormWrapper>
    </div>

  );
};

export default Register;