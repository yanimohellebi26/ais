package com.iem.backend.service;

import com.iem.backend.dto.RequestPropertyDto;
import com.iem.backend.dto.UpdateRequestPropertyDto;
import com.iem.backend.entity.*;
import com.iem.backend.exception.*;
import com.iem.backend.repository.FileUploadRepository;
import com.iem.backend.repository.RequestPropertyRepository;
import com.iem.backend.repository.UserRepository;
import com.iem.backend.repository.VesselRepository;
import jakarta.transaction.Transactional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;



@Service
public class RequestPropertyService {

    private final VesselRepository vesselRepository;
    private final UserRepository userRepository;
    private final FileUploadRepository fileUploadRepository;
    private final RequestPropertyRepository requestPropertyRepository;

    public RequestPropertyService(VesselRepository vesselRepository, UserRepository userRepository, RequestPropertyRepository requestPropertyRepository, FileUploadRepository fileUploadRepository) {
        this.vesselRepository = vesselRepository;
        this.userRepository = userRepository;
        this.requestPropertyRepository = requestPropertyRepository;
        this.fileUploadRepository = fileUploadRepository;
    }

    @Transactional
    public void postRequestProperty(Integer userId, String mmsi, Integer fileId) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new UserNotFoundException(userId));

        Vessel vessel = vesselRepository.findByMmsi(mmsi)
                .orElseThrow(() -> new VesselNotFoundException());

        FileUpload fileUpload = fileUploadRepository.findById(fileId).orElseThrow(() -> new FileNotFoundException());

        RequestProperty requestProperty = new RequestProperty();
        requestProperty.setUser(user);
        requestProperty.setVessel(vessel);
        requestProperty.setFile(fileUpload);

        boolean hasOwner = vessel.getUsers().stream().anyMatch(u -> "OWNER".equalsIgnoreCase(u.getRole().getName()));
        if (hasOwner) {
            throw new VesselAlreadyOwnedException();
        }

        requestPropertyRepository.save(requestProperty);
    }

    public RequestPropertyDto getRequestPropertyById(Integer id) {
        RequestProperty requestProperty = requestPropertyRepository.findById(id).orElseThrow(()-> new RequestPropertyNotFoundException());
        RequestPropertyDto responseDto = new RequestPropertyDto(
                requestProperty.getId(),
                requestProperty.getUser().getId(),
                requestProperty.getVessel().getMmsi(),
                requestProperty.getFile().getId(),
                requestProperty.getCreatedAt()
        );
        return responseDto;

    }

    public Page<RequestPropertyDto> getAllRequestProperty(int page, int size, String sortField, String sortDirection, String search) {
        Sort sort = sortDirection.equalsIgnoreCase("desc")
                ? Sort.by(sortField).descending()
                : Sort.by(sortField).ascending();

        Pageable pageable = PageRequest.of(page, size, sort);

        Page<RequestProperty> requestPropertyPage;

        requestPropertyPage = requestPropertyRepository.findAll(pageable);

        return requestPropertyPage.map(RequestPropertyDto::fromEntity);
    }

    @Transactional
    public RequestPropertyDto deleteRequestPropertyById(Integer id) {
        RequestProperty requestProperty = requestPropertyRepository.findById(id).orElseThrow(()-> new RequestPropertyNotFoundException());
        RequestPropertyDto responseDto = new RequestPropertyDto(
                requestProperty.getId(),
                requestProperty.getUser().getId(),
                requestProperty.getVessel().getMmsi(),
                requestProperty.getFile().getId(),
                requestProperty.getCreatedAt()
        );
        requestPropertyRepository.deleteById(id);
        fileUploadRepository.deleteById(requestProperty.getFile().getId());
        return responseDto;
    }

    @Transactional
    public RequestPropertyDto updateRequestProperty(UpdateRequestPropertyDto dto) {
        RequestProperty requestProperty = requestPropertyRepository.findById(dto.id())
                .orElseThrow(() -> new RequestPropertyNotFoundException());

        if (dto.fileid() != null) {
            FileUpload file = fileUploadRepository.findById(dto.fileid()).orElseThrow(()-> new FileNotFoundException());
            requestProperty.setFile(file);
        }

        if (dto.mmsi() != null && !dto.mmsi().isBlank()) {
            Vessel vessel = vesselRepository.findByMmsi(dto.mmsi()).orElseThrow(() -> new VesselNotFoundException(dto.mmsi()));
            requestProperty.setVessel(vessel);
        }

        if (dto.userid() != null) {
            User user = userRepository.findById(dto.userid()).orElseThrow(() -> new UserNotFoundException(dto.userid()));
            requestProperty.setUser(user);
        }

        RequestProperty updateRequestProperty = requestPropertyRepository.save(requestProperty);

        return new RequestPropertyDto(
                updateRequestProperty.getId(),
                updateRequestProperty.getUser().getId(),
                updateRequestProperty.getVessel().getMmsi(),
                updateRequestProperty.getFile().getId(),
                updateRequestProperty.getCreatedAt()
        );
    }



}
