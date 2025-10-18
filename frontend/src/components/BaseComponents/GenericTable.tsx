import React, { useMemo, useState } from "react";
import { useReactTable, getCoreRowModel, ColumnDef, flexRender, SortingState, getSortedRowModel} from "@tanstack/react-table";

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
    const [sorting, setSorting] = useState<SortingState>([]);

    const table = useReactTable({
        data,
        columns,
        getCoreRowModel: getCoreRowModel(),
        state: { sorting },
        onSortingChange: setSorting,
        getSortedRowModel: getSortedRowModel(),
        manualSorting: false
    });

    return (
        <div className={`overflow-x-auto ${className}`}>
            <table className="table table-pin-rows w-full">
                <thead className="bg-gray-100">
                {table.getHeaderGroups().map((headerGroup) => (
                    <tr key={headerGroup.id}>
                    {headerGroup.headers.map((header) => (
                        <th key={header.id} className="cursor-pointer select-none" onClick={header.column.getToggleSortingHandler()}>
                            <div className="flex items-center gap-1">
                                {
                                    flexRender(
                                        header.column.columnDef.header,
                                        header.getContext()
                                    )
                                }
                                {
                                    {
                                        asc: "↑",
                                        desc: "↓"
                                    }[header.column.getIsSorted() as string] ?? null
                                }
                            </div>
                        </th>
                    ))}
                    </tr>
                ))}
                </thead>
                <tbody>
                {table.getRowModel().rows.map((row, rowIndex) => (
                    <tr
                    key={row.id}
                    >
                    {row.getVisibleCells().map((cell) => (
                        <td key={cell.id}>
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