package kz.keruenix.platform.persistence;

import java.util.Objects;
import java.util.UUID;

/**
 * FOUND-05 TDD RED: typed outbound delivery contract. Actual implementation
 * must load a fenced committed event, send outside DB transaction, then ACK.
 * No broker/provider selected yet; transport is an injected boundary.
 */
final class PlatformOutboxDelivery {
    record Envelope(UUID tenantId, UUID eventId, String eventType,
                    String payloadJson, String payloadSha256, int deliveryAttempt) {}

    @FunctionalInterface
    interface Sender {
        void send(Envelope envelope);
    }

    private final PlatformOutboxClaims claims;
    private final PlatformTenantTransaction dispatcherScope;

    PlatformOutboxDelivery(PlatformOutboxClaims claims, PlatformTenantTransaction dispatcherScope) {
        this.claims = Objects.requireNonNull(claims);
        this.dispatcherScope = Objects.requireNonNull(dispatcherScope);
    }

    boolean dispatchNext(UUID tenantId, String workerId, int leaseSeconds, Sender sender) {
        return false; // RED: never claim completion without a committed send and ack.
    }
}
