package com.iem.backend.entity;

import java.time.LocalDate;

import org.locationtech.jts.geom.LineString;

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
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@Entity
@NoArgsConstructor
@Table(name = "port_routes")
public class PortRoute {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(name = "route_date", nullable = false)
    private LocalDate routeDate;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "src_port_id", nullable = false)
    private Port srcPort;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "dest_port_id", nullable = false)
    private Port destPort;

    @Column(name = "ship_count")
    private Integer shipCount = 0;

    @Column(name = "avg_duration_minutes")
    private Double avgDurationMinutes;

    @Column(name = "geom", columnDefinition = "geography(LineString,4326)")
    private LineString geom;
}
