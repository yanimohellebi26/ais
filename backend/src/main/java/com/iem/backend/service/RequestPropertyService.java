package com.iem.backend.service;

import com.iem.backend.dto.RequestPropertyAdminDto;
import com.iem.backend.dto.UpdateRequestPropertyDto;
import com.iem.backend.entity.FileUpload;
import com.iem.backend.entity.RequestProperty;
import com.iem.backend.entity.User;
import com.iem.backend.entity.Vessel;
import com.iem.backend.exception.RequestPropertyNotFoundException;
import com.iem.backend.exception.UserNotFoundException;
import com.iem.backend.exception.VesselAlreadyOwnedException;
import com.iem.backend.exception.VesselNotFoundException;
import com.iem.backend.repository.RequestPropertyRepository;
import com.iem.backend.repository.UserRepository;
import com.iem.backend.repository.VesselRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class RequestPropertyService {

	private final VesselRepository vesselRepository;
	private final UserRepository userRepository;
	private final RequestPropertyRepository requestPropertyRepository;
	private final FileUploadService fileUploadService;

	public RequestPropertyService(
			VesselRepository vesselRepository,
			UserRepository userRepository,
			RequestPropertyRepository requestPropertyRepository,
			FileUploadService fileUploadService
	) {
		this.vesselRepository = vesselRepository;
		this.userRepository = userRepository;
		this.requestPropertyRepository = requestPropertyRepository;
		this.fileUploadService = fileUploadService;
	}

	@Transactional
	public void postRequestProperty(Integer userId, String mmsi, Integer fileId) {
		User user = userRepository.findById(userId)
				.orElseThrow(() -> new UserNotFoundException(userId));

		Vessel vessel = vesselRepository.findByMmsi(mmsi)
				.orElseThrow(VesselNotFoundException::new);

		FileUpload fileUpload = fileUploadService.getFileEntity(fileId);

		RequestProperty requestProperty = new RequestProperty();
		requestProperty.setUser(user);
		requestProperty.setVessel(vessel);
		requestProperty.setFile(fileUpload);

		boolean hasOwner = vessel.getUsers().stream()
				.anyMatch(u -> "OWNER".equalsIgnoreCase(u.getRole().getName()));
		if (hasOwner) {
			throw new VesselAlreadyOwnedException();
		}

		requestPropertyRepository.save(requestProperty);
	}

	@Transactional(readOnly = true)
	public RequestPropertyAdminDto getRequestPropertyById(Integer id) {
		RequestProperty requestProperty = requestPropertyRepository.findById(id)
				.orElseThrow(RequestPropertyNotFoundException::new);
		return RequestPropertyAdminDto.fromEntity(requestProperty);
	}

	@Transactional(readOnly = true)
	public Page<RequestPropertyAdminDto> getAllRequestProperty(int page, int size, String sortField, String sortDirection, String search) {
		Sort sort = sortDirection.equalsIgnoreCase("desc")
				? Sort.by(sortField).descending()
				: Sort.by(sortField).ascending();

		Pageable pageable = PageRequest.of(page, size, sort);

		Page<RequestProperty> requestPropertyPage = requestPropertyRepository.findAll(pageable);

		return requestPropertyPage.map(RequestPropertyAdminDto::fromEntity);
	}

	@Transactional
	public RequestPropertyAdminDto deleteRequestPropertyById(Integer id) {
		RequestProperty requestProperty = requestPropertyRepository.findById(id)
				.orElseThrow(RequestPropertyNotFoundException::new);

		RequestPropertyAdminDto responseDto = RequestPropertyAdminDto.fromEntity(requestProperty);

		requestPropertyRepository.deleteById(id);
		fileUploadService.deleteFile(requestProperty.getFile());

		return responseDto;
	}

	@Transactional
	public RequestPropertyAdminDto updateRequestProperty(UpdateRequestPropertyDto dto) {
		RequestProperty requestProperty = requestPropertyRepository.findById(dto.id())
				.orElseThrow(RequestPropertyNotFoundException::new);

		if (dto.fileid() != null) {
			FileUpload file = fileUploadService.getFileEntity(dto.fileid());
			requestProperty.setFile(file);
		}

		if (dto.mmsi() != null && !dto.mmsi().isBlank()) {
			Vessel vessel = vesselRepository.findByMmsi(dto.mmsi())
					.orElseThrow(() -> new VesselNotFoundException(dto.mmsi()));
			requestProperty.setVessel(vessel);
		}

		if (dto.userid() != null) {
			User user = userRepository.findById(dto.userid())
					.orElseThrow(() -> new UserNotFoundException(dto.userid()));
			requestProperty.setUser(user);
		}

		RequestProperty updateRequestProperty = requestPropertyRepository.save(requestProperty);

		return RequestPropertyAdminDto.fromEntity(updateRequestProperty);
	}
}

