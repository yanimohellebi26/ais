import React from "react";

interface Props {
    files: string[];
    selectedFiles: string[];
    onToggleFile: (file: string) => void;
    onRemoveFile: (file: string) => void;
    hideSelectedList?: boolean;
}

const FileSelector: React.FC<Props> = ({
                                           files,
                                           selectedFiles,
                                           onToggleFile,
                                           onRemoveFile,
                                           hideSelectedList = false,
                                       }) => {
    if (files.length === 0) return null;

    return (
        <div className="form-control w-full">
            <label className="label">
                <span className="label-text">Select files</span>
            </label>

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
                    {files.map((file) => (
                        <li key={file}>
                            <label className="label cursor-pointer justify-start gap-2">
                                <input
                                    type="checkbox"
                                    className="checkbox checkbox-sm"
                                    checked={selectedFiles.includes(file)}
                                    onChange={() => onToggleFile(file)}
                                />
                                <span className="label-text">{file}</span>
                            </label>
                        </li>
                    ))}
                </ul>
            </div>

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
