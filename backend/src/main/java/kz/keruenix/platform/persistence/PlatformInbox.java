package kz.keruenix.platform.persistence;

import java.util.Objects;
import java.util.UUID;

import org.springframework.jdbc.core.JdbcTemplate;

/**
 * Durable duplicate classification on the authoritative tenant-scoped Inbox.
 * This class does not dispatch events or grant business privileges.
 */
final class PlatformInbox {
    enum Result { NEW, REPLAY_IDENTICAL }

    Result accept(JdbcTemplate jdbc, UUID tenantId, String consumer, UUID eventId,
                  String payloadSha256) {
        Objects.requireNonNull(jdbc);
        Objects.requireNonNull(tenantId);
        Objects.requireNonNull(eventId);
        if (consumer == null || consumer.isBlank() ||
                payloadSha256 == null || !payloadSha256.matches("[0-9a-f]{64}")) {
            throw new IllegalArgumentException("Invalid consumer or payload digest");
        }
        int inserted = jdbc.update("""
            INSERT INTO platform.inbox_receipt(tenant_id,consumer_name,event_id,payload_sha256)
            VALUES (?,?,?,?)
            ON CONFLICT (tenant_id,consumer_name,event_id) DO NOTHING
            """, tenantId, consumer, eventId, payloadSha256);
        if (inserted == 1) {
            return Result.NEW;
        }
        String storedDigest = jdbc.queryForObject("""
            SELECT payload_sha256
            FROM platform.inbox_receipt
            WHERE tenant_id = ? AND consumer_name = ? AND event_id = ?
            """, String.class, tenantId, consumer, eventId);
        if (storedDigest == null || !storedDigest.equals(payloadSha256)) {
            // Conflict must not be silently accepted as a successful retry.
            throw new IllegalStateException("Inbox event identity reused with a different digest");
        }
        return Result.REPLAY_IDENTICAL;
    }
}
