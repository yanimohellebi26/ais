package com.iem.backend.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.Setter;

@Entity
@Table(name = "pa_infos")
@Getter
@Setter
public class PaInfos {
    @Id
    @Column(name = "site_id")
    private Integer siteId;

    @Column(name = "name")
    private String name;

    @Column(name = "site_type", length = 10)
    private String siteType;

    @Column(name = "iso3", length = 50)
    private String iso3;

    @Column(name = "status", length = 50)
    private String status;

    @Column(name = "status_yr")
    private Integer statusYr;
}
