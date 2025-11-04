package com.iem.backend.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.sql.Timestamp;
import org.locationtech.jts.geom.Point;

@Getter
@Setter
@Entity
@NoArgsConstructor
@Table(name = "position_vessel")
public class PositionVessel {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "vessel_id", nullable = false)
    private Integer vesselId;

    @Column(name = "base_date_time", nullable = false)
    private Timestamp baseDateTime;

    @Column(name = "sog")
    private Double sog;

    @Column(name = "cog")
    private Double cog;

    @Column(name = "heading")
    private Short heading;

    @ManyToOne
    @JoinColumn(name = "status_id")
    private VesselStatus status;

    @Column(name = "geom", nullable = false, columnDefinition = "geography(Point, 4326)")
    private Point geom;

    @ManyToOne
    @JoinColumn(name = "vessel_id", insertable = false, updatable = false)
    private Vessel vessel;
}