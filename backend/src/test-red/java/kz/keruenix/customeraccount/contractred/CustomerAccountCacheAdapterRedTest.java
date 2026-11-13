package kz.keruenix.customeraccount.contractred;

import java.util.UUID;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import kz.keruenix.customeraccount.cache.CustomerAccountCacheKey;
import kz.keruenix.customeraccount.cache.CustomerAccountCachePort;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * INTENTIONALLY NOT part of normal src/test/java. Compiling this with
 * -Pca-adapter-red must currently FAIL because the REAL production cache
 * port/key are absent. Not a mock, disabled success test or S2 acceptance.
 *
 * WARNING: Proposed API until DEC-CA-02 is signed. Replace only after Test
 * Review confirms exact public port and an actual cache adapter exists.
 */
@SpringBootTest
class CustomerAccountCacheAdapterRedTest {
    private static final UUID TENANT_A =
            UUID.fromString("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa");
    private static final UUID TENANT_B =
            UUID.fromString("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb");
    private static final UUID ACCOUNT_X =
            UUID.fromString("11111111-1111-1111-1111-111111111111");
    private static final UUID ACCOUNT_Y =
            UUID.fromString("22222222-2222-2222-2222-222222222222");
    private static final UUID RESOURCE = UUID.fromString("33333333-3333-3333-3333-333333333333");

    @Autowired CustomerAccountCachePort productionAdapter;

    @Test
    void cacheKeysPartitionTenantAccountResourceVersionAndGrantEpoch() {
        // Must exercise the REAL key encoder, not a test-only string builder.
        var base = new CustomerAccountCacheKey(TENANT_A, ACCOUNT_X,
                "geography", RESOURCE, 1, 1);
        String key = productionAdapter.encodeKey(base);
        assertThat(key).isNotEqualTo(productionAdapter.encodeKey(
                new CustomerAccountCacheKey(TENANT_A, ACCOUNT_Y, "geography", RESOURCE, 1, 1)));
        assertThat(key).isNotEqualTo(productionAdapter.encodeKey(
                new CustomerAccountCacheKey(TENANT_B, ACCOUNT_X, "geography", RESOURCE, 1, 1)));
        assertThat(key).isNotEqualTo(productionAdapter.encodeKey(
                new CustomerAccountCacheKey(TENANT_A, ACCOUNT_X, "documents", RESOURCE, 1, 1)));
        assertThat(key).isNotEqualTo(productionAdapter.encodeKey(
                new CustomerAccountCacheKey(TENANT_A, ACCOUNT_X, "geography", RESOURCE, 2, 1)));
        assertThat(key).isNotEqualTo(productionAdapter.encodeKey(
                new CustomerAccountCacheKey(TENANT_A, ACCOUNT_X, "geography", RESOURCE, 1, 2)));
    }

    // CA-CACHE-02/03 remain NOT executable until approved production
    // account-authorized read path, versioned grant store and cache adapter
    // are available. Required oracle is written in DEC-CA-02 matrix:
    // populate via REAL DB -> authenticated read (cache miss) -> cache hit ->
    // revoke and commit -> next read denies even if eviction is lost, while
    // payload and cross-account data remain inaccessible.
}
