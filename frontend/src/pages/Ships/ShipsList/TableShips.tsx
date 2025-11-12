import React, { useEffect, useMemo, useState } from "react";
import { useReactTable, getCoreRowModel, ColumnDef } from "@tanstack/react-table";
import { useApi } from "../../../hooks/useApi";
import { toast } from "react-toastify";
import { ApiError } from "../../../types";
import TableControls from "./TableControls";
import TableDisplay from "./TableDisplay";
import TablePagination from "./TablePagination";
import RequestModal from "./RequestModal";
import { Vessel } from "./types";
import {useCurrentUser} from "../../../hooks/useCurrentUser";
import {useLoading} from "../../../context/LoadingContext";

const TableShips: React.FC = () => {
    const [data, setData] = useState<Vessel[]>([]);
    const {setLoading} = useLoading();
    const [totalItems, setTotalItems] = useState(0);
    const [pageIndex, setPageIndex] = useState(0);
    const [pageSize, setPageSize] = useState(50);

    const [visibleColumns, setVisibleColumns] = useState<string[]>([
        'mmsi',
        'imo',
        'vesselName',
        'vesselType',
        'cargoType',
        'baseDateTime',
        'locked'
    ]);

    const [searchTerm, setSearchTerm] = useState('');
    const [sortColumn, setSortColumn] = useState<string>('mmsi');
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [selectedVessel, setSelectedVessel] = useState<Vessel | null>(null);

    const api = useApi();

    const handleRequestClick = (vessel: Vessel) => {
        setSelectedVessel(vessel);
        setIsModalOpen(true);
    };

    const allColumns = useMemo<ColumnDef<Vessel, any>[]>(() => [
        { id: 'mmsi', accessorKey: 'mmsi', header: 'MMSI' },
        { id: 'imo', accessorKey: 'imo', header: 'IMO' },
        { id: 'vesselName', accessorKey: 'vesselName', header: 'Name' },
        { id: 'vesselType', accessorKey: 'vesselType', header: 'Vessel Type' },
        { id: 'vesselTypeName', accessorKey: 'vesselTypeName', header: 'Vessel Type Name' },
        { id: 'cargoType', accessorKey: 'cargoType', header: 'Cargo Type' },
        { id: 'cargoTypeName', accessorKey: 'cargoTypeName', header: 'Cargo Type Name' },
        { id: 'length', accessorKey: 'length', header: 'Length' },
        { id: 'width', accessorKey: 'width', header: 'Width' },
        { id: 'draft', accessorKey: 'draft', header: 'Draft' },
        { id: 'transceiverClass', accessorKey: 'transceiverClass', header: 'Transceiver Class' },
        { id: 'baseDateTime', accessorKey: 'baseDateTime', header: 'Base Date Time' },
        {
            id: 'locked',
            accessorKey: 'locked',
            header: 'Locked',
            cell: props => {
                const vessel = props.row.original;
                return !props.getValue() ? (
                    <button className="btn btn-xs btn-primary btn-outline" onClick={() => handleRequestClick(vessel)}>Request</button>
                ) : null;
            }
        },
    ], []);

    const columns = useMemo(
        () => allColumns.filter(col => visibleColumns.includes(col.id as string)),
        [allColumns, visibleColumns]
    );

    useEffect(() => {
        async function fetchData() {
            try {

                setLoading(true);
                const query = new URLSearchParams({
                    page: (pageIndex).toString(),
                    size: pageSize.toString(),
                    search: searchTerm,
                    sort: `${sortColumn},${sortOrder}`,
                });

                const response = await api(`/api/v1/vessels?${query.toString()}`, {
                    method: 'GET',
                    headers: { 'Content-Type': 'application/json' }
                });

                const cleaned = (response.content || []).map((v: any) => ({
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
                    locked: v.locked ?? false,
                    baseDateTime: v.baseDateTime
                        ? new Date(v.baseDateTime).toISOString().split('T')[0]
                        : '-',
                })) as Vessel[];

                setData(cleaned);
                setTotalItems(response.page?.totalElements ?? 0);
            } catch (e) {
                if ("statusCode" in (e as any)) {
                    const err = e as ApiError;
                    toast.error(`${err.statusCode} - ${err.message}`);
                } else {
                    toast.error("Unexpected error occurred");
                }
            } finally {
                setLoading(false);
            }
        }

        fetchData();
    }, [pageIndex, pageSize, searchTerm, sortColumn, sortOrder]);

    const table = useReactTable({
        data,
        columns,
        pageCount: Math.ceil(totalItems / pageSize),
        state: { pagination: { pageIndex, pageSize } },
        manualPagination: true,
        getCoreRowModel: getCoreRowModel(),
    });

    const toggleColumn = (colId: string) => {
        setVisibleColumns(prev =>
            prev.includes(colId) ? prev.filter(c => c !== colId) : [...prev, colId]
        );
    };

    const toggleSort = (col: string) => {
        if (col === sortColumn) setSortOrder(prev => (prev === 'asc' ? 'desc' : 'asc'));
        else {
            setSortColumn(col);
            setSortOrder('asc');
        }
    };

    return (
        <div>
            <h1 className="text-2xl font-semibold mb-4">All ships available</h1>

            <TableControls
                searchTerm={searchTerm}
                setSearchTerm={setSearchTerm}
                allColumns={allColumns.map(c => ({
                    id: c.id,
                    header: typeof c.header === 'string' ? c.header : '-'
                }))}
                visibleColumns={visibleColumns}
                toggleColumn={toggleColumn}
            />

            <TableDisplay
                table={table}
                sortColumn={sortColumn}
                sortOrder={sortOrder}
                toggleSort={toggleSort}
            />

            <TablePagination
                pageIndex={pageIndex}
                totalItems={totalItems}
                pageSize={pageSize}
                setPageIndex={setPageIndex}
            />
            {isModalOpen && selectedVessel && (
                <RequestModal
                    vessel={selectedVessel}
                    onClose={() => setIsModalOpen(false)}
                />
            )}
        </div>
    );
};

export default TableShips;
