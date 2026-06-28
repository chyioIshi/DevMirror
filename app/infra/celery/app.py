"""Celery application factory for DevMirror background tasks."""

from celery import Celery  # type: ignore[import-untyped]

from app.config import AppSettings, get_app_settings


def create_celery_app(settings: AppSettings | None = None) -> Celery:
    """Create the Celery application configured from app settings."""
    app_settings = settings or get_app_settings()
    celery_app = Celery(
        "devmirror",
        broker=app_settings.celery_broker_url,
        backend=app_settings.celery_result_backend,
        include=["app.infra.celery.tasks.side_effects", "app.infra.celery.signals"],
    )
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        task_default_queue=app_settings.celery_task_queue,
        task_ignore_result=app_settings.celery_ignore_result,
        task_acks_late=app_settings.celery_task_acks_late,
        task_reject_on_worker_lost=app_settings.celery_task_reject_on_worker_lost,
        task_time_limit=app_settings.celery_task_time_limit,
        task_soft_time_limit=app_settings.celery_task_soft_time_limit,
    )
    return celery_app


celery_app = create_celery_app()
