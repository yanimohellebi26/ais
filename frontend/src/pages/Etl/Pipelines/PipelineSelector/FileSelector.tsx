import React from "react";
import { FileInfo } from "../interfaces";
import { CheckCircle, XCircle } from "lucide-react";

interface Props {
    files: FileInfo[];
    selectedFiles: string[];
    onToggleFile: (file: string) => void;
    onRemoveFile: (file: string) => void;
    hideSelectedList?: boolean;
    requiredColumns?: string[];
}

const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
};

const hasRequiredColumns = (fileColumns: string[] | undefined, requiredColumns: string[]): boolean => {
    if (!Array.isArray(fileColumns) || fileColumns.length === 0) return false;
    return requiredColumns.every(reqCol => fileColumns.includes(reqCol));
};

const FileSelector: React.FC<Props> = ({
                                           files,
                                           selectedFiles,
                                           onToggleFile,
                                           onRemoveFile,
                                           hideSelectedList = false,
                                           requiredColumns = [],
                                       }) => {
    // Filter compatible files
    const compatibleFiles = files.filter(fileInfo =>
        requiredColumns.length === 0 || hasRequiredColumns(fileInfo.columns, requiredColumns)
    );

    // Determine if all compatible files are selected
    const allCompatibleSelected = compatibleFiles.length > 0 &&
        compatibleFiles.every(fileInfo => selectedFiles.includes(fileInfo.filename));

    // Function to select/deselect all compatible files
    const handleToggleAll = () => {
        if (allCompatibleSelected) {
            // Deselect all compatible files
            compatibleFiles.forEach(fileInfo => {
                if (selectedFiles.includes(fileInfo.filename)) {
                    onRemoveFile(fileInfo.filename);
                }
            });
        } else {
            // Select all compatible files
            compatibleFiles.forEach(fileInfo => {
                if (!selectedFiles.includes(fileInfo.filename)) {
                    onToggleFile(fileInfo.filename);
                }
            });
        }
    };

    return (
        <div className="form-control w-full">
            <label className="label">
                <span className="label-text">Select files</span>
            </label>

            {files.length === 0 ? (
                <div className="p-3 text-center text-base-content/60 border rounded-lg">
                    No file available
                </div>
            ) : (
                <div className="flex gap-2 items-center">
                    <div className="dropdown dropdown-bottom w-full">
                        <label tabIndex={0} className="btn btn-outline w-full justify-between">
                        <span>
                            {selectedFiles.length === 0
                                ? "Choose files..."
                                : `${selectedFiles.length} file(s) selected`}
                        </span>
                            <svg
                                className="w-4 h-4"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M19 9l-7 7-7-7"
                                />
                            </svg>
                        </label>

                        <ul
                            tabIndex={0}
                            className="dropdown-content menu p-2 shadow bg-base-100 rounded-box w-full max-h-60 overflow-y-auto flex-nowrap"
                        >
                            {files.map((fileInfo) => {
                                const isValid = requiredColumns.length === 0 || hasRequiredColumns(fileInfo.columns, requiredColumns);

                                return (
                                    <li key={fileInfo.filename}>
                                        <label className="label cursor-pointer justify-start gap-2 hover:bg-base-200">
                                            <input
                                                type="checkbox"
                                                className="checkbox checkbox-sm"
                                                checked={selectedFiles.includes(fileInfo.filename)}
                                                onChange={() => onToggleFile(fileInfo.filename)}
                                                disabled={!isValid}
                                            />
                                            <div className="flex flex-col flex-1">
                                                <div className="flex items-center gap-2">
                                                <span className={`label-text font-medium ${!isValid ? 'opacity-70' : ''}`}>
                                                    {fileInfo.filename}
                                                </span>
                                                    {requiredColumns.length > 0 && (
                                                        isValid ? (
                                                            <CheckCircle className="w-4 h-4 text-success" />
                                                        ) : (
                                                            <XCircle className="w-4 h-4 text-error" />
                                                        )
                                                    )}
                                                </div>
                                                <span className={`text-xs text-base-content/70 ${!isValid ? 'opacity-70' : ''}`}>
                                                {(fileInfo.columns || []).map((col, index) => (
                                                    <span key={index}>{col} </span>
                                                ))}
                                            </span>
                                                <span className={`text-xs text-base-content/60 ${!isValid ? 'opacity-70' : ''}`}>
                                                {formatFileSize(fileInfo.size_bytes)}
                                            </span>
                                            </div>
                                        </label>
                                    </li>
                                );
                            })}
                        </ul>
                    </div>

                    {compatibleFiles.length > 0 && (
                        <button
                            type="button"
                            className="btn btn-sm btn-primary"
                            onClick={handleToggleAll}
                        >
                            {allCompatibleSelected ? 'Deselect all' : 'Select all compatible'}
                        </button>
                    )}
                </div>
            )}

            {!hideSelectedList && selectedFiles.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2">
                    {selectedFiles.map((file) => (
                        <div key={file} className="badge badge-primary gap-2">
                            {file}
                            <button
                                onClick={() => onRemoveFile(file)}
                                className="btn btn-ghost btn-xs btn-circle"
                            >
                                ✕
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default FileSelector;