import React from "react";
import { flexRender, Table } from "@tanstack/react-table";
import { Vessel } from "./types";

interface Props  {
    table: Table<Vessel>;
    sortColumn: string;
    sortOrder: 'asc' | 'desc';
    toggleSort: (col: string) => void;
}

const TableDisplay: React.FC<Props> = ({ table, sortColumn, sortOrder, toggleSort }) => {
    return (
        <div className="overflow-y-auto h-126">
            <table className="table table-pin-rows w-full">
                <thead>
                {table.getHeaderGroups().map(headerGroup => (
                    <tr key={headerGroup.id}>
                        {headerGroup.headers.map(header => (
                            <th key={header.id} onClick={() => toggleSort(header.id)}>
                                {flexRender(header.column.columnDef.header, header.getContext())}
                                {sortColumn === header.id && (sortOrder === 'asc' ? ' ↑' : ' ↓')}
                            </th>
                        ))}
                    </tr>
                ))}
                </thead>

                <tbody>
                {table.getRowModel().rows.map(row => (
                    <tr key={row.id}>
                        {row.getVisibleCells().map(cell => (
                            <td key={cell.id}>
                                {flexRender(cell.column.columnDef.cell, cell.getContext())}
                            </td>
                        ))}
                    </tr>
                ))}
                </tbody>
            </table>
        </div>
    );
};

export default TableDisplay;
