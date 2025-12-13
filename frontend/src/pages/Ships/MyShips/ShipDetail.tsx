import React, { useEffect, useState } from "react";
import {Vessel, UserPublicDetails, CaptainDetails, Port} from "../interfaces";
import { useApi } from "../../../hooks/useApi";
import { toast } from "react-toastify";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import Breadcrumbs from "../../../components/BaseComponents/Breadcrumbs";
import Card from "../../../components/BaseComponents/Card";
import { useCaptainModal } from "./ModalCaptain";
import { useLoading } from "../../../context/LoadingContext";
import ShipCards from "./components/ShipCards";
import MapWidget from "../../Map/components/MapWidget";
import {ArrowLeft, Plus, User} from "lucide-react";
import {useAuth} from "../../../context/AuthContext";
import PortCard from "./components/PortCard.tsx";

const ShipDetail : React.FC = () =>{
    const location = useLocation();
    const navigate = useNavigate();
    const { user } = useAuth();

    const {id} = useParams<{id:string}>();

    const api = useApi();
    const {loading, setLoading} = useLoading();

    const vessel = location.state?.vessel as Vessel | undefined;
    const captain = vessel?.users?.find(u => u.role === "CAPTAIN") || null;

    const [currentCaptainVessel, setCurrentCaptainVessel] = useState<UserPublicDetails | null>(captain);
    const [captains, setCaptains] = useState<CaptainDetails[]>([]);
    const [nearestPort, setNearestPort] = useState<Port>();
    const [nearestPortGeoJson, setNearestPortGeoJson] = useState<any>(null);


    const { modalCaptain } = useCaptainModal(
        captains,
        vessel,
        api,
        setCurrentCaptainVessel
    );

    const fetchCaptains = async () => {
        if(user?.role !== "ROLE_ADMIN" && user?.role !== "ROLE_OWNER") return;
        setLoading(true);
        try {
            const data = await api(`/api/v1/users/role?role=CAPTAIN`);
            setCaptains(data);
        } catch (err : any) {
            toast.error(err.message || "Error while retrieving captains");
        } finally {
            setLoading(false);
        }
    };

    const fetchNearestPort = async () => {
        if(!vessel?.id) return;
        setLoading(true);
        try {
            const response = await api(`/api/v1/ports/nearest?vesselId=${vessel.id}`);

            setNearestPortGeoJson(response);

            const data = response.features[0] ?? null;
            if (data) {
                const port = {
                    portId: data.properties.portId,
                    name: data.properties.name,
                    code: data.properties.code,
                    country: data.properties.country,
                    distance: data.properties.distance,
                    latitude: data.geometry.coordinates[1],
                    longitude: data.geometry.coordinates[0],
                };
                setNearestPort(port);
            }
        } catch (err : any) {
            toast.error(err.message || "Error while retrieving port");
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        fetchCaptains();
        fetchNearestPort();
    }, [id]);

    const handleDelete = async () => {
        if (!currentCaptainVessel?.id || !vessel?.id) return;
        try {
            const data = await api(`/api/v1/vessels/unrelate`,{
                method:"POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    userId: currentCaptainVessel?.id,
                    vesselId: vessel?.id
                })
            });
            setCurrentCaptainVessel(null);
            toast.success("Captain removed successfully");
        } catch (err:any) {
            toast.error(err.message || "Error while removing captain");
        }
    };

    if (!vessel) return <div className="text-center py-10">Vessel not found</div>;

    return (
        <>
            <Breadcrumbs/>
            <div className="flex gap-4 mt-4">
                <button className="btn btn-sm btn-outline" onClick={() => navigate(-1)}>
                    <ArrowLeft />
                    Back
                </button>
                <h1 className="text-2xl font-semibold mr-4"> Information about {vessel.vesselName} </h1>
            </div>

            <div className="grid grid-cols-4 py-6 gap-4">
                <ShipCards vessel={vessel} />

                <Card className="col-span-2 h-96">
                    <MapWidget vesselId={vessel.id} portGeoJson={nearestPortGeoJson} />

                </Card>

                <Card className="col-span-2 h-96">
                    <PortCard port={nearestPort} />
                </Card>

                {(user?.role === "ROLE_ADMIN" || user?.role === "ROLE_OWNER") && (
                    <Card className="col-span-2 col-start-2 col-end-4">
                        <div className="p-6 flex items-center gap-6">
                            <figure className="">
                                <User className="w-24 h-24 text-success border-4 bg-success/10 rounded-full"/>
                            </figure>
                            <div className="flex flex-col h-full">
                                <h1 className="mb-2 font-bold text-xl">
                                    {currentCaptainVessel?.username || "Assign a Captain"}
                                </h1>

                                <h2 className="mb-2 font-semibold text-sm">
                                    {currentCaptainVessel?.email || ""}
                                </h2>

                                <p className="py-4">
                                    The current captain for this vessel is{" "}
                                    {currentCaptainVessel?.username || "not assigned"}
                                </p>
                                {currentCaptainVessel?(
                                    <button onClick={handleDelete} className="btn btn-error w-fit ml-auto mt-auto ">
                                        Delete
                                    </button>
                                ) : (<button onClick={modalCaptain} className="btn btn-primary w-fit ml-auto mt-auto ">
                                        <Plus /> Add
                                    </button>
                                )}

                            </div>
                        </div>
                    </Card>
                )}

            </div>

        </>
    );

};

export default ShipDetail;