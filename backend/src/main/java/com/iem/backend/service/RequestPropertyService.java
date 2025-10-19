package com.iem.backend.service;

import com.iem.backend.entity.FileUpload;
import com.iem.backend.entity.RequestProperty;
import com.iem.backend.entity.User;
import com.iem.backend.entity.Vessel;
import com.iem.backend.exception.FileNotFoundException;
import com.iem.backend.exception.UserNotFoundException;
import com.iem.backend.exception.VesselAlreadyOwnedException;
import com.iem.backend.exception.VesselNotFoundException;
import com.iem.backend.repository.FileUploadRepository;
import com.iem.backend.repository.RequestPropertyRepository;
import com.iem.backend.repository.UserRepository;
import com.iem.backend.repository.VesselRepository;
import jakarta.transaction.Transactional;
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

        if (!vessel.getUsers().contains(user)) {
            requestPropertyRepository.save(requestProperty);
        }
    }
}
