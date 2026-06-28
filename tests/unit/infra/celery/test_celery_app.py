import pytest
from pydantic import ValidationError

from app.config import AppSettings
from app.infra.celery.app import create_celery_app


class TestCeleryApp:
    def test_create_celery_app_uses_settings(self) -> None:
        settings = AppSettings(
            celery_broker_url="redis://redis:6379/2",
            celery_result_backend="redis://redis:6379/3",
            celery_task_queue="custom-side-effects",
            celery_task_acks_late=True,
            celery_task_reject_on_worker_lost=True,
            celery_task_time_limit=30,
            celery_task_soft_time_limit=25,
        )

        result = create_celery_app(settings=settings)

        assert result.conf.broker_url == "redis://redis:6379/2"
        assert result.conf.result_backend == "redis://redis:6379/3"
        assert set(result.conf.include) == {
            "app.infra.celery.tasks.side_effects",
            "app.infra.celery.signals",
        }
        assert result.conf.task_default_queue == "custom-side-effects"
        assert result.conf.task_acks_late is True
        assert result.conf.task_reject_on_worker_lost is True
        assert result.conf.task_time_limit == 30
        assert result.conf.task_soft_time_limit == 25

    def test_settings_reject_soft_time_limit_greater_than_hard_limit(self) -> None:
        with pytest.raises(ValidationError, match="celery_task_soft_time_limit"):
            AppSettings(
                celery_task_time_limit=10,
                celery_task_soft_time_limit=11,
            )
