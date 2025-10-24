package com.iem.backend.entity;

import java.time.LocalDateTime;

import org.locationtech.jts.geom.Point;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@Entity
@Table(name = "position_vessel")
public class PositionVessel {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "vessel_id")
    private Integer vesselId;

    @Column(name = "base_date_time")
    private LocalDateTime baseDateTime;
    
    @Column(name = "sog")
    private Double sog;

    @Column(name = "cog")
    private Double cog;

    @Column(name = "heading")
    private Short heading;
    
    @Column(name = "status_id")
    private Integer statusId;

    @Column(columnDefinition = "geography(Point, 4326)")
    private Point geom;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "vessel_id", insertable = false, updatable = false)
    private Vessel vessel;
}
