package com.iem.backend.service;

import com.iem.backend.dto.requestProperty.RequestPropertyDetails;
import com.iem.backend.dto.requestProperty.RequestPropertyRequest;
import com.iem.backend.entity.*;
import com.iem.backend.exception.*;
import com.iem.backend.mapper.RequestPropertyMapper;
import com.iem.backend.repository.RequestPropertyRepository;
import com.iem.backend.repository.VesselRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class RequestPropertyService {

	private final RequestPropertyRepository requestPropertyRepository;
	private final RequestPropertyMapper requestPropertyMapper;
	private final VesselRepository vesselRepository;
	private final FileUploadService fileUploadService;

	public RequestPropertyService(
			RequestPropertyRepository requestPropertyRepository,
			RequestPropertyMapper requestPropertyMapper,
			VesselRepository vesselRepository,
			FileUploadService fileUploadService
	) {
		this.requestPropertyRepository = requestPropertyRepository;
		this.requestPropertyMapper = requestPropertyMapper;
		this.vesselRepository = vesselRepository;
		this.fileUploadService = fileUploadService;
	}

	@Transactional
	public void createRequestProperty(RequestPropertyRequest dto, CustomUserDetails currentUser) {
		User user = currentUser.getUser();

		Vessel vessel = vesselRepository.findById(dto.vesselId())
				.orElseThrow(() -> new ApiExceptions.NotFoundException("Vessel not found"));

		FileUpload fileUpload = fileUploadService.getFileById(dto.fileId());

		boolean hasOwner = vessel.getUsers().stream()
				.anyMatch(u -> "OWNER".equalsIgnoreCase(u.getRole().getName()));
		if (hasOwner) {
			throw new VesselAlreadyOwnedException();
		}

		RequestProperty requestProperty = new RequestProperty();
		requestProperty.setUser(user);
		requestProperty.setVessel(vessel);
		requestProperty.setFile(fileUpload);

		requestPropertyRepository.save(requestProperty);
	}

	@Transactional(readOnly = true)
	public RequestPropertyDetails getRequestPropertyById(Integer id) {
		RequestProperty requestProperty = requestPropertyRepository.findById(id)
				.orElseThrow(() -> new ApiExceptions.NotFoundException("RequestProperty not found"));
		return requestPropertyMapper.toDetails(requestProperty);
	}

	@Transactional(readOnly = true)
	public Page<RequestPropertyDetails> getAllRequestProperty(int page, int size, String sortField, String sortDirection, String search) {
		Sort sort = sortDirection.equalsIgnoreCase("desc")
				? Sort.by(sortField).descending()
				: Sort.by(sortField).ascending();

		Pageable pageable = PageRequest.of(page, size, sort);

		Page<RequestProperty> requestPropertyPage = requestPropertyRepository.findAll(pageable);

		return requestPropertyPage.map(requestPropertyMapper::toDetails);
	}


	@Transactional
	public RequestPropertyDetails deleteRequestPropertyById(Integer id) {
		RequestProperty requestProperty = requestPropertyRepository.findById(id)
				.orElseThrow(() -> new ApiExceptions.NotFoundException("RequestProperty not found"));

		requestPropertyRepository.deleteById(id);
		fileUploadService.deleteFile(requestProperty.getFile());

		return requestPropertyMapper.toDetails(requestProperty);
	}

	@Transactional
	public RequestPropertyDetails updateRequestProperty(Integer id, RequestPropertyRequest dto) {
		RequestProperty requestProperty = requestPropertyRepository.findById(id)
				.orElseThrow(() -> new ApiExceptions.NotFoundException("RequestProperty not found"));

		FileUpload file = fileUploadService.getFileById(dto.fileId());

		Vessel vessel = vesselRepository.findById(dto.vesselId())
				.orElseThrow(() -> new ApiExceptions.NotFoundException("Vessel not found"));

		requestProperty.setFile(file);
		requestProperty.setVessel(vessel);

		RequestProperty updateRequestProperty = requestPropertyRepository.save(requestProperty);

		return requestPropertyMapper.toDetails(updateRequestProperty);
	}
}

