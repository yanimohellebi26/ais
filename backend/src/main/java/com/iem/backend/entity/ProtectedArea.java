package com.iem.backend.entity;

import org.locationtech.jts.geom.Geometry;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.Setter;

@Entity
@Table(name = "protected_area")
@Getter
@Setter
public class ProtectedArea {
    @Id
    @Column(name = "site_pid", length = 50)
    private String sitePid;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "site_id", nullable = false)
    private PaInfos paInfos;

    @Column(name = "desig_eng")
    private String desigEng;

    @Column(name = "desig_type", length = 50)
    private String desigType;

    @Column(name = "iucn_cat", length = 50)
    private String iucnCat;

    @Column(name = "realm", length = 50)
    private String realm;

    @Column(name = "no_take", length = 50)
    private String noTake;

    @Column(name = "no_tk_area")
    private Double noTkArea;

    @Column(name = "rep_area")
    private Double repArea;

    @Column(name = "gis_area")
    private Double gisArea;

    @Column(name = "rep_m_area")
    private Double repMArea;

    @Column(name = "gis_m_area")
    private Double gisMArea;

    @Column(name = "own_type", length = 100)
    private String ownType;

    @Column(name = "geometry", nullable = false, columnDefinition = "Geometry(Geometry, 4326)")
    private Geometry geometry;
}
