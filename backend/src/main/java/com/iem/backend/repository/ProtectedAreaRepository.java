package com.iem.backend.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import com.iem.backend.entity.ProtectedArea;

public interface ProtectedAreaRepository extends JpaRepository<ProtectedArea, String> {
    
    @Query(value = """
        SELECT json_build_object(
            'type', 'FeatureCollection',
            'features', COALESCE(json_agg(
                json_build_object(
                    'type', 'Feature',
                    'id', pa.site_pid,
                    'geometry', ST_AsGeoJSON(pa.geometry)::json,
                    'properties', json_build_object(
                        'name', pi.name,
                        'site_type', pi.site_type,
                        'desig_eng', pa.desig_eng,
                        'desig_type', pa.desig_type,
                        'iucn_cat', pa.iucn_cat,
                        'realm', pa.realm,
                        'no_take', pa.no_take,
                        'status', pi.status,
                        'status_yr', pi.status_yr,
                        'iso3', pi.iso3
                    )
                )
            ), '[]'::json)
        )::text
        FROM protected_area pa
        JOIN pa_infos pi ON pa.site_id = pi.site_id
        WHERE pa.geometry && ST_MakeEnvelope(:xmin, :ymin, :xmax, :ymax, 4326)
        """, nativeQuery = true)
    String findProtectedAreaInBboxAsGeoJson(
        @Param("xmin") double xmin,
        @Param("ymin") double ymin,
        @Param("xmax") double xmax,
        @Param("ymax") double ymax
    );
}
