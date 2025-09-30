package com.iem.backend.utils;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

@Slf4j
@Component
public class ApiLogger {

    public void success(String msg) {
        log.info("[SUCCESS] {}", msg);
    }

    public void info(String msg) {
        log.info(msg);
    }

    public void error(String msg, Exception e) {
        log.error("[ERROR] {}", msg, e);
    }

    public void warn(String msg) {
        log.warn("[WARN] {}", msg);
    }

    public void debug(String msg) {
        log.debug("[DEBUG] {}", msg);
    }
}
