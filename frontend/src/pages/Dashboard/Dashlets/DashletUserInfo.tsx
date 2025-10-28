import React, {useEffect} from "react";
import TitleH2 from "../../../components/BaseComponents/TitleH2";
import {CircleUserRound, Mail, User} from "lucide-react";
import Button from "../../../components/BaseComponents/Button";
import Card from "../../../components/BaseComponents/Card";
import {useCurrentUser} from "../../../hooks/useCurrentUser";
import {useChangePassword} from "../../../components/Swals/SwallPasswordChanger";
import {useLoading} from "../../../context/LoadingContext";


const DashletUserInfo: React.FC = () => {
    const {userData,error} = useCurrentUser();
    const {handleChangePassword} = useChangePassword(userData?.id);

    return (
        <Card >
            <figure className="w-full h-48">
                <User className="w-24 h-24 text-success border-4 bg-success/10 rounded-full"/>
            </figure>

            <div className="card-body">
                <TitleH2 className="card-title ">
                    Personnal data
                </TitleH2>

                {error && (
                    <p className="text-center text-danger font-medium">{error}</p>
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
                    <Button onClick={handleChangePassword} className="btn btn-primary" >Change password</Button>
                </div>
            </div>
        </Card>

    );
};

export default DashletUserInfo;
