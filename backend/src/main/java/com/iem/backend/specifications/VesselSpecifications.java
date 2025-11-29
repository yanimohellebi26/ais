package com.iem.backend.specifications;

import com.iem.backend.entity.Vessel;
import org.springframework.data.jpa.domain.Specification;

public class VesselSpecifications {

    public static Specification<Vessel> hasCountry(String country) {
        return (root, query, cb) ->
                cb.equal(cb.lower(root.get("mid").get("country").get("name")), country.toLowerCase());
    }

    public static Specification<Vessel> hasMid(Integer mid) {
        return (root, query, cb) ->
                cb.equal(root.get("mid").get("mid"), mid);
    }

    public static Specification<Vessel> nameContains(String name) {
        return (root, query, cb) ->
                cb.like(cb.lower(root.get("vesselName")), "%" + name.toLowerCase() + "%");
    }

    public static Specification<Vessel> mmsiEquals(String mmsi) {
        return (root, query, cb) ->
                cb.equal(root.get("mmsi"), mmsi);
    }

    public static Specification<Vessel> lengthMin(Double min) {
        return (root, query, cb) ->
                cb.greaterThanOrEqualTo(root.get("length"), min);
    }

    public static Specification<Vessel> lengthMax(Double max) {
        return (root, query, cb) ->
                cb.lessThanOrEqualTo(root.get("length"), max);
    }

    public static Specification<Vessel> widthMin(Double min) {
        return (root, query, cb) ->
                cb.greaterThanOrEqualTo(root.get("width"), min);
    }

    public static Specification<Vessel> widthMax(Double max) {
        return (root, query, cb) ->
                cb.lessThanOrEqualTo(root.get("width"), max);
    }

    public static Specification<Vessel> draftMin(Double min) {
        return (root, query, cb) ->
                cb.greaterThanOrEqualTo(root.get("draft"), min);
    }

    public static Specification<Vessel> draftMax(Double max) {
        return (root, query, cb) ->
                cb.lessThanOrEqualTo(root.get("draft"), max);
    }
}


