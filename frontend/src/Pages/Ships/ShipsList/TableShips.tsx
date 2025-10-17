import React, {useEffect, useState, useMemo} from 'react';
import {useReactTable, getCoreRowModel, ColumnDef, flexRender} from '@tanstack/react-table';
import {useApi} from '../../../utils/api';
import {toast} from "react-toastify";
import {ApiError} from "../../../types";

type Vessel = {
    id: number;
    mmsi: string;
    imo: string | null;
    vesselName: string;
    callSign: string | null;
    vesselType: number | null;
    vesselTypeName: string;
    cargoType: number | null;
    cargoTypeName: string;
    length: number | null;
    width: number | null;
    draft: number | null;
    transceiverClass: string | null;
    locked: boolean;
    baseDateTime: string;
};

const TableShips: React.FC = () => {
    const [data, setData] = useState<Vessel[]>([]);
    const [totalItems, setTotalItems] = useState(0);
    const [pageIndex, setPageIndex] = useState(0);
    const [pageSize, setPageSize] = useState(50);

    const [visibleColumns] = useState<string[]>([
        'mmsi',
        'imo',
        'vesselType',
        'cargoType',
        'baseDateTime',
        'locked'
    ]);

    const allColumns = useMemo<ColumnDef<Vessel, any>[]>(() => [
        {id: 'mmsi', accessorKey: 'mmsi', header: 'MMSI'},
        {id: 'imo', accessorKey: 'imo', header: 'IMO'},
        {id: 'callSign', accessorKey: 'callSign', header: 'Call Sign'},
        {id: 'vesselType', accessorKey: 'vesselType', header: 'Vessel Type'},
        {id: 'vesselTypeName', accessorKey: 'vesselTypeName', header: 'Vessel Type Name'},
        {id: 'cargoType', accessorKey: 'cargoType', header: 'Cargo Type'},
        {id: 'cargoTypeName', accessorKey: 'cargoTypeName', header: 'Cargo Type Name'},
        {id: 'length', accessorKey: 'length', header: 'Length'},
        {id: 'width', accessorKey: 'width', header: 'Width'},
        {id: 'draft', accessorKey: 'draft', header: 'Draft'},
        {id: 'transceiverClass', accessorKey: 'transceiverClass', header: 'Transceiver Class'},
        {id: 'baseDateTime', accessorKey: 'baseDateTime', header: 'Base Date Time'},
        {id: 'locked',accessorKey: 'locked',header: 'Locked', cell : props => {
            return !props.getValue() ?
                <button className="btn btn-xs btn-primary btn-outline">Request ship</button> : null;
            }
        },
    ], []);


    const columns = useMemo(
        () => allColumns.filter(col => visibleColumns.includes(col.id as string)),
        [allColumns, visibleColumns]
    );

    const api = useApi();

    useEffect(() => {
        async function fetchData() {
            try {
                const response = await api(
                    `/api/v1/vessels?page=${pageIndex + 1}&size=${pageSize}`,
                    {method: 'GET', headers: {'Content-Type': 'application/json'}}
                );

                const cleaned = response.content.map((v: any) => ({
                    id: v.id ?? '-',
                    mmsi: v.mmsi ?? '-',
                    imo: v.imo ?? '-',
                    vesselName: v.vesselName ?? '-',
                    callSign: v.callSign ?? '-',
                    vesselType: v.vesselType && v.vesselType !== 0 ? v.vesselType : '-',
                    vesselTypeName: v.vesselTypeName ?? '-',
                    cargoType: v.cargoType && v.cargoType !== 0 ? v.cargoType : '-',
                    cargoTypeName: v.cargoTypeName ?? '-',
                    length: v.length ?? '-',
                    width: v.width ?? '-',
                    draft: v.draft ?? '-',
                    transceiverClass: v.transceiverClass ?? '-',
                    locked: v.locked ?? '-',
                    baseDateTime: v.baseDateTime
                        ? new Date(v.baseDateTime).toISOString().split('T')[0]
                        : '-',
                }));

                setData(cleaned);
                setTotalItems(response.page.totalElements);
            } catch (e) {
                if ("statusCode" in (e as any)) {
                    const err = e as ApiError;
                    toast.error(`${err.statusCode} - ${err.message}`);
                } else {
                    toast.error("Unexpected error occurred");
                }
            }
        }
        fetchData();
    }, [pageIndex, pageSize]);


    const table = useReactTable({
        data,
        columns,
        pageCount: Math.ceil(totalItems / pageSize),
        state: {pagination: {pageIndex, pageSize}},
        manualPagination: true,
        getCoreRowModel: getCoreRowModel(),
    });
    return (
        <div>
            <div className="overflow-y-auto h-126">
                <table className="table table-pin-rows ">
                    <thead>
                    {table.getHeaderGroups().map(headerGroup => (
                        <tr key={headerGroup.id}>
                            {headerGroup.headers.map(header => (
                                <th key={header.id}>
                                    {header.isPlaceholder
                                        ? null
                                        : (header.column.columnDef.header as React.ReactNode ?? '-')}
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
            <div className="flex justify-between items-center mt-4">
                <button
                    className="btn btn-sm"
                    onClick={() => setPageIndex(old => Math.max(old - 1, 0))}
                    disabled={pageIndex === 0}
                >
                    Previous
                </button>
                <span>Page {pageIndex + 1} / {Math.ceil(totalItems / pageSize)}</span>
                <button
                    className="btn btn-sm"
                    onClick={() =>
                        setPageIndex(old => Math.min(old + 1, Math.ceil(totalItems / pageSize) - 1))
                    }
                    disabled={pageIndex + 1 >= Math.ceil(totalItems / pageSize)}
                >
                    Next
                </button>
            </div>
        </div>
    );
};

export default TableShips;
