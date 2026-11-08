package kz.keruenix.platform.persistence;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.Callable;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;

import javax.sql.DataSource;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.test.context.ActiveProfiles;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Real concurrent PostgreSQL claims with restricted dispatcher credentials.
 * No external broker is connected; only durable claim/ack/retry fencing is proved.
 */
@EnabledIfEnvironmentVariable(named="KERUENIX_DB_URL", matches="jdbc:postgresql:.*")
@SpringBootTest
@ActiveProfiles({"platform-db","platform-db-migrate-test"})
class PlatformOutboxClaimIntegrationTest {
    private static final UUID A=UUID.fromString("cccccccc-cccc-cccc-cccc-cccccccccccc");
    private static final UUID B=UUID.fromString("dddddddd-dddd-dddd-dddd-dddddddddddd");
    @Autowired DataSource dataSource;
    PlatformTenantTransaction app;
    PlatformOutboxClaims worker;

    private Connection admin() throws Exception {
        return DriverManager.getConnection(
            System.getenv("KERUENIX_DB_URL"),
            System.getenv("KERUENIX_DB_MIGRATOR_USER"),
            System.getenv("KERUENIX_DB_MIGRATOR_PASSWORD"));
    }

    @BeforeEach
    void provisionIsolatedWorkerRole() throws Exception {
        try(Connection admin=admin(); Statement ddl=admin.createStatement()){
            ddl.execute("""
                DO $roles$ BEGIN
                  IF NOT EXISTS (SELECT 1 FROM pg_roles
                                 WHERE rolname = 'keruenix_ci_dispatcher') THEN
                    CREATE ROLE keruenix_ci_dispatcher LOGIN
                    PASSWORD 'ci-only-dispatcher-pass';
                  END IF;
                END $roles$
                """);
            ddl.execute(java.nio.file.Files.readString(
                    java.nio.file.Path.of("db/admin/bootstrap_roles.sql")));
            ddl.execute("GRANT keruenix_dispatcher TO keruenix_ci_dispatcher");
            ddl.execute("GRANT keruenix_app TO keruenix_ci_login");
        }
        app=new PlatformTenantTransaction(dataSource);
        DriverManagerDataSource dispatcher=new DriverManagerDataSource(
            System.getenv("KERUENIX_DB_URL"),
            "keruenix_ci_dispatcher", "ci-only-dispatcher-pass");
        worker=new PlatformOutboxClaims(new PlatformTenantTransaction(dispatcher));
    }

    private UUID seed(UUID tenant) {
        UUID id=UUID.randomUUID();
        app.execute(tenant,jdbc->{
            jdbc.update("""
                INSERT INTO platform.outbox_event(
                    tenant_id,event_id,event_type,aggregate_ref,
                    payload_schema_version,payload,payload_sha256)
                VALUES (?,?,'LeaseProbe','ci:lease',1,'{}'::jsonb,?)
                """,tenant,id,"a".repeat(64));
            return null;
        });
        return id;
    }

    @Test
    void twoConcurrentWorkersCannotClaimTheSameReadyEvent() throws Exception {
        UUID id=seed(A);
        CountDownLatch start=new CountDownLatch(1);
        try(var pool=Executors.newFixedThreadPool(2)){
            List<Callable<Optional<PlatformOutboxClaims.Claim>>> actions=List.of(
                ()->{start.await();return worker.claimNext(A,"w-1",60);},
                ()->{start.await();return worker.claimNext(A,"w-2",60);}
            );
            List<Future<Optional<PlatformOutboxClaims.Claim>>> futures=new ArrayList<>();
            for(var action:actions)futures.add(pool.submit(action));
            start.countDown();
            var first=futures.get(0).get(25,TimeUnit.SECONDS);
            var second=futures.get(1).get(25,TimeUnit.SECONDS);
            assertThat(List.of(first,second).stream().filter(Optional::isPresent).count())
                .isEqualTo(1);
            var claim=first.or(()->second).orElseThrow();
            assertThat(claim.eventId()).isEqualTo(id);
            assertThat(claim.fencingToken()).isEqualTo(1L);
            assertThat(worker.markPublished(A,claim)).isTrue();
            assertThat(worker.markPublished(A,claim)).isFalse();
        }
    }

    @Test
    void staleOwnerCannotPublishAfterLeaseExpirationAndTakeover() throws Exception {
        UUID event=seed(A);
        var first=worker.claimNext(A,"worker-old",60).orElseThrow();
        try(Connection connection=admin();
            PreparedStatement update=connection.prepareStatement("""
                UPDATE platform.outbox_event
                   SET lease_until = clock_timestamp()-interval '1 second'
                 WHERE tenant_id=? AND event_id=?
                """)){
            update.setObject(1,A);
            update.setObject(2,event);
            assertThat(update.executeUpdate()).isEqualTo(1);
        }
        var second=worker.claimNext(A,"worker-new",60).orElseThrow();
        assertThat(second.eventId()).isEqualTo(event);
        assertThat(second.fencingToken()).isEqualTo(first.fencingToken()+1);
        assertThat(worker.markPublished(A,first)).isFalse();
        assertThat(worker.scheduleRetry(A,first,0)).isFalse();
        assertThat(worker.markPublished(A,second)).isTrue();
    }

    @Test
    void retryReleasesClaimAndRetainsDurablePayload() {
        UUID event=seed(A);
        var initial=worker.claimNext(A,"worker-retry",30).orElseThrow();
        assertThat(worker.scheduleRetry(A,initial,0)).isTrue();
        assertThat(worker.markPublished(A,initial)).isFalse();
        var retried=worker.claimNext(A,"worker-next",30).orElseThrow();
        assertThat(retried.eventId()).isEqualTo(event);
        assertThat(retried.fencingToken()).isEqualTo(initial.fencingToken()+1);
        assertThat(retried.attemptCount()).isEqualTo(2);
        assertThat(worker.markPublished(A,retried)).isTrue();
    }

    @Test
    void dispatcherCanNeverSelectAnotherTenantsPendingEvent() {
        UUID id=seed(A);
        assertThat(worker.claimNext(B,"foreign",30)).isEmpty();
        assertThat(worker.claimNext(A,"correct",30).orElseThrow().eventId()).isEqualTo(id);
    }
}
