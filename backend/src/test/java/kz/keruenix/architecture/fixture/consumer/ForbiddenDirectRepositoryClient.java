package kz.keruenix.architecture.fixture.consumer;

import kz.keruenix.architecture.fixture.provider.internal.RepositoryInternal;

/** Compiles, but violates provider module encapsulation. */
public final class ForbiddenDirectRepositoryClient {
    private final RepositoryInternal forbidden = new RepositoryInternal();
    public String invoke() { return forbidden.secret(); }
}
