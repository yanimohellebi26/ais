import React, {useEffect, useState} from 'react';
import {useEtlApi} from '../../../hooks/useEtlApi';
import {useLoading} from "../../../context/LoadingContext";
import {toast} from "react-toastify";
import CommandDropdown from "./CommandDropdown";
import {Command} from "./interfaces";

const Commands: React.FC = () => {
    const api = useEtlApi();
    const { setLoading} = useLoading();
    const [commands, setCommands] = useState<Command[]>([]);

    useEffect(() => {
        const fetchCommands = async () => {
            try {
                setLoading(true);
                const data = await api('/commands/', {
                    method: 'GET',
                    headers: { 'Content-Type': 'application/json' }
                });

                const formattedCommands: Command[] = Object.entries(data.commands).map(([name, details]: [string, any]) => ({
                    name,
                    help: details.help,
                    params: details.params || []
                }));

                setCommands(formattedCommands);
            } catch (err: any) {
                toast.error('Failed to fetch ETL commands');
            } finally {
                setLoading(false);
            }
        };

        fetchCommands();
    }, []);


    return (
        <div className='rounded-2xl shadow-sm bg-base-100 p-4 border-accent space-y-2'>
            <div className='flex flex-col justify-center'>
                <h1 className='text-xl font-semibold mr-4'>Available ETL Commands</h1>
                <p className='text-base-content/70 mb-4' >Script commands available in ETL Worker for execution</p>
            </div>
            {commands.map((command, index) => (
                <CommandDropdown key={index} command={command} index={index} />
            ))}
        </div>
    );
};

export default Commands;
