import React, { useMemo } from "react";
import { useReactTable, getCoreRowModel, ColumnDef, flexRender } from "@tanstack/react-table";

type GenericTableProps<T> = {
    data: T[];
    columns: ColumnDef<T, any>[];
    className?: string;
};

export const GenericTable = <T,>({
    data,
    columns,
    className = "",
}: GenericTableProps<T>) => {
    const table = useReactTable({
        data, columns, getCoreRowModel: getCoreRowModel()
    });

    return (
        <div className={`overflow-x-auto ${className}`}>
            <table className="min-w-full border border-gray-300 rounded-lg bg-white shadow-sm">
                <thead className="bg-gray-100">
                {table.getHeaderGroups().map((headerGroup) => (
                    <tr key={headerGroup.id}>
                    {headerGroup.headers.map((header) => (
                        <th key={header.id} className="px-4 py-2 text-left">
                        {header.isPlaceholder
                            ? null
                            : flexRender(
                                header.column.columnDef.header,
                                header.getContext()
                            )}
                        </th>
                    ))}
                    </tr>
                ))}
                </thead>
                <tbody>
                {table.getRowModel().rows.map((row, rowIndex) => (
                    <tr
                    key={row.id}
                    className={"border-t bg-gray-50"}
                    >
                    {row.getVisibleCells().map((cell) => (
                        <td key={cell.id} className="px-4 py-2">
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                        </td>
                    ))}
                    </tr>
                ))}
                </tbody>
            </table>
        </div>
    )
}