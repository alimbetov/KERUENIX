package kz.keruenix.platform.errors;

import jakarta.servlet.http.HttpServletRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.MediaType;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.web.HttpMediaTypeNotSupportedException;
import org.springframework.web.HttpRequestMethodNotSupportedException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.context.request.ServletWebRequest;
import org.springframework.web.context.request.WebRequest;
import org.springframework.web.servlet.mvc.method.annotation.ResponseEntityExceptionHandler;

import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * MVC boundary only. Domain modules throw typed errors but must not
 * decide HTTP response formatting or bypass their own transactional guards.
 */
@RestControllerAdvice
public final class ApiExceptionHandler extends ResponseEntityExceptionHandler {
    private static final Logger LOG = LoggerFactory.getLogger(ApiExceptionHandler.class);
    private static final MediaType PROBLEM_JSON = MediaType.parseMediaType("application/problem+json");

    private final ApiProblemFactory problems;

    public ApiExceptionHandler(ApiProblemFactory problems) {
        this.problems = problems;
    }

    @ExceptionHandler(DomainProblemException.class)
    public ResponseEntity<ProblemDetail> domain(DomainProblemException failure, HttpServletRequest request) {
        ErrorCode code = failure.errorCode();
        return response(problems.create(code, request), code.status());
    }

    @ExceptionHandler(AccessDeniedException.class)
    public ResponseEntity<ProblemDetail> methodAccessDenied(AccessDeniedException failure,
                                                             HttpServletRequest request) {
        return response(problems.create(ErrorCode.PERMISSION_DENIED, request),
                ErrorCode.PERMISSION_DENIED.status());
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ProblemDetail> unexpected(Exception failure, HttpServletRequest request) {
        String requestId = RequestIdFilter.requestId(request);
        // Do not log exception.getMessage(): SQL/credentials/PII can appear in exception chains.
        LOG.error("Unhandled request failure requestId={} exceptionType={}",
                requestId, failure.getClass().getSimpleName());
        return response(problems.create(ErrorCode.INTERNAL_ERROR, request),
                ErrorCode.INTERNAL_ERROR.status());
    }

    @Override
    protected ResponseEntity<Object> handleExceptionInternal(
            Exception failure, Object body, HttpHeaders headers, HttpStatusCode status, WebRequest request) {
        HttpServletRequest servlet = ((ServletWebRequest) request).getRequest();
        ErrorCode code = classify(failure, status);
        List<Map<String, String>> violations = List.of();
        if (failure instanceof MethodArgumentNotValidException validation) {
            violations = validation.getBindingResult().getFieldErrors().stream()
                    .map(field -> {
                        Map<String, String> violation = new LinkedHashMap<>();
                        violation.put("field", field.getField());
                        violation.put("rule", field.getCode() == null ? "Invalid" : field.getCode());
                        return violation;
                    })
                    .sorted(Comparator.comparing(v -> v.get("field")))
                    .limit(30)
                    .toList();
        }
        ProblemDetail problem = problems.create(code, status, servlet, violations);
        HttpHeaders safeHeaders = new HttpHeaders();
        safeHeaders.addAll(headers); // Preserve Allow, Accept and other framework metadata.
        safeHeaders.setContentType(PROBLEM_JSON);
        safeHeaders.set("Cache-Control", "no-store");
        return new ResponseEntity<>(problem, safeHeaders, status);
    }

    private ErrorCode classify(Exception failure, HttpStatusCode status) {
        if (failure instanceof MethodArgumentNotValidException) {
            return ErrorCode.VALIDATION_FAILED;
        }
        if (failure instanceof HttpMessageNotReadableException) {
            return ErrorCode.BAD_REQUEST;
        }
        if (failure instanceof HttpRequestMethodNotSupportedException) {
            return ErrorCode.METHOD_NOT_ALLOWED;
        }
        if (failure instanceof HttpMediaTypeNotSupportedException) {
            return ErrorCode.UNSUPPORTED_MEDIA_TYPE;
        }
        if (status.value() == 404) {
            return ErrorCode.RESOURCE_NOT_FOUND;
        }
        if (status.value() == 401) {
            return ErrorCode.AUTHENTICATION_REQUIRED;
        }
        if (status.value() == 403) {
            return ErrorCode.PERMISSION_DENIED;
        }
        if (status.value() == 429) {
            return ErrorCode.RATE_LIMITED;
        }
        if (status.value() == 503) {
            return ErrorCode.UPSTREAM_UNAVAILABLE;
        }
        if (status.is5xxServerError()) {
            return ErrorCode.INTERNAL_ERROR;
        }
        return ErrorCode.FRAMEWORK_HTTP_ERROR; // Preserve unexpected 4xx status without mislabeling as 400.
    }

    private ResponseEntity<ProblemDetail> response(ProblemDetail problem, HttpStatusCode status) {
        return ResponseEntity.status(status)
                .contentType(PROBLEM_JSON)
                .header("Cache-Control", "no-store")
                .body(problem);
    }
}
