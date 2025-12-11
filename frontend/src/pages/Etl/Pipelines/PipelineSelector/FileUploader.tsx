import React, { useState } from "react";
import { Upload, X, FileCheck } from "lucide-react";
import {toast} from "react-toastify";
import {useEtlApi} from "../../../../hooks/useEtlApi";

interface Props {
    onFileUploaded: () => void;
}

const FileUploader: React.FC<Props> = ({ onFileUploaded }) => {
    const api = useEtlApi();
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [dragActive, setDragActive] = useState(false);

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setSelectedFile(e.target.files[0]);
        }
    };

    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            setSelectedFile(e.dataTransfer.files[0]);
        }
    };

    const handleUpload = async () => {
        if (!selectedFile) return;

        setUploading(true);
        try {
            const formData = new FormData();
            formData.append("file", selectedFile);

            await api("/files/upload", {
                method: "POST",
                body: formData,
            });

            setSelectedFile(null);
            onFileUploaded();
        } catch (error: any) {
            toast.error(error.message || "File upload failed");
        } finally {
            setUploading(false);
        }
    };

    const formatFileSize = (bytes: number): string => {
        if (bytes === 0) return "0 B";
        const k = 1024;
        const sizes = ["B", "KB", "MB", "GB"];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
    };

    return (
        <div className="form-control w-full">
            <label className="label">
                <span className="label-text font-semibold">Upload New File</span>
            </label>

            <div
                className={`border-2 border-dashed rounded-lg p-3 transition-colors ${
                    dragActive
                        ? "border-primary bg-primary/5"
                        : "border-base-300 hover:border-primary/50"
                }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
            >
                {!selectedFile ? (
                    <div className="flex items-center gap-4">
                        <Upload className="w-8 h-8 text-base-content/40 flex-shrink-0" />
                        <div className="flex-1">
                            <p className="text-sm text-base-content/70">
                                Drag and drop your file here
                            </p>
                            <p className="text-xs text-base-content/50">
                                Supported formats: CSV
                            </p>
                        </div>
                        <label className="btn btn-sm btn-primary cursor-pointer flex-shrink-0">
                            Browse
                            <input
                                type="file"
                                className="hidden"
                                onChange={handleFileSelect}
                                accept=".csv,.xlsx,.xls"
                            />
                        </label>
                    </div>
                ) : (
                    <div className="flex items-center gap-3">
                        <FileCheck className="w-8 h-8 text-success flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                            <p className="font-medium truncate text-sm">{selectedFile.name}</p>
                            <p className="text-xs text-base-content/60">
                                {formatFileSize(selectedFile.size)}
                            </p>
                        </div>
                        <div className="flex items-center gap-2 flex-shrink-0">
                            <button
                                className="btn btn-primary btn-sm"
                                onClick={handleUpload}
                                disabled={uploading}
                            >
                                {uploading ? (
                                    <>
                                        <span className="loading loading-spinner loading-xs"></span>
                                        Uploading...
                                    </>
                                ) : (
                                    <>
                                        <Upload className="w-4 h-4" />
                                        Upload
                                    </>
                                )}
                            </button>
                            <button
                                className="btn btn-ghost btn-sm btn-circle"
                                onClick={() => setSelectedFile(null)}
                                disabled={uploading}
                            >
                                <X className="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default FileUploader;