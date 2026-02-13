SELECT partman.create_parent(
    p_parent_table := 'public.position_vessel',
    p_control := 'base_date_time',
    p_interval := '1 month',
    p_start_partition := '2015-01-01',
    p_premake := 24
);

CALL partman.partition_data_proc(
    p_parent_table := 'public.position_vessel'
);

SELECT partman.run_maintenance();
