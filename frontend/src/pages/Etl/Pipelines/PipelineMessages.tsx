import React, { useEffect, useRef } from "react";

interface Props {
    className?: string;
    logs: any[];
}

const PipelineMessages: React.FC<Props> = ({ className, logs }) => {
    const logEntries = logs
        .filter((msg) => msg.type === "logs")
        .flatMap((msg) => msg.data);

    const containerRef = useRef<HTMLDivElement>(null);

    // Auto scroll
    useEffect(() => {
        if (containerRef.current) {
            containerRef.current.scrollTop = containerRef.current.scrollHeight;
        }
    }, [logEntries]);

    return (
        <div className={`${className} rounded-2xl max-h-60 shadow-sm bg-base-100 p-4 border-accent`}>
            <h3 className="font-semibold mb-2 text-base-content/80">Logs</h3>
            <div
                ref={containerRef}
                className="overflow-y-auto max-h-40 space-y-1 font-mono text-sm"
            >
                {logEntries.length > 0 ? (
                    logEntries.map((entry: any, i: number) => {
                        const { timestamp, type, status, payload } = entry;
                        const stepName =
                            payload?.step && payload?.index ? ` ${payload.index}-${payload.step} ` : "";
                        return (
                            <div key={i} className="whitespace-pre-wrap">
                                <span className="text-gray-500">{`[${timestamp}]`}</span>
                                {` : ${type}${stepName} -> ${status}`}
                            </div>
                        );
                    })
                ) : (
                    <div className="text-base-content/50 italic">No logs yet...</div>
                )}
            </div>
        </div>
    );
};

export default PipelineMessages;
