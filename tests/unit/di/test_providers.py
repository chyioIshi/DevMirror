from app.config import AppSettings
from app.di import providers
from app.di.container import AppContainer


class TestDependencyProviders:
    """Проверяет DI provider-функции."""

    def test_get_app_settings_returns_container_settings(self) -> None:
        """Проверяет получение настроек приложения."""
        container = AppContainer(settings=AppSettings())

        result = providers.get_app_settings(container)

        assert result is container.settings

    def test_get_mock_management_service_returns_container_service(self) -> None:
        """Проверяет получение сервиса управления моками."""
        container = AppContainer(settings=AppSettings())

        result = providers.get_mock_management_service(container)

        assert result is container.mock_management_service

    def test_get_mock_resolver_service_returns_container_service(self) -> None:
        """Проверяет получение сервиса резолва моков."""
        container = AppContainer(settings=AppSettings())

        result = providers.get_mock_resolver_service(container)

        assert result is container.mock_resolver_service

    def test_get_mock_response_builder_returns_container_builder(self) -> None:
        """Проверяет получение билдера HTTP-ответов."""
        container = AppContainer(settings=AppSettings())

        result = providers.get_mock_response_builder(container)

        assert result is container.mock_response_builder

    def test_get_request_log_service_returns_container_service(self) -> None:
        """Проверяет получение сервиса журнала запросов."""
        container = AppContainer(settings=AppSettings())

        result = providers.get_request_log_service(container)

        assert result is container.request_log_service

    def test_get_request_context_resolver_returns_container_resolver(self) -> None:
        """Проверяет получение резолвера контекста запроса."""
        container = AppContainer(settings=AppSettings())

        result = providers.get_request_context_resolver(container)

        assert result is container.request_context_resolver
