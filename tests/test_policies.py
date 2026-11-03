import pytest

from emporio_agent.policies import PolicyTopic, load_policy


@pytest.mark.parametrize("topic", list(PolicyTopic))
def test_every_topic_has_a_section(topic):
    assert load_policy(topic).startswith("# ")


def test_payment_section_follows_specific_installment_rule():
    text = load_policy(PolicyTopic.PAYMENT)
    assert "De 4x a 6x" in text and "R$ 80,00" in text
