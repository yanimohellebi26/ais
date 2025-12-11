import React from "react";
import { Copy, Check } from "lucide-react";

type CopyButtonProps = {
    targetId: string;
    className?: string;
};

const CopyButton: React.FC<CopyButtonProps> = ({ targetId, className = "" }) => {
    const [copied, setCopied] = React.useState(false);

    const handleCopy = async () => {
        const input = document.getElementById(targetId) as HTMLInputElement | null;
        if (!input) return;

        try {
            await navigator.clipboard.writeText(input.value);
            setCopied(true);
            setTimeout(() => setCopied(false), 1500);
        } catch (err) {
            console.error("Failed to copy: ", err);
        }
    };

    return (
        <button
            type="button"
    onClick={handleCopy}
    className={`btn btn-ghost btn-sm flex items-center gap-1 ${className}`}
    title="Copy to clipboard"
        >
        {copied ? <Check size={18} /> : <Copy size={18} />}
    {copied ? "Copied!" : "Copy"}
    </button>
);
};

export default CopyButton;
