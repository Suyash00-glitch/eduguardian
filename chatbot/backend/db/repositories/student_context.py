"""
StudentContextRepository — Persistence, Caching, and Teammate Integration for Student Academic Context.

Features:
  - Student-level scoped caching with configurable TTL (default: 3600 seconds)
  - Thread-safe and async-safe in-memory cache with automatic stale eviction
  - Cache reuse across multiple conversations for the same authenticated student
  - Extensible data provider interface (AcademicDataProvider)
  - Safe, non-fabricating baseline fallback on any database / network / integration failure
  - Strict student identity isolation (no cross-student data contamination)
"""
from __future__ import annotations

import abc
import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any

from chatbot.backend.config import get_settings
from chatbot.backend.schemas.student import StudentContext

logger = logging.getLogger(__name__)


# ── Cache Layer Interfaces & Implementation ──────────────────────────────────

@dataclass
class CacheEntry:
    """Represents a cached StudentContext with its absolute expiration timestamp."""
    context: StudentContext
    expires_at: float

    @property
    def is_expired(self) -> bool:
        return time.time() >= self.expires_at


class BaseStudentContextCache(abc.ABC):
    """Abstract base class for student context caching."""

    @abc.abstractmethod
    async def get(self, student_id: str) -> StudentContext | None:
        """Retrieve cached StudentContext if present and unexpired."""
        ...

    @abc.abstractmethod
    async def set(self, student_id: str, context: StudentContext, ttl_seconds: int) -> None:
        """Store StudentContext in cache with specified TTL."""
        ...

    @abc.abstractmethod
    async def invalidate(self, student_id: str) -> None:
        """Evict cached context for a specific student."""
        ...

    @abc.abstractmethod
    async def clear(self) -> None:
        """Clear all cached entries."""
        ...


class InMemoryStudentContextCache(BaseStudentContextCache):
    """
    Thread-safe and async-safe in-memory TTL cache for StudentContext.
    Keys are strictly formatted by student_id to prevent cross-tenant contamination.
    """

    def __init__(self) -> None:
        self._cache: dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()

    async def get(self, student_id: str) -> StudentContext | None:
        async with self._lock:
            entry = self._cache.get(student_id)
            if entry is None:
                return None
            if entry.is_expired:
                logger.debug("InMemoryStudentContextCache: Expired entry for student_id=%s. Evicting.", student_id)
                del self._cache[student_id]
                return None
            return entry.context

    async def set(self, student_id: str, context: StudentContext, ttl_seconds: int) -> None:
        expires_at = time.time() + max(1, ttl_seconds)
        async with self._lock:
            self._cache[student_id] = CacheEntry(context=context, expires_at=expires_at)
            logger.debug(
                "InMemoryStudentContextCache: Cached context for student_id=%s (TTL=%ds, expires_at=%.1f)",
                student_id,
                ttl_seconds,
                expires_at,
            )

    async def invalidate(self, student_id: str) -> None:
        async with self._lock:
            if student_id in self._cache:
                del self._cache[student_id]
                logger.debug("InMemoryStudentContextCache: Invalidated cache for student_id=%s", student_id)

    async def clear(self) -> None:
        async with self._lock:
            self._cache.clear()
            logger.debug("InMemoryStudentContextCache: Cleared all entries.")


# ── Academic Data Provider Interface & Teammate Seam ──────────────────────────

class AcademicDataProvider(abc.ABC):
    """
    Abstract interface for retrieving academic records from external or internal sources.
    """

    @abc.abstractmethod
    async def fetch_student_context(self, student_id: str) -> StudentContext | None:
        """
        Fetches the complete academic record for the student.
        Returns a populated StudentContext or None if not found / unavailable.
        """
        ...


class PortalAcademicDataProvider(AcademicDataProvider):
    """
    Primary integration seam for connecting to the university student portal.
    
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║  TEAMMATE INTEGRATION POINT                                              ║
    ║                                                                          ║
    ║  When the university portal database or REST endpoint is available:      ║
    ║    1. Query the portal database or HTTP API using `student_id`.          ║
    ║    2. Map the columns/JSON into the `StudentContext` Pydantic model.     ║
    ║    3. Return the populated `StudentContext`.                             ║
    ║                                                                          ║
    ║  If no records exist for the student, return None.                       ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    """

    async def fetch_student_context(self, student_id: str) -> StudentContext | None:
        # Currently, portal DB / endpoint is pending integration by the portal teammate.
        # Raising NotImplementedError here cleanly signals the repository to use the safe baseline.
        raise NotImplementedError(
            "PortalAcademicDataProvider: University student portal data source is not yet connected."
        )


# ── StudentContextRepository ──────────────────────────────────────────────────

class StudentContextRepository:
    """
    Repository that manages student academic context resolution, TTL caching,
    and fallback safety.
    """

    def __init__(
        self,
        provider: AcademicDataProvider | None = None,
        cache: BaseStudentContextCache | None = None,
        ttl_seconds: int | None = None,
    ) -> None:
        settings = get_settings()
        self._provider = provider or PortalAcademicDataProvider()
        self._cache = cache or InMemoryStudentContextCache()
        self._ttl_seconds = ttl_seconds or settings.student_context_cache_ttl_seconds

    @property
    def cache(self) -> BaseStudentContextCache:
        return self._cache

    @property
    def provider(self) -> AcademicDataProvider:
        return self._provider

    def set_provider(self, provider: AcademicDataProvider) -> None:
        """Dynamically update or inject a custom academic data provider (useful for testing or switching sources)."""
        self._provider = provider

    def _create_baseline_context(self, student_id: str) -> StudentContext:
        """
        Creates a safe, non-hallucinating baseline StudentContext when real
        records are unavailable.
        """
        return StudentContext(
            student_id=student_id,
            student_name="",
        )

    async def get_context(self, student_id: str) -> StudentContext:
        """
        Resolves academic records for `student_id`:
        1. Checks cache for unexpired context.
        2. On cache miss, attempts to fetch fresh data from the provider.
        3. Caches valid data for `self._ttl_seconds`.
        4. If retrieval fails or is not implemented, returns safe baseline without fabricating data.
        """
        clean_student_id = (student_id or "").strip()
        if not clean_student_id:
            logger.warning("StudentContextRepository: Empty student_id provided. Returning blank baseline.")
            return self._create_baseline_context("unknown")

        # 1. Check Cache
        try:
            cached_context = await self._cache.get(clean_student_id)
            if cached_context is not None:
                logger.debug("StudentContextRepository: Cache HIT for student_id=%s", clean_student_id)
                return cached_context
        except Exception as cache_err:
            logger.warning("StudentContextRepository: Cache read error (%s). Proceeding to provider.", cache_err)

        logger.info("StudentContextRepository: Cache MISS for student_id=%s. Fetching fresh context...", clean_student_id)

        # 2. Fetch from Academic Data Provider
        try:
            context = await self._provider.fetch_student_context(clean_student_id)
            if context is not None:
                # Ensure identity consistency
                if context.student_id != clean_student_id:
                    logger.error(
                        "StudentContextRepository: Provider returned mismatched student_id=%s for query=%s. Rejecting payload.",
                        context.student_id,
                        clean_student_id,
                    )
                    return self._create_baseline_context(clean_student_id)

                # Store in cache
                try:
                    await self._cache.set(clean_student_id, context, self._ttl_seconds)
                except Exception as cache_write_err:
                    logger.warning("StudentContextRepository: Cache write error (%s).", cache_write_err)

                return context

            logger.info("StudentContextRepository: No academic records found for student_id=%s. Using baseline.", clean_student_id)
            baseline = self._create_baseline_context(clean_student_id)
            # Cache baseline for a short period to prevent repeated hammering
            await self._cache.set(clean_student_id, baseline, min(self._ttl_seconds, 300))
            return baseline

        except NotImplementedError:
            logger.debug(
                "StudentContextRepository: Real data source not yet connected for student_id=%s. Returning baseline.",
                clean_student_id,
            )
            baseline = self._create_baseline_context(clean_student_id)
            # Cache baseline for standard TTL
            await self._cache.set(clean_student_id, baseline, self._ttl_seconds)
            return baseline

        except Exception as exc:
            logger.error(
                "StudentContextRepository: Failed to fetch academic context for student_id=%s: %s",
                clean_student_id,
                exc,
            )
            baseline = self._create_baseline_context(clean_student_id)
            return baseline
