package com.iem.backend.controller;

import com.iem.backend.utils.ApiLogger;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Slf4j
public class HelloController {

    @GetMapping("/api/HelloWorld")
    @PreAuthorize("hasRole('ADMIN')")
    public String helloWorld() {
        log.info("Hello World");

        return "Hello World from SeaSight backend";
    }
}
