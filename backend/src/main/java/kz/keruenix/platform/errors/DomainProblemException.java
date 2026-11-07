package kz.keruenix.platform.errors;

import java.util.Objects;

/**
 * A typed, expected domain rejection. Do not include PII or SQL in its message.
 * The owning domain module validates tenancy, state and resource scope before throwing.
 */
public final class DomainProblemException extends RuntimeException {
    private final ErrorCode errorCode;

    public DomainProblemException(ErrorCode errorCode) {
        super(Objects.requireNonNull(errorCode).code());
        this.errorCode = errorCode;
    }

    public ErrorCode errorCode() {
        return errorCode;
    }
}
