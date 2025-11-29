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
import jakarta.transaction.Transactional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;

import java.sql.Timestamp;
import java.util.Collection;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

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

    @Transactional
    public void unrelate(VesselRelateRequest dto, CustomUserDetails currentUser) {
        if(!checkUserAccessToVessel(currentUser.getUser(),dto.vesselId())) {
            throw new ForbiddenException("Not allowed to access this vessel");
        }

        User captain = userRepository.findById(dto.userId()).orElseThrow(() -> new ApiExceptions.NotFoundException("User not found"));
        String roleName = captain.getRole().getName();

        Vessel vessel = vesselRepository.findById(dto.vesselId()).orElseThrow(() -> new ApiExceptions.NotFoundException("Vessel not found"));

        if ("CAPTAIN".equalsIgnoreCase(roleName) && vessel.getUsers().contains(captain)){
            vessel.getUsers().remove(captain);
            vesselRepository.save(vessel);
        }
        else {
            throw new ApiExceptions.BadRequestException("Not allowed to unrelate this user from this vessel or relation does not exist");
        }
    }

    public Page<VesselDetails> getAllVessels(int page, int size, String sortField, String sortDirection, String search) {
        Sort sort = sortDirection.equalsIgnoreCase("desc")
                ? Sort.by(sortField).descending()
                : Sort.by(sortField).ascending();

        Pageable pageable = PageRequest.of(page, size, sort);

        Page<Vessel> vesselsPage;

        if (search == null || search.isEmpty()) {
            vesselsPage = vesselRepository.findAll(pageable);
        } else if (search.matches("\\d+")) {
            vesselsPage = vesselRepository.searchByMmsiOrVesselName(search, pageable);
        } else {
            vesselsPage = vesselRepository.findByVesselNameContainingIgnoreCase(search, pageable);
        }

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

    public List<VesselUsersDetails> getVesselsByUserId(Integer userId, CustomUserDetails currentUser) {
        if (!"ADMIN".equalsIgnoreCase(currentUser.getUser().getRole().getName())){
            if(!Objects.equals(currentUser.getUser().getId(), userId)){
                throw new ApiExceptions.ForbiddenException("You are not allowed to get this Vessel details");
            }    
        }

        List<Vessel> vessels = vesselRepository.findByUsers_Id(userId);

        return vesselMapper.toUsersDetails(vessels);
    }

    public List<Vessel> findByIds(List<Integer> ids) {
        return vesselRepository.findAllById(ids);
    }
}
