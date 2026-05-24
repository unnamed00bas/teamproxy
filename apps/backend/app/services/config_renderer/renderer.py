"""Orchestrates rendering, revision storage, diffing and applying configs.

This is the proxy-agnostic seam: today it renders Traefik dynamic files, but the
public surface (``render``, ``preview``, ``apply``) does not leak Traefik
specifics, so a different ingress can be plugged in later.
"""

from __future__ import annotations

import difflib
import hashlib
import os
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.enums import ConfigKind
from app.models.generated_config import GeneratedConfig
from app.models.publication import Publication
from app.services.config_renderer.traefik import (
    PublicationData,
    RenderInput,
    ServiceData,
    find_domain_conflicts,
    render_traefik_dynamic,
)


def _checksum(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


async def build_render_input(session: AsyncSession) -> RenderInput:
    result = await session.execute(
        select(Publication).options(selectinload(Publication.service))
    )
    publications = result.scalars().all()
    pub_data: list[PublicationData] = []
    for pub in publications:
        svc = pub.service
        if svc is None:
            continue
        pub_data.append(
            PublicationData(
                id=pub.id,
                service=ServiceData(
                    id=svc.id,
                    slug=svc.slug,
                    protocol_type=svc.protocol_type,
                    backend_host=svc.backend_host,
                    backend_port=svc.backend_port,
                    backend_scheme=svc.backend_scheme,
                    enabled=svc.enabled,
                ),
                entrypoint_type=pub.entrypoint_type,
                domain_or_sni=pub.domain_or_sni,
                path_prefix=pub.path_prefix,
                tls_enabled=pub.tls_enabled,
                tls_mode=pub.tls_mode,
                published_port=pub.published_port,
                public_enabled=pub.public_enabled,
                maintenance_mode=pub.maintenance_mode,
                priority=pub.priority,
                middleware_profile=pub.middleware_profile,
            )
        )
    return RenderInput(publications=pub_data)


class ConfigRenderer:
    """High-level operations over generated configurations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _next_revision(self) -> int:
        result = await self.session.execute(
            select(GeneratedConfig.revision)
            .where(GeneratedConfig.kind == ConfigKind.traefik_dynamic)
            .order_by(GeneratedConfig.revision.desc())
            .limit(1)
        )
        last = result.scalar_one_or_none()
        return (last or 0) + 1

    async def _latest(self) -> GeneratedConfig | None:
        result = await self.session.execute(
            select(GeneratedConfig)
            .where(GeneratedConfig.kind == ConfigKind.traefik_dynamic)
            .order_by(GeneratedConfig.revision.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def render_current(self) -> tuple[str, list[str]]:
        """Render config from current DB state. Returns (content, conflicts)."""
        render_input = await build_render_input(self.session)
        content = render_traefik_dynamic(render_input)
        conflicts = find_domain_conflicts(render_input)
        return content, conflicts

    async def preview(self) -> tuple[str, str, list[str]]:
        """Return (content, diff-vs-latest, conflicts) without persisting."""
        content, conflicts = await self.render_current()
        latest = await self._latest()
        diff = self._diff(latest.content if latest else "", content)
        return content, diff, conflicts

    async def render_and_store(self) -> GeneratedConfig:
        """Render and persist a new revision (only if content changed)."""
        content, _ = await self.render_current()
        checksum = _checksum(content)
        latest = await self._latest()
        if latest and latest.checksum == checksum:
            return latest
        revision = await self._next_revision()
        config = GeneratedConfig(
            revision=revision,
            kind=ConfigKind.traefik_dynamic,
            content=content,
            checksum=checksum,
            applied=False,
        )
        self.session.add(config)
        await self.session.flush()
        return config

    async def apply(self, config: GeneratedConfig | None = None) -> GeneratedConfig:
        """Write the config to the dynamic directory so Traefik hot-reloads it.

        Traefik watches the file provider directory, so writing the file is the
        whole 'reload' — no process restart needed.
        """
        if config is None:
            config = await self.render_and_store()
        try:
            os.makedirs(settings.traefik_dynamic_dir, exist_ok=True)
            target = os.path.join(settings.traefik_dynamic_dir, "control-plane.yml")
            tmp = target + ".tmp"
            with open(tmp, "w", encoding="utf-8") as handle:
                handle.write(config.content)
            os.replace(tmp, target)  # atomic swap
            config.applied = True
            config.applied_at = datetime.now(UTC)
            config.apply_error = None
        except OSError as exc:  # pragma: no cover - filesystem dependent
            config.apply_error = str(exc)
            config.applied = False
        await self.session.flush()
        return config

    async def diff_revisions(self, from_rev: int | None, to_rev: int) -> str:
        to_config = await self._get_revision(to_rev)
        if to_config is None:
            raise ValueError(f"Revision {to_rev} not found")
        from_content = ""
        if from_rev is not None:
            from_config = await self._get_revision(from_rev)
            from_content = from_config.content if from_config else ""
        return self._diff(from_content, to_config.content)

    async def rollback_to(self, revision: int) -> GeneratedConfig:
        """Re-apply a previous revision as a new revision."""
        target = await self._get_revision(revision)
        if target is None:
            raise ValueError(f"Revision {revision} not found")
        new_revision = await self._next_revision()
        clone = GeneratedConfig(
            revision=new_revision,
            kind=ConfigKind.traefik_dynamic,
            content=target.content,
            checksum=target.checksum,
            applied=False,
        )
        self.session.add(clone)
        await self.session.flush()
        return await self.apply(clone)

    async def _get_revision(self, revision: int) -> GeneratedConfig | None:
        result = await self.session.execute(
            select(GeneratedConfig).where(
                GeneratedConfig.kind == ConfigKind.traefik_dynamic,
                GeneratedConfig.revision == revision,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _diff(old: str, new: str) -> str:
        return "".join(
            difflib.unified_diff(
                old.splitlines(keepends=True),
                new.splitlines(keepends=True),
                fromfile="previous",
                tofile="current",
            )
        )
