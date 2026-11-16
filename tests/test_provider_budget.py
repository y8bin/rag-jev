from concurrent.futures import ThreadPoolExecutor

import pytest

from legal_rag_jev.budget import Budget, BudgetError


def rates(monkeypatch):
    monkeypatch.setattr('legal_rag_jev.budget.pricing', lambda: {
        k: {'input': 1.0, 'output': 1.0} for k in ('generation', 'judge', 'jev')})


def test_openai_generation_and_judge_share_limit_but_jev_does_not(tmp_path, monkeypatch):
    rates(monkeypatch)
    ledger = str(tmp_path / 'budget.sqlite')
    budget = Budget(ledger, 1, openai_limit=.01)
    for kind in ('generation', 'judge'):
        request = budget.reserve(kind, {'model': 'test'}, {'max_tokens': 1})
        budget.settle(request, .003)
    # Existing clients cannot bypass a persisted sublimit by omitting the option.
    reopened = Budget(ledger, 1)
    with pytest.raises(BudgetError, match='OpenAI'):
        reopened.reserve('generation', {'model': 'test'}, {'max_tokens': 1})
    request = reopened.reserve('jev', {'model': 'test'}, {'max_tokens': 1})
    reopened.settle(request, .002)
    status = reopened.summary()
    assert status['known_cost_usd'] == pytest.approx(.008)
    assert status['service_limits']['openai']['known_cost_usd'] == pytest.approx(.006)
    assert status['service_limits']['openai']['remaining_usd'] == pytest.approx(.004)
    with pytest.raises(BudgetError, match='sublimit differs'):
        Budget(ledger, 1, openai_limit=.02)


def test_parallel_openai_reservations_include_unsettled_requests(tmp_path, monkeypatch):
    rates(monkeypatch)
    ledger = str(tmp_path / 'parallel.sqlite')
    Budget(ledger, 1, openai_limit=.01)
    def reserve(i):
        try:
            return Budget(ledger, 1).reserve('generation' if i % 2 else 'judge', {'model': 'test'}, {'max_tokens': 1})
        except BudgetError:
            return None
    with ThreadPoolExecutor(max_workers=4) as pool:
        calls = list(pool.map(reserve, range(8)))
    assert sum(call is not None for call in calls) == 2
    status = Budget(ledger, 1).summary()
    assert status['unsettled_attempts'] == 2
    assert status['service_limits']['openai']['accounted_with_reservations_usd'] <= .01
