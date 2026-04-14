package com.iem.backend.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.locationtech.jts.geom.LineString;

import java.time.OffsetDateTime;
import java.util.UUID;

@Getter
@Setter
@Entity
@NoArgsConstructor
@Table(name = "trajectories")
public class Trajectory {

    @Id
    @Column(name = "id", nullable = false)
    private UUID id;

    @ManyToOne
    @JoinColumn(name = "vessel_id")
    private Vessel vesselId;

    @Column(name = "start_time", nullable = false)
    private OffsetDateTime startTime;

    @Column(name = "end_time", nullable = false)
    private OffsetDateTime endTime;

    @Column(name = "duration_minutes")
    private Double durationMinutes;

    @Column(name = "point_count", nullable = false)
    private Integer pointCount;

    @Column(name = "distance_nm")
    private Double distanceNm;

    @Column(name = "avg_speed")
    private Double avgSpeed;

    @Column(name = "geom", columnDefinition = "Geometry(LineString, 4326)")
    private LineString geom;
}