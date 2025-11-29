import React, { useEffect, useState } from "react";
import Breadcrumbs from "../../../components/BaseComponents/Breadcrumbs";
import { useApi } from "../../../hooks/useApi";
import { toast } from "react-toastify";
import { useCurrentUser } from "../../../hooks/useCurrentUser";
import Card from "../../../components/BaseComponents/Card";
import Input from "../../../components/BaseComponents/Input";
import { Search } from "lucide-react";
import Button from "../../../components/BaseComponents/Button";
import { useNavigate } from "react-router-dom";
import { Vessel } from "../interfaces";
import {useLoading} from "../../../context/LoadingContext";

const DashboardShipsMyShips: React.FC = () => {
    const [vessels,setVessels] = useState<Vessel[]>([]);
    const {loading, setLoading} = useLoading();
    const [search,setSearch] = useState<string>("");
    const api = useApi();
    const {userData} = useCurrentUser();
    const navigate = useNavigate();

    useEffect(() => {
        const fetchVessels = async () => {
            if (!userData?.id) return;
            setLoading(true);
            try {
                const data = await api(`/api/v1/vessels/userId/${userData.id}`);
                setVessels(data);
            } catch (err: any) {
                toast.error(err.message || "Error while retrieving vessels");
            } finally {
                setLoading(false);
            }
        };
        fetchVessels();
    }, [userData?.id]);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setSearch(e.target.value);
    }

    const filteredVessels = vessels.filter(vessel =>
        vessel.vesselName.toLowerCase().startsWith(search.toLowerCase())
    );

    return (
        <>
            <Breadcrumbs/>
            <div className="flex justify-between mb-6">
                <h1 className="text-2xl font-semibold mr-4"> My Ships </h1>

            </div>
            <div className="flex items-baseline mb-6 space-x-4">
                <Input
                    name="search"
                    value={search}
                    placeholder="Search ships..."
                    onChange={handleChange}
                    icon={Search}
                />
                <span className="badge badge-primary">
                    {filteredVessels.length} vessel{filteredVessels.length !== 1 && "s"} in fleet
                </span>
            </div>
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {filteredVessels.map((vessel) => (
                    <Card
                        key={vessel.id}
                        className="
                        p-6 flex flex-col justify-between hover:shadow-xl transition-shadow duration-300 rounded-4xl overflow-hidden backdrop-blur-sm"
                    >
                        <div className="flex justify-between items-start mb-4">
                            <div>
                                <h2 className="font-semibold text-xl">{vessel.vesselName}</h2>
                                <p className="text-sm text-base-content/60">{vessel.vesselTypeName}</p>
                            </div>
                            <span
                                className={`badge badge-soft ${
                                    vessel.locked
                                        ? "badge-success "
                                        : "badge-primary "
                                }`}
                            >
                                {vessel.locked ? "Locked" : "Unlocked"}
                            </span>
                        </div>

                        <div className="h-36 w-full bg-base-300 rounded-lg mb-4 flex items-center justify-center text-base-content/50 text-sm">
                            <img src="https://images.pexels.com/photos/3327981/pexels-photo-3327981.jpeg" alt="Ship" className="h-full w-full object-cover rounded-lg"/>
                        </div>

                        <div className="text-sm mb-4 space-y-1">
                            <p><strong>MMSI:</strong> {vessel.mmsi}</p>
                            <p><strong>IMO:</strong> {vessel.imo}</p>
                            <p>
                                <strong>Dimensions:</strong> {vessel.length}m × {vessel.width}m | Draft: {vessel.draft}m
                            </p>
                            <p><strong>Transceiver:</strong> {vessel.transceiverClass}</p>
                        </div>

                        <Button
                            onClick={() =>
                                navigate(`${vessel.id}`, {
                                    state: { vessel },
                                })
                            }
                        >
                            View Details
                        </Button>

                    </Card>
                ))}
            </div>
        </>
    );
};

export default DashboardShipsMyShips;
