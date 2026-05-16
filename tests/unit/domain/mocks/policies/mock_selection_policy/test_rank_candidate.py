from app.domain.mocks.models.resolution import RuleMatchResult


class TestRankCandidate:
    """Проверяет расчет ранга кандидата."""

    def test_priority_reflects_mock_priority(
        self,
        policy,
        mock_factory,
        zero_score_result,
    ) -> None:
        """Проверяет, что priority берется из мока."""
        mock = mock_factory.create_mock(priority=10)
        rank = policy.rank_candidate(
            mock,
            requested_scope="global",
            rule_result=zero_score_result,
        )

        assert rank.priority == 10

    def test_scope_rank_is_one_when_scopes_match(
        self,
        policy,
        mock_factory,
        zero_score_result,
    ) -> None:
        """Проверяет, что совпавший scope получает rank 1."""
        mock = mock_factory.create_mock(scope="user-1")
        rank = policy.rank_candidate(
            mock,
            requested_scope="user-1",
            rule_result=zero_score_result,
        )

        assert rank.scope_rank == 1

    def test_scope_rank_is_zero_when_scopes_differ(
        self,
        policy,
        mock_factory,
        zero_score_result,
    ) -> None:
        """Проверяет, что несовпавший scope получает rank 0."""
        mock = mock_factory.create_mock(scope="global")
        rank = policy.rank_candidate(
            mock,
            requested_scope="user-1",
            rule_result=zero_score_result,
        )

        assert rank.scope_rank == 0

    def test_specificity_equals_number_of_match_rules(
        self,
        policy,
        mock_factory,
        zero_score_result,
    ) -> None:
        """Проверяет, что specificity равно числу правил."""
        mock = mock_factory.create_mock()
        rank = policy.rank_candidate(
            mock,
            requested_scope="global",
            rule_result=zero_score_result,
        )

        assert rank.specificity == len(mock.match_rules)

    def test_rule_score_comes_from_rule_result(
        self,
        policy,
        mock_factory,
    ) -> None:
        """Проверяет, что rule_score берется из результата матчинга."""
        mock = mock_factory.create_mock()
        rank = policy.rank_candidate(
            mock,
            requested_scope="global",
            rule_result=RuleMatchResult(matched=True, score=42),
        )

        assert rank.rule_score == 42
