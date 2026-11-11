package kz.keruenix.platform.persistence;

import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.Statement;
import java.util.UUID;

import javax.sql.DataSource;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.transaction.support.TransactionSynchronizationManager;
import org.springframework.test.context.ActiveProfiles;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

/**
 * FOUND-05 RED: real committed Outbox -> typed sender -> Inbox + Audit effect;
 * crash after consumer commit and BEFORE publisher ACK; replay once more.
 * This proves local at-least-once with idempotent logical consumer effects,
 * NOT delivery through a live external broker.
 */
@EnabledIfEnvironmentVariable(named="KERUENIX_DB_URL", matches="jdbc:postgresql:.*")
@SpringBootTest
@ActiveProfiles({"platform-db","platform-db-migrate-test"})
class PlatformOutboxDeliveryIntegrationTest {
    static final UUID TENANT=UUID.fromString("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee");
    static final UUID OTHER=UUID.fromString("ffffffff-ffff-ffff-ffff-ffffffffffff");
    @Autowired DataSource dataSource;
    PlatformTenantTransaction appScope;
    PlatformOutboxDelivery delivery;

    private Connection admin() throws Exception {
        return DriverManager.getConnection(System.getenv("KERUENIX_DB_URL"),
                System.getenv("KERUENIX_DB_MIGRATOR_USER"),
                System.getenv("KERUENIX_DB_MIGRATOR_PASSWORD"));
    }

    @BeforeEach
    void provisionRuntimeAndFencedDispatcher() throws Exception {
        try (Connection admin=admin(); Statement ddl=admin.createStatement()) {
            ddl.execute(Files.readString(Path.of("db/admin/bootstrap_roles.sql")));
            ddl.execute("""
                    DO $roles$ BEGIN
                      IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='keruenix_ci_dispatcher') THEN
                        CREATE ROLE keruenix_ci_dispatcher LOGIN PASSWORD 'ci-only-dispatcher-pass';
                      END IF;
                    END $roles$
                    """);
            ddl.execute("GRANT keruenix_dispatcher TO keruenix_ci_dispatcher");
            ddl.execute("GRANT keruenix_app TO keruenix_ci_login");
        }
        appScope=new PlatformTenantTransaction(dataSource);
        var workerDataSource=new DriverManagerDataSource(
                System.getenv("KERUENIX_DB_URL"),"keruenix_ci_dispatcher","ci-only-dispatcher-pass");
        var workerScope=new PlatformTenantTransaction(workerDataSource);
        delivery=new PlatformOutboxDelivery(new PlatformOutboxClaims(workerScope),workerScope);
    }

    private UUID seed() {
        UUID id=UUID.randomUUID();
        appScope.execute(TENANT,sql -> {
            sql.update("""
                    INSERT INTO platform.outbox_event(
                        tenant_id,event_id,event_type,aggregate_ref,payload_schema_version,
                        payload,payload_sha256)
                    VALUES (?,?,'DeliveryQualification','probe:1',1,'{"probe":true}'::jsonb,?)
                    """,TENANT,id,"c".repeat(64));
            return null;
        });
        return id;
    }

    private void consume(PlatformOutboxDelivery.Envelope envelope) {
        appScope.execute(envelope.tenantId(),sql -> {
            var applied=new PlatformInbox().accept(sql,envelope.tenantId(),
                    "qualification-consumer",envelope.eventId(),envelope.payloadSha256());
            if(applied == PlatformInbox.Result.NEW) {
                sql.update("""
                        INSERT INTO platform.audit_fact(
                            tenant_id,audit_id,actor_ref,action_type,subject_ref)
                        VALUES (?,?,'ci:consumer','OutboxConsumed',?)
                        """,envelope.tenantId(),envelope.eventId(),envelope.eventType());
            }
            return null;
        });
    }

    private int count(String table, UUID event) {
        return appScope.execute(TENANT,sql -> sql.queryForObject(
                "SELECT count(*) FROM "+table+" WHERE "+(
                    table.equals("platform.audit_fact")?"audit_id":"event_id")+"=?",
                Integer.class,event));
    }

    @Test
    void crashAfterConsumerCommitBeforePublisherAckIsSafeOnReplay() throws Exception {
        UUID event=seed();
        int[] sends={0};
        PlatformOutboxDelivery.Sender sender=envelope -> {
            sends[0]++;
            assertThat(envelope.eventId()).isEqualTo(event);
            assertThat(envelope.tenantId()).isEqualTo(TENANT);
            assertThat(envelope.eventType()).isEqualTo("DeliveryQualification");
            assertThat(envelope.payloadJson()).contains("probe");
            assertThat(envelope.payloadSha256()).isEqualTo("c".repeat(64));
            assertThat(TransactionSynchronizationManager.isActualTransactionActive()).isFalse();
            consume(envelope); // separate committed consumer Inbox + business effect
            if(sends[0]==1)throw new IllegalStateException("simulated crash before ACK");
        };
        assertThatThrownBy(() -> delivery.dispatchNext(TENANT,"worker-old",30,sender))
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("simulated crash before ACK");
        assertThat(count("platform.audit_fact",event)).isEqualTo(1);
        assertThat(count("platform.inbox_receipt",event)).isEqualTo(1);
        String state=appScope.execute(TENANT,sql -> sql.queryForObject(
                "SELECT delivery_state FROM platform.outbox_event WHERE event_id=?",
                String.class,event));
        assertThat(state).isEqualTo("CLAIMED");

        try (Connection admin=admin(); PreparedStatement expire=admin.prepareStatement("""
                UPDATE platform.outbox_event
                SET lease_until=clock_timestamp()-interval '1 second'
                WHERE tenant_id=? AND event_id=?
                """)) {
            expire.setObject(1,TENANT);
            expire.setObject(2,event);
            assertThat(expire.executeUpdate()).isEqualTo(1);
        }
        assertThat(delivery.dispatchNext(TENANT,"worker-new",30,sender)).isTrue();
        assertThat(sends[0]).isEqualTo(2);
        assertThat(count("platform.audit_fact",event)).isEqualTo(1);
        assertThat(count("platform.inbox_receipt",event)).isEqualTo(1);
        String published=appScope.execute(TENANT,sql -> sql.queryForObject(
                "SELECT delivery_state FROM platform.outbox_event WHERE event_id=?",
                String.class,event));
        assertThat(published).isEqualTo("PUBLISHED");
        assertThat(delivery.dispatchNext(TENANT,"worker-third",30,sender)).isFalse();
    }

    /**
     * A-05: lease expiration during Sender.send permits a second send.
     * Both real dispatcher transactions use PostgreSQL; Inbox prevents two
     * logical audit effects. This is at-least-once, NOT exactly-once I/O.
     */
    @Test
    void expiredLeaseDuringSlowSendRedeliversButConsumerEffectIsIdempotent() throws Exception {
        UUID event = seed();
        var oldEnteredSend = new java.util.concurrent.CountDownLatch(1);
        var allowOldReturn = new java.util.concurrent.CountDownLatch(1);
        var invocations = new java.util.concurrent.atomic.AtomicInteger();
        try (var pool = java.util.concurrent.Executors.newSingleThreadExecutor()) {
            var old = pool.submit(() -> {
                try {
                    delivery.dispatchNext(TENANT, "slow-old", 60, envelope -> {
                        assertThat(envelope.eventId()).isEqualTo(event);
                        invocations.incrementAndGet();
                        consume(envelope);
                        oldEnteredSend.countDown();
                        try {
                            if (!allowOldReturn.await(20, java.util.concurrent.TimeUnit.SECONDS)) {
                                throw new IllegalStateException("release latch timed out");
                            }
                        } catch (InterruptedException interrupted) {
                            Thread.currentThread().interrupt();
                            throw new IllegalStateException(interrupted);
                        }
                    });
                    return "ACK_UNEXPECTED";
                } catch (IllegalStateException expected) {
                    return expected.getMessage();
                }
            });
            assertThat(oldEnteredSend.await(20, java.util.concurrent.TimeUnit.SECONDS))
                    .as("old sender actually reached side-effect boundary").isTrue();
            try (Connection admin=admin(); PreparedStatement expire=admin.prepareStatement("""
                    UPDATE platform.outbox_event
                       SET lease_until=clock_timestamp()-interval '1 second'
                     WHERE tenant_id=? AND event_id=? AND delivery_state='CLAIMED'
                    """)) {
                expire.setObject(1, TENANT);
                expire.setObject(2, event);
                assertThat(expire.executeUpdate()).isEqualTo(1);
            }
            try {
                assertThat(delivery.dispatchNext(TENANT, "new-after-expiry", 60,
                        envelope -> {
                            assertThat(envelope.eventId()).isEqualTo(event);
                            invocations.incrementAndGet();
                            consume(envelope);
                        })).isTrue();
            } finally {
                allowOldReturn.countDown();
            }
            assertThat(old.get(25, java.util.concurrent.TimeUnit.SECONDS))
                    .contains("Outbox lease lost before ACK");
        }
        assertThat(invocations.get()).as("two transport sends are expected").isEqualTo(2);
        assertThat(count("platform.inbox_receipt", event)).isEqualTo(1);
        assertThat(count("platform.audit_fact", event)).isEqualTo(1);
        assertThat(appScope.execute(TENANT, jdbc -> jdbc.queryForObject(
                "SELECT delivery_state FROM platform.outbox_event WHERE event_id=?",
                String.class, event))).isEqualTo("PUBLISHED");
    }

    @Test
    void refusesToSendExternalEventInsideAnOpenBusinessTransaction() {
        UUID event = seed();
        int[] sends = {0};
        assertThatThrownBy(() -> appScope.execute(TENANT, jdbc -> {
            delivery.dispatchNext(TENANT,"illegal-nested-worker",30,
                    envelope -> sends[0]++);
            return null;
        })).isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("must not run in an active transaction");

        assertThat(sends[0]).isZero();
        String state = appScope.execute(TENANT, jdbc -> jdbc.queryForObject(
                "SELECT delivery_state FROM platform.outbox_event WHERE event_id=?",
                String.class,event));
        assertThat(state).isEqualTo("PENDING");
    }

    @Test
    void emptyTenantQueueCannotSendForeignTenantEvents() {
        UUID event=seed();
        int[] sends={0};
        assertThat(delivery.dispatchNext(OTHER,"other-worker",30,envelope -> sends[0]++))
                .isFalse();
        assertThat(sends[0]).isZero();
        assertThat(count("platform.audit_fact",event)).isZero();
    }
}
