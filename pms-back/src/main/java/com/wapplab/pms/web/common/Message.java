package com.wapplab.pms.web.common;

public enum Message {
    SUCCESS("success"),
    ERROR("error");

    private String message;

    Message(String message) {
        this.message = message;
    }

    public String getMessage() {
        return message;
    }
}
