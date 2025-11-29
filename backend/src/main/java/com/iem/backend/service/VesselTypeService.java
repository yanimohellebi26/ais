package com.iem.backend.service;

import com.iem.backend.dto.vesselType.VesselTypeDetails;
import com.iem.backend.entity.VesselType;
import com.iem.backend.mapper.VesselTypeMapper;
import com.iem.backend.repository.VesselTypeRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class VesselTypeService {

    private final VesselTypeRepository vesselTypeRepository;
    private final VesselTypeMapper vesselTypeMapper;

    public VesselTypeService(VesselTypeRepository vesselTypeRepository, VesselTypeMapper vesselTypeMapper) {
        this.vesselTypeRepository = vesselTypeRepository;
        this.vesselTypeMapper = vesselTypeMapper;
    }

    public List<VesselTypeDetails> getAll() {
        List<VesselType> vesselTypes = vesselTypeRepository.findAll();
        return vesselTypeMapper.toDetails(vesselTypes);
    }

}
