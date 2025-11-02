package com.iem.backend.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.sql.Timestamp;
import java.util.ArrayList;
import java.util.List;

@Getter
@Setter
@NoArgsConstructor
@Entity
@Table(name = "vessel")
public class Vessel {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(length = 9, nullable = false, unique = true)
    private String mmsi;

    @Column(length = 20, unique = true)
    private String imo;

    @Column(name = "vessel_name", length = 100)
    private String vesselName;

    @Column(name = "call_sign", length = 20)
    private String callSign;

    @ManyToOne
    @JoinColumn(name="vessel_type_id")
    private VesselType vesselType;

    @ManyToOne
    @JoinColumn(name = "cargo_type_id")
    private VesselType cargoType;

    private Double length;
    private Double width;
    private Double draft;

    @Enumerated(EnumType.STRING)
    private TransceiverClass transceiverClass;

    private boolean locked = false;

    @Column(nullable = false, updatable = false)
    private Timestamp createdAt;

    private Timestamp lastUpdate;

    @Column(nullable = false)
    private Timestamp baseDateTime;

    @ManyToMany
    @JoinTable(
            name = "user_vessel",
            joinColumns = @JoinColumn(name = "vessel_id"),
            inverseJoinColumns = @JoinColumn(name = "user_id")
    )
    @JsonIgnore
    private List<User> users = new ArrayList<>();


}

