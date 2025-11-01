import React, {useState} from "react";
import {CircleCheck, CircleX, Info, Key, Save} from "lucide-react";
import PasswordInput from "../../../components/BaseComponents/PasswordInput";
import CopyButton from "../../../components/BaseComponents/CopyButton";
import {useEtlAuth} from "../../../context/EtlAuthContext";
import {toast} from "react-toastify";

const ApiKeyForm: React.FC = () => {
    const { apiKey, setApiKey, clearApiKey } = useEtlAuth();
    const [inputKey, setInputKey] = useState(apiKey || "");

    const handleSave = () => {
        setApiKey(inputKey.trim());
        toast.success("API key saved !");
    };

    return (
        <div className="rounded-2xl shadow-sm bg-base-100 p-4 border-accent space-y-2">
            <div className="flex items-center">
                <Key/>
                <span className="font-semibold pl-2 mr-2">API Key Configuration</span>
                {apiKey !== "" ? (
                    <div className="badge badge-success badge-soft">
                        <CircleCheck className="w-4" />
                        Key found
                    </div>
                ) :
                    <div className="badge badge-error badge-soft">
                        <CircleX className="w-4"/>
                        No key found
                    </div>
                }
            </div>
            <p className="text-base-content/70" >Configure your API key for accessing external AIS data feeds and services</p>
            <span className="label font-semibold">API Key</span>
            <div className="flex items-center">
                <PasswordInput
                    placeholder="Enter API Key"
                    id="api-key-input"
                    value={inputKey}
                    onChange={(e) => setInputKey(e.target.value)}
                />
                <CopyButton className="mx-4 " targetId={"api-key-input"} />
            </div>
            <button className="btn btn-soft btn-success" onClick={handleSave}>
                <Save className=""/>
                Save API Key
            </button>
            <div role="alert" className="alert alert-info alert-outline ">
                <Info/>
                <div>
                    <strong>Security Notice:</strong>
                    <span className="block">
                        Your API key is stored locally in your browser. <br/> Never share this key with
                        unauthorized users. If you need new API-Key contact your <strong>Devops</strong>.
                  </span>
                </div>
            </div>

        </div>
    );
};

export default ApiKeyForm;
