import React, { useState } from "react";
import { toast } from "react-toastify";
import { useApi } from "../../../hooks/useApi";
import { Vessel } from "./types";
import { useCurrentUser } from "../../../hooks/useCurrentUser";

interface RequestModalProps {
    vessel: Vessel;
    onClose: () => void;
}

const RequestModal: React.FC<RequestModalProps> = ({ vessel, onClose }) => {
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const { userData, error } = useCurrentUser();
    const api = useApi();

    const handleConfirmRequest = async () => {
        if (!selectedFile) {
            toast.warn("Please select a file before confirming.");
            return;
        }
        if (!userData) {
            toast.error(error);
            return;
        }

        try {
            setIsLoading(true);

            const formData = new FormData();
            formData.append("file", selectedFile);

            const uploadResponse = await api("/api/v1/uploads", {
                method: "POST",
                body: formData,
            });

            const fileId = uploadResponse?.id;
            if (!fileId) throw new Error("Invalid upload response");

            await api("/api/v1/request-property", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    userid: userData.id,
                    mmsi: vessel.mmsi,
                    fileid: fileId,
                }),
            });

            toast.success(`Request created successfully for ${vessel.vesselName}`);
            onClose();
        } catch (e) {
            console.error(e);
            toast.error("Failed to create request");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-opacity-50 flex justify-center items-center z-50">
            <div className="bg-white rounded-2xl p-6 shadow-lg w-96 text-center">
                <h2 className="text-lg font-bold mb-4">Request Access</h2>
                <p className="mb-4">
                    Upload a file to request access for vessel <b>{vessel.vesselName}</b>.
                </p>

                <input
                    type="file"
                    accept="*/*"
                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                    className="file-input file-input-bordered w-full mb-4"
                />

                <div className="flex justify-center gap-4">
                    <button
                        className={`btn btn-primary ${isLoading ? "loading" : ""}`}
                        onClick={handleConfirmRequest}
                        disabled={isLoading}
                    >
                        {isLoading ? "Processing..." : "Confirm"}
                    </button>
                    <button className="btn btn-outline" onClick={onClose}>
                        Cancel
                    </button>
                </div>
            </div>
        </div>
    );
};

export default RequestModal;
