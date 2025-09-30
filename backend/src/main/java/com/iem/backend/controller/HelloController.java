package com.iem.backend.controller;

import com.iem.backend.utils.ApiLogger;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HelloController {

    private final ApiLogger apiLogger;

    public HelloController(ApiLogger apiLogger) {
        this.apiLogger = apiLogger;
    }

    @GetMapping("/api/HelloWorld")
    public String helloWorld() {
        apiLogger.success("Hello World");

        return "Hello World from SeaSight backend";
    }
}
