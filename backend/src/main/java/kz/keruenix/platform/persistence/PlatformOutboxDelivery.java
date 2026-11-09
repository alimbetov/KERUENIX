package kz.keruenix.platform.persistence;

import java.util.List;
import java.util.Objects;
import java.util.UUID;

import org.springframework.transaction.support.TransactionSynchronizationManager;

/**
 * FOUND-05: durable at-least-once Outbox transport boundary.
 *
 * Claim + committed payload read and fenced ACK are independent short
 * transactions; Sender is always called with NO active transaction.
 * A send may be repeated after a crash. Consumers MUST durably deduplicate
 * their logical effects using a scoped Inbox in their own business transaction.
 *
 * PR-01 caveat: this is a transport port, NOT a configured external broker,
 * tenant discovery scheduler, DLQ, or production runtime worker.
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
        Objects.requireNonNull(tenantId, "tenantId");
        Objects.requireNonNull(sender, "sender");
        if (TransactionSynchronizationManager.isActualTransactionActive()) {
            throw new IllegalStateException(
                    "Outbox external delivery must not run in an active transaction");
        }
        var next = claims.claimNext(tenantId, workerId, leaseSeconds);
        if (next.isEmpty()) {
            return false;
        }
        var claim = next.orElseThrow();
        Envelope envelope = dispatcherScope.execute(tenantId, jdbc -> {
            List<Envelope> rows = jdbc.query("""
                    SELECT event_id,event_type,payload::text AS payload_json,
                           payload_sha256,attempt_count
                      FROM platform.outbox_event
                     WHERE tenant_id = ? AND event_id = ?
                       AND delivery_state = 'CLAIMED'
                       AND claim_owner = ? AND claim_token = ?
                       AND lease_until > clock_timestamp()
                    """, (rs, index) -> new Envelope(
                            tenantId,
                            (UUID) rs.getObject("event_id"),
                            rs.getString("event_type"),
                            rs.getString("payload_json"),
                            rs.getString("payload_sha256"),
                            rs.getInt("attempt_count")),
                    tenantId, claim.eventId(), claim.owner(), claim.fencingToken());
            if (rows.size() != 1) {
                throw new IllegalStateException("Outbox lease lost before payload read");
            }
            return rows.getFirst();
        });

        // A sender exception represents a possible crash AFTER the consumer
        // committed its logical effect but BEFORE ACK. Do not ACK or discard it.
        // The event remains CLAIMED until its lease expires, then can be replayed.
        sender.send(envelope);
        if (!claims.markPublished(tenantId, claim)) {
            throw new IllegalStateException("Outbox lease lost before ACK");
        }
        return true;
    }
}
