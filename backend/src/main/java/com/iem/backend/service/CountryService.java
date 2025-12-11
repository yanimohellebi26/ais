package com.iem.backend.service;

import com.iem.backend.dto.country.CountryMidDetails;
import com.iem.backend.mapper.CountryMapper;
import com.iem.backend.repository.MidRepository;
import org.springframework.stereotype.Service;

import java.util.List;


@Service
public class CountryService {

    private final MidRepository midRepository;
    private final CountryMapper countryMapper;

    public CountryService(MidRepository midRepository, CountryMapper countryMapper) {
        this.midRepository = midRepository;
        this.countryMapper = countryMapper;
    }

    public List<CountryMidDetails> getCountriesWithMid() {
        return countryMapper.toMidDetails(midRepository.findAll());
    }
}


