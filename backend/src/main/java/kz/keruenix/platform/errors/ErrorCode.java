package kz.keruenix.platform.errors;

import org.springframework.http.HttpStatus;

/**
 * Public, append-only error identifiers. Never use exception messages as API codes.
 * Keep this list synchronized with docs/contracts/api-error-catalog.v1.json.
 */
public enum ErrorCode {
    BAD_REQUEST("KX-GEN-400-001", HttpStatus.BAD_REQUEST, "Malformed request",
        "The request could not be parsed or validated.", false),
    VALIDATION_FAILED("KX-GEN-400-002", HttpStatus.BAD_REQUEST, "Validation failed",
        "One or more request fields are invalid.", false),
    FRAMEWORK_HTTP_ERROR("KX-GEN-000-001", HttpStatus.BAD_REQUEST, "HTTP request rejected",
        "The request could not be completed using the supplied HTTP parameters.", false),
    AUTHENTICATION_REQUIRED("KX-AUTH-401-001", HttpStatus.UNAUTHORIZED, "Authentication required",
        "Valid authentication is required to access this resource.", false),
    PERMISSION_DENIED("KX-AUTH-403-001", HttpStatus.FORBIDDEN, "Permission denied",
        "You do not have permission to perform this operation.", false),
    RESOURCE_HIDDEN("KX-AUTH-404-001", HttpStatus.NOT_FOUND, "Resource not found",
        "The requested resource was not found.", false),
    RESOURCE_NOT_FOUND("KX-GEN-404-001", HttpStatus.NOT_FOUND, "Resource not found",
        "The requested resource was not found.", false),
    METHOD_NOT_ALLOWED("KX-GEN-405-001", HttpStatus.METHOD_NOT_ALLOWED, "Method not allowed",
        "This HTTP method is not supported for the resource.", false),
    UNSUPPORTED_MEDIA_TYPE("KX-GEN-415-001", HttpStatus.UNSUPPORTED_MEDIA_TYPE, "Unsupported media type",
        "The submitted content type is not supported.", false),
    STALE_VERSION("KX-GEN-409-001", HttpStatus.CONFLICT, "Version conflict",
        "The resource has changed. Reload and retry the operation.", false),
    IDEMPOTENCY_CONFLICT("KX-GEN-409-002", HttpStatus.CONFLICT, "Idempotency conflict",
        "The idempotency key was used with a different request.", false),
    INVALID_TRANSITION("KX-DOM-409-001", HttpStatus.CONFLICT, "Invalid state transition",
        "The requested action is not permitted in the current state.", false),
    QUOTE_EXPIRED("KX-COM-409-001", HttpStatus.CONFLICT, "Quote expired",
        "The selected quotation version is no longer effective.", false),
    SIGNATORY_REQUIRED("KX-COM-403-001", HttpStatus.FORBIDDEN, "Signatory authority required",
        "Verified authority to accept the quotation is required.", false),
    CAPACITY_CONFLICT("KX-FLT-409-001", HttpStatus.CONFLICT, "Capacity conflict",
        "The selected resource is unavailable for the requested interval.", false),
    CUSTODY_EVIDENCE_REQUIRED("KX-EXE-422-001", HttpStatus.UNPROCESSABLE_ENTITY, "Custody evidence required",
        "Verified cargo handover evidence is required.", false),
    PARTIAL_DELIVERY_CONFLICT("KX-EXE-409-001", HttpStatus.CONFLICT, "Partial delivery conflict",
        "The delivered and remaining cargo quantities are inconsistent.", false),
    SETTLEMENT_EVIDENCE_REQUIRED("KX-FIN-422-001", HttpStatus.UNPROCESSABLE_ENTITY, "Settlement evidence required",
        "Verified payment settlement evidence is required.", false),
    SUBSCRIPTION_RESTRICTED("KX-SAA-403-001", HttpStatus.FORBIDDEN, "Subscription restricted",
        "This operation is not available under the current subscription policy.", false),
    RATE_LIMITED("KX-GEN-429-001", HttpStatus.TOO_MANY_REQUESTS, "Rate limit exceeded",
        "Too many requests. Retry according to the server retry policy.", true),
    UPSTREAM_UNAVAILABLE("KX-GEN-503-001", HttpStatus.SERVICE_UNAVAILABLE, "Service temporarily unavailable",
        "The operation cannot be completed at this time.", true),
    INTERNAL_ERROR("KX-GEN-500-001", HttpStatus.INTERNAL_SERVER_ERROR, "Internal server error",
        "The request could not be completed. Contact support using the request ID.", false);

    private final String code;
    private final HttpStatus status;
    private final String title;
    private final String publicDetail;
    private final boolean retryable;

    ErrorCode(String code, HttpStatus status, String title, String publicDetail, boolean retryable) {
        this.code = code;
        this.status = status;
        this.title = title;
        this.publicDetail = publicDetail;
        this.retryable = retryable;
    }

    public String code() { return code; }
    public HttpStatus status() { return status; }
    public String title() { return title; }
    public String publicDetail() { return publicDetail; }
    public boolean retryable() { return retryable; }
}
