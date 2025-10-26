import React, {useEffect, useState} from 'react';
import {useEtlApi} from '../../../hooks/useEtlApi';
import {useLoading} from "../../../context/LoadingContext";
import {toast} from "react-toastify";
import CommandDropdown from "./CommandDropdown";


interface CommandParam {
    name: string;
    opts: string[];
    required: boolean;
    type: string;
    default: any;
    help: string;
}

interface Command {
    name: string;
    help: string;
    params: CommandParam[];
}


const Commands: React.FC = () => {
    const api = useEtlApi();
    const { setLoading} = useLoading();
    const [commands, setCommands] = useState<Command[]>([]);

    useEffect(() => {
        let isMounted = true;
        const fetchCommands = async () => {
            try {
                setLoading(true);
                const data = await api('/commands', {
                    method: 'GET',
                    headers: { 'Content-Type': 'application/json' }
                });
                if (!isMounted) return;

                const formattedCommands: Command[] = Object.entries(data.commands).map(([name, details]: [string, any]) => ({
                    name,
                    help: details.help,
                    params: details.params || []
                }));

                setCommands(formattedCommands);
            } catch (err: any) {
                console.error(err);
                toast.error('Failed to fetch ETL commands');
            } finally {
                if (isMounted) setLoading(false);
            }
        };

        fetchCommands();
        return () => { isMounted = false; };
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
