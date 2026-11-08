package kz.keruenix.platform.security;

import java.util.UUID;

import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.Authentication;

/**
 * PR-01 foundation boundary for later PR-02 verified identity/grants.
 * A signed JWT is identity evidence only, never a tenant/customer grant.
 * Default is DENY until proof of server-side grant and role authorization.
 */
public final class TenantScopeAuthorization {
    @FunctionalInterface
    public interface VerifiedGrantSource {
        boolean canAccess(String subject, UUID tenantId, UUID customerAccountId);
    }

    public record Scope(String subject, UUID tenantId, UUID customerAccountId) {}

    private final VerifiedGrantSource grants;

    public TenantScopeAuthorization(VerifiedGrantSource grants) {
        this.grants = java.util.Objects.requireNonNull(grants);
    }

    public Scope authorize(Authentication authentication, UUID requestedTenant,
                           UUID requestedAccount, String tenantHeader, UUID tenantInBody) {
        throw new AccessDeniedException("Tenant/customer grant verification not yet implemented");
    }
}
