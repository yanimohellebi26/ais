import React, { useEffect, useState } from "react";

type ColumnMeta = { id?: string; header?: string | React.ReactNode };

interface Props {
    searchTerm: string;
    setSearchTerm: (v: string) => void;
    allColumns: ColumnMeta[];
    visibleColumns: string[];
    toggleColumn: (colId: string) => void;
};

const TableControls: React.FC<Props> = ({
                                                         searchTerm,
                                                         setSearchTerm,
                                                         allColumns,
                                                         visibleColumns,
                                                         toggleColumn
                                                     }) => {
    const [inputValue, setInputValue] = useState(searchTerm);

    useEffect(() => {
        const handler = setTimeout(() => {
            setSearchTerm(inputValue);
        }, 1000);

        return () => clearTimeout(handler);
    }, [inputValue, setSearchTerm]);

    return (
        <div className="flex flex-wrap gap-4 items-center mb-4">
            <input
                type="text"
                placeholder="Search by mmsi or name ..."
                className="input input-bordered input-sm"
                value={inputValue}
                onChange={e => setInputValue(e.target.value)}
            />

            <div className="dropdown dropdown-hover dropdown-right">
                <div tabIndex={0} role="button" className="btn m-1">Columns</div>
                <ul tabIndex={-1} className="dropdown-content menu bg-base-100 rounded-box z-2 w-52 p-2 shadow-sm">
                    {allColumns.map(col => (
                        <li key={col.id}>
                            <label className="label cursor-pointer flex justify-between items-center">
                                <span>{col.header as string}</span>
                                <input
                                    type="checkbox"
                                    className="checkbox checkbox-xs"
                                    checked={col.id ? visibleColumns.includes(col.id) : false}
                                    onChange={() => col.id && toggleColumn(col.id)}
                                />
                            </label>
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    );
};

export default TableControls;
