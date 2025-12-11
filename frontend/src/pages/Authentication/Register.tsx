import React, { ChangeEvent, FormEvent, useState } from "react";
import Input from "../../components/BaseComponents/Input";
import Button from "../../components/BaseComponents/Button";
import FormWrapper from "../../components/BaseComponents/FormWrapper";
import TitleH1 from "../../components/BaseComponents/TitleH1";
import TitleH2 from "../../components/BaseComponents/TitleH2";
import P from "../../components/BaseComponents/P";
import SelectRole from "./SelectRole";
import arrowLeft from "../../assets/arrow-left.svg";
import shipIcon from "../../assets/ship-icon.svg";
import { useNavigate } from "react-router-dom";
import {toast} from "react-toastify";
import {ArrowLeft, Ship} from "lucide-react";

type RegisterForm = {
  username: string;
  email: string;
  password: string;
  role: string;
};

type RegisterErrorResponse = {
  message?: string;
};

const Register = () => {
  const [formData, setFormData] = useState<RegisterForm>({
    email: "",
    password: "",
    username: "",
    role: "",
  });
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleRoleChange = (event: ChangeEvent<HTMLSelectElement>) => {
    setFormData((prev) => ({ ...prev, role: event.target.value }));
  };

  const validPassword = (password: string) => {
    const regex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*]).{8,}$/;
    return regex.test(password);
  };

  const validEmail = (email: string) => {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    if (!formData.username || !formData.email || !formData.password || !formData.role) {
      toast.warning("Fill all the fields");
      setError("Fill all the fields");
      return;
    }

    if (!validEmail(formData.email)) {
      toast.warning("Enter a valid email");
      setError("Enter a valid email");
      return;
    }

    if (!validPassword(formData.password)) {
      toast.warning("Password must contain at least 8 characters, including uppercase, lowercase, number, and special character");
      setError(
        "Password must contain at least 8 characters, including uppercase, lowercase, number, and special character",
      );
      return;
    }

    setLoading(true);
    try {
      const apiBaseUrl = import.meta.env.VITE_API_URL?.replace(/\/$/, "");

      if (!apiBaseUrl) {
        toast.error("Internal error");
        throw new Error("La variable d'environnement VITE_API_URL est manquante.");
      }

      const response = await fetch(`${apiBaseUrl}/api/v1/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const dataError = (await response.json()) as RegisterErrorResponse;
        toast.error("Registration failed")
        throw new Error(dataError.message || "Registration failed");
      }

      navigate("/login");
      toast.success("Account created ! You can logged in now")
    } catch (err) {
      toast.error("Registration failed");
      const message = err instanceof Error ? err.message : "Registration failed";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
      <div className="min-h-screen bg-base-100 py-10 flex flex-col items-center">
        <div className="flex justify-center w-full max-w-md mb-4 text-center ">
          <Button
              onClick={() => navigate("/")}
              className="flex gap-2 items-center btn btn-ghost "
          >
            <ArrowLeft />
            Back to Home
          </Button>
        </div>
        <div className="w-full max-w-md flex justify-center gap-4 items-start pb-5">
          <Ship className="text-primary w-8 h-8"/>
          <TitleH1 className="text-base-content">SeaSight</TitleH1>
        </div>

      <FormWrapper>
        <TitleH2 className="mb-2 text-center font-bold">Create Account</TitleH2>
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

            <SelectRole name="role" value={formData.role} onChange={handleRoleChange} />
            <Button
              type="submit"
              className="w-full px-4 py-2 rounded-md btn btn-primary"
              disabled={loading}
            >
              {loading ? "Creating..." : "Create Account"}
            </Button>
          </div>
        </form>

        {error && <p className="mt-4 text-center text-sm text-error">{error}</p>}

        <div className="flex  mt-4 text-sm font-bold items-center">
          <P>Already have an account ?</P>
          <Button
            onClick={() => navigate("/login")}
            className="bg-transparent text-primary hover:underline px-0 py-0"
          >
            Sign in
          </Button>
        </div>
      </FormWrapper>
    </div>
  );
};

export default Register;
