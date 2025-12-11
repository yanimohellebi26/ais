package com.iem.backend.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table(name = "mid")
@Getter
@Setter
@NoArgsConstructor
public class Mid {

    @Id
    private Integer mid;

    @ManyToOne
    @JoinColumn(name = "country_id", nullable = false)
    private Country country;
}
