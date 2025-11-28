package com.iem.backend.service;

import com.iem.backend.dto.vessel.*;
import com.iem.backend.entity.CustomUserDetails;
import com.iem.backend.entity.User;
import com.iem.backend.entity.Vessel;
import com.iem.backend.exception.*;
import com.iem.backend.exception.ApiExceptions.*;
import com.iem.backend.mapper.VesselMapper;
import com.iem.backend.repository.UserRepository;
import com.iem.backend.repository.VesselRepository;
import com.iem.backend.specifications.VesselSpecifications;
import jakarta.transaction.Transactional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;

import java.sql.Timestamp;
import java.util.*;

@Service
public class VesselService {

    private final VesselRepository vesselRepository;
    private final VesselMapper vesselMapper;
    private final UserRepository userRepository;


    public VesselService(
            VesselRepository vesselRepository,
            UserRepository userRepository,
            VesselMapper vesselMapper
    ) {
        this.vesselRepository = vesselRepository;
        this.vesselMapper = vesselMapper;
        this.userRepository = userRepository;
    }

    public boolean checkUserAccessToVessels(User user, Collection<Integer> vesselIds) {
        if ("ADMIN".equalsIgnoreCase(user.getRole().getName())) {
            return true;
        }

        if (vesselIds == null || vesselIds.isEmpty()) {
            return false;
        }

        long count = vesselRepository.countByUsers_IdAndIdIn(user.getId(), vesselIds);
        return count == vesselIds.size();
    }

    public boolean checkUserAccessToVessel(User user, Integer vesselId) {
        return checkUserAccessToVessels(user, Collections.singletonList(vesselId));
    }

    public List<Integer> getVesselIdsByUser(Integer userId) {
        return vesselRepository.findIdByUsers_Id(userId);
    }

    @Transactional
    public VesselDetails relateUserToVessel(VesselRelateRequest dto) {
        User user = userRepository.findById(dto.userId())
                .orElseThrow(() -> new ApiExceptions.NotFoundException("User not found"));

        Vessel vessel = vesselRepository.findById(dto.vesselId())
                .orElseThrow(()-> new ApiExceptions.NotFoundException("Vessel not found"));

        String roleName = user.getRole().getName();

        if ("OWNER".equalsIgnoreCase(roleName)) {
            boolean hasOwner = vessel.getUsers().stream()
                    .anyMatch(u -> "OWNER".equalsIgnoreCase(u.getRole().getName()));
            if (hasOwner) {
                throw new VesselAlreadyOwnedException();
            }
        }

        if (!vessel.getUsers().contains(user)) {
            vessel.getUsers().add(user);
            vessel.setLocked(true);
            vesselRepository.save(vessel);
        }

        return vesselMapper.toDetails(vessel);
    }

    public Page<VesselDetails> getAllVessels(
            int page, int size, String sortField, String sortDirection,
            VesselFilter filter
    ) {
        Sort sort = sortDirection.equalsIgnoreCase("desc")
                ? Sort.by(sortField).descending()
                : Sort.by(sortField).ascending();

        Pageable pageable = PageRequest.of(page, size, sort);

        List<Specification<Vessel>> specs = new ArrayList<>();

        if (filter.country() != null && !filter.country().isBlank()) {
            specs.add(VesselSpecifications.hasCountry(filter.country()));
        }

        if (filter.mid() != null) {
            specs.add(VesselSpecifications.hasMid(filter.mid()));
        }

        if (filter.mmsi() != null && !filter.mmsi().isBlank()) {
            specs.add(VesselSpecifications.mmsiEquals(filter.mmsi()));
        }

        if (filter.name() != null && !filter.name().isBlank()) {
            specs.add(VesselSpecifications.nameContains(filter.name()));
        }

        if (filter.minLength() != null) {
            specs.add(VesselSpecifications.lengthMin(filter.minLength()));
        }

        if (filter.maxLength() != null) {
            specs.add(VesselSpecifications.lengthMax(filter.maxLength()));
        }

        if (filter.minDraft() != null) {
            specs.add(VesselSpecifications.draftMin(filter.minDraft()));
        }

        if (filter.maxDraft() != null) {
            specs.add(VesselSpecifications.draftMax(filter.maxDraft()));
        }

        // Search global = name or MMSI
        if (filter.search() != null && !filter.search().isBlank()) {
            String s = filter.search();
            if (s.matches("\\d+")) {
                specs.add(VesselSpecifications.mmsiEquals(s));
            } else {
                specs.add(VesselSpecifications.nameContains(s));
            }
        }

        Specification<Vessel> finalSpec = Specification.allOf(specs);

        Page<Vessel> vesselsPage = vesselRepository.findAll(finalSpec, pageable);
        return vesselsPage.map(vesselMapper::toDetails);
    }



    public VesselDetails findById(Integer vesselId) {
        Vessel vessel = vesselRepository.findById(vesselId).
            orElseThrow(()-> new ApiExceptions.NotFoundException("Vessel not found"));
        return vesselMapper.toDetails(vessel);
    }

    public VesselDetails createVessel(VesselCreateRequest dto) {
        Vessel vessel = vesselMapper.fromCreateRequest(dto);

        vessel.setLocked(dto.locked() != null ? dto.locked() : false);
        vessel.setBaseDateTime(
                dto.baseDateTime() != null ? dto.baseDateTime() : new Timestamp(System.currentTimeMillis())
        );

        Vessel saved = vesselRepository.save(vessel);

        return vesselMapper.toDetails(saved);
    }

    public VesselDetails updateVessel(Integer vesselId, VesselUpdateRequest dto, CustomUserDetails currentUser) {
        Vessel vessel = vesselRepository.findById(vesselId).
            orElseThrow(()-> new ApiExceptions.NotFoundException("Vessel not found"));

        User user = currentUser.getUser();

        if(!"ADMIN".equalsIgnoreCase(user.getRole().getName())) {
            boolean ownVessel = this.checkUserAccessToVessel(user,vesselId);
            if (!ownVessel){
                throw new ApiExceptions.ForbiddenException("You are not allowed to update this Vessel");
            }
        }

        vesselMapper.updateEntityFromRequest(dto, vessel);
        vessel.setLastUpdate(new Timestamp(System.currentTimeMillis()));

        vesselRepository.save(vessel);

        return vesselMapper.toDetails(vessel);
    }

    public void deleteVessel(Integer id) {
        Vessel vessel = vesselRepository.findById(id).
            orElseThrow(()-> new NotFoundException(("Vessel not found with this id")));

        vesselRepository.delete(vessel);
    }

    public List<VesselDetails> getVesselsByUserId(Integer userId, CustomUserDetails currentUser) {
        if (!"ADMIN".equalsIgnoreCase(currentUser.getUser().getRole().getName())){
            if(!Objects.equals(currentUser.getUser().getId(), userId)){
                throw new ApiExceptions.ForbiddenException("You are not allowed to update this Vessel");
            }    
        }

        List<Vessel> vessels = vesselRepository.findByUsers_Id(userId);

        return vesselMapper.toDetails(vessels);
    }

    public List<Vessel> findByIds(List<Integer> ids) {
        return vesselRepository.findAllById(ids);
    }
}
