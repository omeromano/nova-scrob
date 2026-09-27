package com.archos.mediacenter.utils.scrob;

/** Explicit, credential-safe state of the Scrob connection. */
public enum ScrobConnectionState {
    UNCONFIGURED("Unconfigured"),
    CONFIGURED("Configured"),
    TESTING("Testing"),
    CONNECTED("Connected"),
    AUTHENTICATION_FAILED("Authentication failed"),
    SERVER_UNREACHABLE("Server unreachable"),
    SERVER_API_INCOMPATIBLE("Server/API incompatible");

    private final String label;

    ScrobConnectionState(String label) {
        this.label = label;
    }

    public String getLabel() {
        return label;
    }

    static ScrobConnectionState fromStored(String value) {
        if (value == null || value.trim().isEmpty()) return CONFIGURED;
        try {
            ScrobConnectionState state = valueOf(value.trim());
            // TESTING is deliberately transient and must not survive a process restart.
            return state == TESTING ? CONFIGURED : state;
        } catch (IllegalArgumentException ignored) {
            return CONFIGURED;
        }
    }
}
