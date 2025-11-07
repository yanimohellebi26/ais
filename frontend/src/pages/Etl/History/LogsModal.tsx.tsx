import React, { useEffect, useState } from "react";
import { useEtlWebSocket } from "../../../hooks/useEtlWebsocket";
import PipelineMessages from "../Pipelines/PipelineMessages";

interface Props {
    isOpen: boolean;
    onClose: () => void;
    taskId: string | null;
}

const LogsModal: React.FC<Props> = ({ isOpen, onClose, taskId }) => {
    const { messages: wsMessages, clearMessages } = useEtlWebSocket(
        taskId ? `/tasks/${taskId}` : null
    );
    const [messages, setMessages] = useState<any[]>([]);
    const modalId = "logs_modal";

    useEffect(() => {
        if (isOpen) {
            setMessages(wsMessages);
            const modal = document.getElementById(modalId) as HTMLDialogElement | null;
            modal?.showModal();
        }
    }, [wsMessages, isOpen]);

    const handleClose = () => {
        clearMessages();
        setMessages([]);
        onClose();
        const modal = document.getElementById(modalId) as HTMLDialogElement | null;
        modal?.close();
    };

    useEffect(() => {
        const modal = document.getElementById(modalId) as HTMLDialogElement | null;
        if (!modal) return;

        const handleCancel = () => handleClose();
        modal.addEventListener("close", handleCancel);
        return () => {
            modal.removeEventListener("close", handleCancel);
        };
    }, []);

    useEffect(() => {
        if (taskId) {
            setMessages([]);
            clearMessages();
        }
    }, [taskId]);

    if (!taskId) return null;

    return (
        <dialog id={modalId} className="modal modal-bottom sm:modal-middle">
            <div className="modal-box">
                <h3 className="font-bold text-lg mb-3">
                    Logs task <span className="text-primary">{taskId}</span>
                </h3>

                <div className="overflow-y-auto max-h-[60vh]">
                    <PipelineMessages logs={messages} />
                </div>

                <div className="modal-action">
                    <button className="btn btn-error" onClick={handleClose}>
                        Close
                    </button>
                </div>
            </div>
        </dialog>
    );
};

export default LogsModal;
