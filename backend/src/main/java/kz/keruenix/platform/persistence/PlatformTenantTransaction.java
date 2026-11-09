package kz.keruenix.platform.persistence;

import java.util.Objects;
import java.util.UUID;
import java.util.function.Function;

import javax.sql.DataSource;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DataSourceTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;

/**
 * Internal PR-01 testable transaction primitive, NOT an authorization API.
 * The UUID must eventually be provided only by PR-02 verified identity+grant.
 * Callers must not pass a user-supplied tenant header, JSON field or JWT claim
 * without signature, issuer, audience and membership validation.
 */
final class PlatformTenantTransaction {
    private final TransactionTemplate transactions;
    private final JdbcTemplate jdbc;

    PlatformTenantTransaction(DataSource dataSource) {
        Objects.requireNonNull(dataSource, "dataSource");
        this.transactions = new TransactionTemplate(new DataSourceTransactionManager(dataSource));
        this.jdbc = new JdbcTemplate(dataSource);
    }

    <T> T execute(UUID verifiedTenantId, Function<JdbcTemplate, T> work) {
        Objects.requireNonNull(verifiedTenantId, "verifiedTenantId");
        Objects.requireNonNull(work, "work");
        return transactions.execute(status -> {
            // REQUIRED propagation joins the existing physical transaction.
            // Never allow an inner operation to replace the active tenant's
            // PostgreSQL RLS context: SET LOCAL would otherwise permit B reads
            // and writes from inside an A-scoped command.
            String currentTenant = jdbc.queryForObject("""
                    SELECT NULLIF(current_setting('keruenix.tenant_id', true), '')
                    """, String.class);
            String requestedTenant = verifiedTenantId.toString();
            if (currentTenant != null && !currentTenant.equals(requestedTenant)) {
                throw new SecurityException(
                        "Cannot switch tenant inside an active transaction");
            }
            // set_config(..., true) is local to this physical transaction,
            // unlike a session-level SET that may persist in a JDBC pool.
            if (currentTenant == null) {
                jdbc.queryForObject("SELECT set_config('keruenix.tenant_id', ?, true)",
                        String.class, requestedTenant);
            }
            return work.apply(jdbc);
        });
    }
}
