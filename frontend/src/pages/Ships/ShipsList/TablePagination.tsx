import React, {useState} from "react";

interface Props {
    pageIndex: number;
    totalItems: number;
    pageSize: number;
    setPageIndex: React.Dispatch<React.SetStateAction<number>>;
}

const TablePagination: React.FC<Props> = ({ pageIndex, totalItems, pageSize, setPageIndex }) => {
    const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
    const [inputValue, setInputValue] = useState(pageIndex + 1);

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        if (/^\d*$/.test(value)) {
            setInputValue(value === "" ? 0 : parseInt(value));
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === "Enter") {
            const pageNumber = Math.min(Math.max(1, inputValue), totalPages);
            setPageIndex(pageNumber - 1);
        }
    };

    React.useEffect(() => {
        setInputValue(pageIndex + 1);
    }, [pageIndex]);

    return (
        <div className="flex justify-between items-center mt-4">
            <button
                className="btn btn-sm"
                onClick={() => setPageIndex(old => Math.max(old - 1, 0))}
                disabled={pageIndex === 0}
            >
                Previous
            </button>

            <div className="flex items-center gap-2">
                <input
                    type="text"
                    value={inputValue}
                    onChange={handleInputChange}
                    onKeyDown={handleKeyDown}
                    className="input input-sm w-16 text-center"
                />
                <span>/ {totalPages}</span>
            </div>

            <button
                className="btn btn-sm"
                onClick={() => setPageIndex(old => Math.min(old + 1, totalPages - 1))}
                disabled={pageIndex + 1 >= totalPages}
            >
                Next
            </button>
        </div>
    );
};

export default TablePagination;
