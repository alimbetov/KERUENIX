package kz.keruenix.platform.persistence;

import java.util.UUID;

import javax.sql.DataSource;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.context.ActiveProfiles;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * PR-04 safe RFQ Draft RED specification. No domain implementation or
 * test-only RFQ success controller: a valid, scoped customer must be able to
 * create a NON-BINDING draft only after S0/S2 review. The current production
 * SecurityConfig denyAll intentionally makes the positive test RED.
 *
 * /api/v1/rfqs/drafts is a PROPOSED endpoint, not an approved public contract.
 */
@EnabledIfEnvironmentVariable(named = "KERUENIX_DB_URL", matches = "jdbc:postgresql:.*")
@SpringBootTest
@AutoConfigureMockMvc
@Import(TrustedTenantHttpIntegrationTest.QualificationConfig.class)
@ActiveProfiles({"platform-db", "platform-db-migrate-test"})
class RfqDraftRedContractTest {
    private static final UUID TENANT_A = TrustedTenantHttpIntegrationTest.TENANT_A;
    private static final UUID ACCOUNT_X = TrustedTenantHttpIntegrationTest.ACCOUNT_X;
    @Autowired MockMvc mvc;
    @Autowired DataSource database;

    private String json(UUID cargoId) {
        return "{\"tenantId\":\"" + TENANT_A + "\",\"customerAccountId\":\""
                + ACCOUNT_X + "\",\"cargo\":[{\"cargoId\":\"" + cargoId
                + "\",\"units\":1}],\"origin\":\"CUSTOMER\"}";
    }

    private int countOutbox(UUID tenant) {
        return new PlatformTenantTransaction(database).execute(tenant, jdbc ->
                jdbc.queryForObject("SELECT count(*) FROM platform.outbox_event",
                        Integer.class));
    }

    /**
     * S1 RED: the currently absent RFQ domain API must eventually return 201
     * for an authorized, verified, non-binding draft, never for an unsigned submit.
     * The expected response is defined before any PR-04 implementation.
     */
    @Test
    void authorizedNonBindingDraftCreationIsMissingBehaviorRed() throws Exception {
        int before = countOutbox(TENANT_A);
        mvc.perform(post("/api/v1/rfqs/drafts")
                .header("Authorization", "Bearer " + TrustedTenantHttpIntegrationTest.valid("alice"))
                .header("Idempotency-Key", UUID.randomUUID().toString())
                .contentType(MediaType.APPLICATION_JSON)
                .content(json(UUID.randomUUID())))
                .andExpect(status().isCreated());  // deliberate behavior RED; never @Disabled
        // To be extended after the canonical RFQ Draft schema/ADR is approved:
        // assert DRAFT persisted, same-key replay stable, new key different draft,
        // cargo hash immutable, no RFQ_SUBMITTED/QuoteAccepted/BookingConfirmed.
        assertThat(countOutbox(TENANT_A)).isEqualTo(before);
    }

    /**
     * Pending DEC-R0-03: draft cannot authorize Submit, Quote or Booking.
     * This negative safety contract is executable independently of PR-04.
     */
    @Test
    void bindingSubmissionRemainsDeniedWithoutApprovedAuthority() throws Exception {
        UUID id = UUID.randomUUID();
        int before = countOutbox(TENANT_A);
        mvc.perform(post("/api/v1/rfqs/{id}/submit", id)
                .header("Authorization", "Bearer " + TrustedTenantHttpIntegrationTest.valid("alice"))
                .contentType(MediaType.APPLICATION_JSON)
                .content("{}"))
                .andExpect(status().isForbidden());
        assertThat(countOutbox(TENANT_A)).isEqualTo(before);
    }
}
