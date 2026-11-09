package kz.keruenix.platform.persistence;

import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.Statement;

import liquibase.integration.spring.SpringLiquibase;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.springframework.jdbc.datasource.DriverManagerDataSource;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

/**
 * Synthetic legacy-Flyway database. Never migrate over an existing Flyway history
 * automatically: a reviewed production cutover needs a DB snapshot and baseline.
 */
@EnabledIfEnvironmentVariable(
        named = "KERUENIX_LEGACY_GUARD_DB_URL", matches = "jdbc:postgresql:.*")
class LiquibaseFlywayHistoryGuardTest {
    @Test
    void rejectsLegacyFlywayHistoryBeforeCreatingBusinessSchema() throws Exception {
        var admin = new DriverManagerDataSource(
                System.getenv("KERUENIX_LEGACY_GUARD_DB_URL"),
                System.getenv("KERUENIX_DB_MIGRATOR_USER"),
                System.getenv("KERUENIX_DB_MIGRATOR_PASSWORD"));
        try (Connection connection = admin.getConnection();
             Statement statement = connection.createStatement()) {
            statement.execute("""
                CREATE TABLE IF NOT EXISTS public.flyway_schema_history (
                    installed_rank integer PRIMARY KEY
                )
                """);
            statement.execute("INSERT INTO public.flyway_schema_history(installed_rank) VALUES (1)");
        }

        var liquibase = new SpringLiquibase();
        liquibase.setDataSource(admin);
        liquibase.setChangeLog("classpath:db/changelog/db.changelog-master.yaml");
        assertThatThrownBy(liquibase::afterPropertiesSet)
                .isInstanceOf(Exception.class);

        try (Connection connection = admin.getConnection();
             Statement statement = connection.createStatement();
             ResultSet result = statement.executeQuery("""
                     SELECT count(*) FROM pg_catalog.pg_tables
                     WHERE schemaname = 'platform'
                       AND tablename IN ('outbox_event','inbox_receipt','audit_fact')
                     """)) {
            assertThat(result.next()).isTrue();
            assertThat(result.getInt(1)).isZero();
        }
    }
}
