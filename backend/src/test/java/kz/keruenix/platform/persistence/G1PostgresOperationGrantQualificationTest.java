package kz.keruenix.platform.persistence;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.Statement;
import java.util.UUID;

import javax.sql.DataSource;

import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * G0/G1 qualification only: a real PostgreSQL-backed, operation-scoped grant
 * oracle under a NON-PRODUCTION table. This test proves PostgreSQL/RLS and
 * explicit account predicates can implement the intended safety contract.
 *
 * It does NOT approve the business relationship, authorize an RFQ endpoint,
 * or satisfy the real CustomerAccount production-adapter behavioral RED gate.
 * No synthetic in-memory grants or permissive application adapter are used.
 */
@EnabledIfEnvironmentVariable(named = "KERUENIX_DB_URL", matches = "jdbc:postgresql:.*")
@SpringBootTest
@ActiveProfiles({"platform-db", "platform-db-migrate-test"})
class G1PostgresOperationGrantQualificationTest {
    @Autowired DataSource dataSource;

    @BeforeAll
    static void prepareQualificationTable() throws Exception {
        try (Connection admin = DriverManager.getConnection(
                System.getenv("KERUENIX_DB_URL"),
                System.getenv("KERUENIX_DB_MIGRATOR_USER"),
                System.getenv("KERUENIX_DB_MIGRATOR_PASSWORD"));
             Statement sql = admin.createStatement()) {
            sql.execute("""
                    CREATE TABLE IF NOT EXISTS platform.g1_qualification_operation_grant (
                        tenant_id uuid NOT NULL,
                        customer_account_id uuid NOT NULL,
                        actor_subject text NOT NULL,
                        operation text NOT NULL,
                        grant_state text NOT NULL CHECK (grant_state IN ('GRANTED','REVOKED')),
                        PRIMARY KEY(tenant_id,customer_account_id,actor_subject,operation)
                    )
                    """);
            sql.execute("""
                    ALTER TABLE platform.g1_qualification_operation_grant ENABLE ROW LEVEL SECURITY
                    """);
            sql.execute("""
                    ALTER TABLE platform.g1_qualification_operation_grant FORCE ROW LEVEL SECURITY
                    """);
            sql.execute("""
                    DROP POLICY IF EXISTS g1_qualification_tenant ON platform.g1_qualification_operation_grant
                    """);
            sql.execute("""
                    CREATE POLICY g1_qualification_tenant
                    ON platform.g1_qualification_operation_grant
                    USING (tenant_id = platform.current_tenant_id())
                    WITH CHECK (tenant_id = platform.current_tenant_id())
                    """);
            sql.execute("""
                    GRANT SELECT,INSERT,UPDATE ON platform.g1_qualification_operation_grant TO keruenix_app
                    """);
            sql.execute("GRANT keruenix_app TO keruenix_ci_login");
        }
    }

    private void grant(UUID tenant, UUID account, String actor, String operation) {
        new PlatformTenantTransaction(dataSource).execute(tenant, jdbc -> {
            jdbc.update("""
                    INSERT INTO platform.g1_qualification_operation_grant
                       (tenant_id,customer_account_id,actor_subject,operation,grant_state)
                    VALUES(?,?,?,?,'GRANTED')
                    """, tenant,account,actor,operation);
            return null;
        });
    }

    private boolean allowed(UUID tenant, UUID account, String actor, String operation) {
        return new PlatformTenantTransaction(dataSource).execute(tenant, jdbc ->
                Boolean.TRUE.equals(jdbc.queryForObject("""
                        SELECT EXISTS(
                          SELECT 1 FROM platform.g1_qualification_operation_grant
                          WHERE tenant_id=? AND customer_account_id=?
                            AND actor_subject=? AND operation=? AND grant_state='GRANTED')
                        """, Boolean.class, tenant,account,actor,operation)));
    }

    @Test
    void sameTenantDifferentCustomerAccountsAreIndependent() {
        UUID tenant=UUID.randomUUID(), x=UUID.randomUUID(), y=UUID.randomUUID();
        grant(tenant,x,"alice","RFQ_DRAFT_CREATE");
        grant(tenant,y,"bob","RFQ_DRAFT_CREATE");

        assertThat(allowed(tenant,x,"alice","RFQ_DRAFT_CREATE")).isTrue();
        assertThat(allowed(tenant,y,"alice","RFQ_DRAFT_CREATE")).isFalse();
        assertThat(allowed(tenant,y,"bob","RFQ_DRAFT_CREATE")).isTrue();
        assertThat(allowed(tenant,x,"bob","RFQ_DRAFT_CREATE")).isFalse();
    }

    @Test
    void operationsCannotBeImpliedFromAnotherOperationGrant() {
        UUID tenant=UUID.randomUUID(), account=UUID.randomUUID();
        grant(tenant,account,"alice","RFQ_DRAFT_READ");

        assertThat(allowed(tenant,account,"alice","RFQ_DRAFT_READ")).isTrue();
        assertThat(allowed(tenant,account,"alice","RFQ_DRAFT_CREATE")).isFalse();
        assertThat(allowed(tenant,account,"alice","RFQ_DRAFT_UPDATE")).isFalse();
        assertThat(allowed(tenant,account,"alice","RFQ_SUBMIT")).isFalse();
    }

    @Test
    void revocationIsObservedByNextPrimaryDatabaseRead() {
        UUID tenant=UUID.randomUUID(), account=UUID.randomUUID();
        grant(tenant,account,"alice","RFQ_DRAFT_READ");
        assertThat(allowed(tenant,account,"alice","RFQ_DRAFT_READ")).isTrue();

        new PlatformTenantTransaction(dataSource).execute(tenant, jdbc -> {
            assertThat(jdbc.update("""
                    UPDATE platform.g1_qualification_operation_grant
                       SET grant_state='REVOKED'
                     WHERE tenant_id=? AND customer_account_id=?
                       AND actor_subject=? AND operation=?
                    """,tenant,account,"alice","RFQ_DRAFT_READ")).isEqualTo(1);
            return null;
        });
        assertThat(allowed(tenant,account,"alice","RFQ_DRAFT_READ")).isFalse();
    }

    @Test
    void tenantRlsAndAccountPredicateBothRestrictAccess() {
        UUID tenantA=UUID.randomUUID(), tenantB=UUID.randomUUID();
        UUID account=UUID.randomUUID();
        grant(tenantA,account,"alice","RFQ_DRAFT_CREATE");

        assertThat(allowed(tenantA,account,"alice","RFQ_DRAFT_CREATE")).isTrue();
        assertThat(allowed(tenantB,account,"alice","RFQ_DRAFT_CREATE")).isFalse();
        assertThat(allowed(tenantA,UUID.randomUUID(),"alice","RFQ_DRAFT_CREATE")).isFalse();
    }
}
