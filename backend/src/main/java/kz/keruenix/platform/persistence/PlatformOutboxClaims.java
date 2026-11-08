package kz.keruenix.platform.persistence;

import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.UUID;

/**
 * Per-tenant durable Outbox lease/fencing primitive (PR-01); not a broker or
 * production scheduler. A trusted system controller must supply an authorized
 * tenant ID. A broker send may repeat after crash; consumers use Inbox dedup.
 *
 * The worker must connect through the restricted keruenix_dispatcher role,
 * not application or privileged migration credentials.
 */
final class PlatformOutboxClaims {
    record Claim(UUID eventId, long fencingToken, String owner, int attemptCount) {}

    private final PlatformTenantTransaction workerTransactions;

    PlatformOutboxClaims(PlatformTenantTransaction workerTransactions) {
        this.workerTransactions = Objects.requireNonNull(workerTransactions);
    }

    Optional<Claim> claimNext(UUID tenantId, String workerId, int leaseSeconds) {
        if (workerId == null || workerId.isBlank() || workerId.length() > 160 ||
                leaseSeconds < 1 || leaseSeconds > 3600) {
            throw new IllegalArgumentException("Invalid worker lease parameters");
        }
        return workerTransactions.execute(tenantId, jdbc -> {
            List<Claim> claimed = jdbc.query("""
                WITH candidate AS (
                  SELECT tenant_id,event_id
                    FROM platform.outbox_event
                   WHERE tenant_id = ?
                     AND next_attempt_at <= clock_timestamp()
                     AND (delivery_state = 'PENDING'
                       OR (delivery_state = 'CLAIMED'
                           AND lease_until < clock_timestamp()))
                   ORDER BY created_at,event_id
                   FOR UPDATE SKIP LOCKED
                   LIMIT 1
                )
                UPDATE platform.outbox_event o
                   SET delivery_state = 'CLAIMED',
                       claim_owner = ?,
                       claim_token = o.claim_token + 1,
                       attempt_count = o.attempt_count + 1,
                       lease_until = clock_timestamp() + make_interval(secs => ?)
                  FROM candidate c
                 WHERE o.tenant_id = c.tenant_id AND o.event_id = c.event_id
                RETURNING o.event_id,o.claim_token,o.claim_owner,o.attempt_count
                """, (rs, number) -> new Claim(
                    (UUID) rs.getObject("event_id"),
                    rs.getLong("claim_token"),
                    rs.getString("claim_owner"),
                    rs.getInt("attempt_count")),
                    tenantId, workerId, leaseSeconds);
            return claimed.stream().findFirst();
        });
    }

    boolean markPublished(UUID tenantId, Claim claim) {
        return workerTransactions.execute(tenantId, jdbc -> jdbc.update("""
            UPDATE platform.outbox_event
               SET delivery_state = 'PUBLISHED',
                   claim_owner = NULL,
                   lease_until = NULL,
                   published_at = clock_timestamp()
             WHERE tenant_id = ? AND event_id = ?
               AND delivery_state = 'CLAIMED'
               AND claim_owner = ? AND claim_token = ?
               AND lease_until > clock_timestamp()
            """, tenantId, claim.eventId(), claim.owner(), claim.fencingToken()) == 1);
    }

    boolean scheduleRetry(UUID tenantId, Claim claim, int delaySeconds) {
        if (delaySeconds < 0 || delaySeconds > 86_400) {
            throw new IllegalArgumentException("Invalid retry delay");
        }
        return workerTransactions.execute(tenantId, jdbc -> jdbc.update("""
            UPDATE platform.outbox_event
               SET delivery_state = 'PENDING',
                   claim_owner = NULL,
                   lease_until = NULL,
                   next_attempt_at = clock_timestamp() + make_interval(secs => ?)
             WHERE tenant_id = ? AND event_id = ?
               AND delivery_state = 'CLAIMED'
               AND claim_owner = ? AND claim_token = ?
               AND lease_until > clock_timestamp()
            """, delaySeconds, tenantId, claim.eventId(), claim.owner(), claim.fencingToken()) == 1);
    }
}
