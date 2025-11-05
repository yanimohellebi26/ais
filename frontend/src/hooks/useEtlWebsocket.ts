import useWebSocket, { ReadyState } from "react-use-websocket";
import { useEtlAuth } from "../context/EtlAuthContext";
import {useState} from "react";

const ETL_WS_BASE_URL = import.meta.env.VITE_ETL_WS_URL?.replace(/\/$/, "");

export function useEtlWebSocket(path: string | null) {
    const { apiKey } = useEtlAuth();

    const shouldConnect = Boolean(path && apiKey && ETL_WS_BASE_URL);
    const url = shouldConnect ? `${ETL_WS_BASE_URL}${path}?token=${apiKey}` : null;

    const [messages, setMessages] = useState<any[]>([]);
    const [lastMessage, setLastMessage] = useState<any | null>(null);

    const { sendMessage, readyState } = useWebSocket(url, {
        shouldReconnect: () => false,
        reconnectAttempts: 10,
        reconnectInterval: 3000,
        onOpen: () => console.log("WebSocket connected:", url),
        onClose: () => console.log("WebSocket closed", url),
        onError: (e) => {
            console.error("WS error:", e);
        },
        onMessage: (m) => {
            try {
                const parsed = JSON.parse(m.data);
                setMessages((prev) => [...prev, parsed]);
                setLastMessage(parsed);
            } catch (err) {
                console.error("Failed to parse WS message", err);
            }
        },
    });

    const clearMessages = () => setMessages([]);

    return {
        sendMessage,
        lastMessage,
        messages,
        clearMessages,
        isConnected: readyState === ReadyState.OPEN,
    };
}
