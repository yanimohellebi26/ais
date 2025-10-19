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




    return (
        <div>
            <Breadcrumbs/>
            <TitleH1 className="text-2xl font-bold mb-4">Welcome in, {userData?.username}</TitleH1>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-3xl mx-auto p-4">
                
                
                <Card >
                    <figure className="w-full h-48">
                        <img
                        src="https://media.licdn.com/dms/image/v2/D4E03AQHEWr2VBd2YXA/profile-displayphoto-shrink_200_200/profile-displayphoto-shrink_200_200/0/1729427211768?e=1762387200&v=beta&t=Q1B3iZcNaFtgYBpCN8d0P79_ZVcLSrpCnEK2Jw5KTzU"
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
                            <Button onClick={() =>navigate("/")} className="btn btn-primary " >Change password</Button>
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
