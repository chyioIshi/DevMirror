class MockNotFoundError(Exception):
    """Выбрасывается, когда искомый мок не найден."""
    pass

class CreateMockError(Exception):
    """Выбрасывается, когда при создании мока произошла ошибка (нарушен инвариант агрегата)."""
    pass