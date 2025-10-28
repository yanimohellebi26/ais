import useWebSocket, { ReadyState } from "react-use-websocket";
import { useEtlAuth } from "../context/EtlAuthContext";
import { toast } from "react-toastify";

const ETL_WS_BASE_URL = import.meta.env.VITE_ETL_WS_URL?.replace(/\/$/, "");

export function useEtlWebSocket(path: string | null) {
    const { apiKey } = useEtlAuth();

    const shouldConnect = Boolean(path && apiKey && ETL_WS_BASE_URL);
    const url = shouldConnect ? `${ETL_WS_BASE_URL}${path}?token=${apiKey}` : null;

    const { sendMessage, lastMessage, readyState } = useWebSocket(url, {
        shouldReconnect: () => false,
        reconnectAttempts: 10,
        reconnectInterval: 3000,
        onOpen: () => console.log("WebSocket connected:", url),
        onClose: () => console.log("WebSocket closed", url),
        onError: (e) => {
            console.error("WS error:", e);
            toast.error("WebSocket connection failed");
        },
    });

    const parsedData = lastMessage ? JSON.parse(lastMessage.data) : null;

    return {
        sendMessage,
        data: parsedData,
        isConnected: readyState === ReadyState.OPEN,
    };
}
