package com.iem.backend.controller;

import com.iem.backend.dto.country.CountryMidDetails;
import com.iem.backend.service.CountryService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/v1/country")
public class CountryController {

    private final CountryService countryService;

    public CountryController(CountryService countryService) {
        this.countryService = countryService;
    }

    @GetMapping
    public ResponseEntity<List<CountryMidDetails>> getCountries() {
        return ResponseEntity.ok(countryService.getCountriesWithMid());
    }
}

