import React from "react";

type Props = {
    pageIndex: number;
    totalItems: number;
    pageSize: number;
    setPageIndex: React.Dispatch<React.SetStateAction<number>>;
};

const TablePagination: React.FC<Props> = ({ pageIndex, totalItems, pageSize, setPageIndex }) => {
    const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));

    return (
        <div className="flex justify-between items-center mt-4">
            <button
                className="btn btn-sm"
                onClick={() => setPageIndex(old => Math.max(old - 1, 0))}
                disabled={pageIndex === 0}
            >
                Previous
            </button>

            <span>Page {pageIndex + 1} / {totalPages}</span>

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
