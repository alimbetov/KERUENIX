package kz.keruenix.customeraccount.contractred;

import java.util.UUID;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import kz.keruenix.customeraccount.jobs.CustomerAccountJobEnvelope;
import kz.keruenix.customeraccount.jobs.CustomerAccountJobPort;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Intentionally compile-RED: real durable job adapter is absent.
 * No synthetic worker, in-memory queue, or dummy green test.
 * The proposed API requires owner sign-off on DEC-CA-03/04.
 */
@SpringBootTest
class CustomerAccountJobAdapterRedTest {
    private static final UUID TENANT_A =
            UUID.fromString("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa");
    private static final UUID ACCOUNT_X =
            UUID.fromString("11111111-1111-1111-1111-111111111111");
    private static final UUID ACCOUNT_Y =
            UUID.fromString("22222222-2222-2222-2222-222222222222");

    @Autowired CustomerAccountJobPort productionWorker;

    @Test
    void forgedCustomerAccountCannotClaimOrDeliverJob() {
        // The real port must reject a payload that does not match the
        // server-verified principal's account. The job must not be published,
        // exported or acknowledged as completed by the worker.
        CustomerAccountJobEnvelope forged = new CustomerAccountJobEnvelope(
                UUID.randomUUID(), TENANT_A, ACCOUNT_Y, "alice",
                "EXPORT", UUID.randomUUID(), 1L, UUID.randomUUID().toString());
        assertThat(productionWorker.canClaimForAccount(forged, ACCOUNT_X)).isFalse();
    }

    // CA-JOB-02..04 must run against a real migrated PostgreSQL job schema,
    // grant store and worker. Claim/retry after revoke, double claim, stale
    // fencing acknowledgement, process restart and artifact URL authorization
    // are NOT validated by this preliminary API-absent source.
}
