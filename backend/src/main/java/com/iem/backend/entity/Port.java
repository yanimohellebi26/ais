package com.iem.backend.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.locationtech.jts.geom.Point;

@Getter
@Setter
@NoArgsConstructor
@Entity
@Table(name = "port")
public class Port {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(length = 5, nullable = false, unique = true)
    private String code;

    private String name;

    @Column(name = "geom", nullable = false, columnDefinition = "geography(Point, 4326)")
    private Point geom;

    @ManyToOne
    @JoinColumn(name = "country_code")
    private Country country;
}

