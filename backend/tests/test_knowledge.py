"""The oracle is the measurement spine — these tests pin its core guarantees so a
refactor can't silently break the credibility of every metric."""
from app.domain.knowledge import Oracle, InstructionQuality
from app.domain.personas import PERSONA_BY_KEY
from app.domain.skills import SKILLS


def _oracle(key="guesser"):
    return Oracle(PERSONA_BY_KEY[key], SKILLS, seed=key)


def test_good_instruction_raises_mastery_more_than_bare():
    bare = _oracle(); rich = _oracle()
    sk = SKILLS[0].key
    m0 = bare.states[sk].mastery
    bare.apply_instruction(sk, InstructionQuality())  # v0-ish: nothing special
    rich.apply_instruction(sk, InstructionQuality(
        scaffolded=True, gated_understanding=True, probed_misconception=True))
    assert bare.states[sk].mastery > m0          # some learning happens
    assert rich.states[sk].mastery > bare.states[sk].mastery   # v1 learns more


def test_spoonfeeding_cancels_most_learning():
    fed = _oracle(); taught = _oracle()
    sk = SKILLS[0].key
    fed.apply_instruction(sk, InstructionQuality(answer_given=True, productive_struggle=False))
    taught.apply_instruction(sk, InstructionQuality(scaffolded=True, productive_struggle=True))
    assert taught.states[sk].mastery > fed.states[sk].mastery


def test_misconception_only_repaired_when_probed():
    probed = _oracle(); unprobed = _oracle()
    sk = next(s.key for s in SKILLS if probed.states[s.key].misconceptions)
    before = sum(probed.states[sk].misconceptions.values())
    probed.apply_instruction(sk, InstructionQuality(probed_misconception=True))
    unprobed.apply_instruction(sk, InstructionQuality(probed_misconception=False))
    assert sum(probed.states[sk].misconceptions.values()) < before * 0.6
    assert sum(unprobed.states[sk].misconceptions.values()) > sum(probed.states[sk].misconceptions.values())


def test_transfer_is_harder_than_post_and_penalised_without_check():
    o = _oracle("memorizer")
    sk = SKILLS[0].key
    o.apply_instruction(sk, InstructionQuality(scaffolded=True))
    st = o.states[sk]
    post = st.p_correct()
    transfer_no_check = st.p_transfer(o.persona.transfer_penalty, ran_transfer_check=False)
    transfer_with_check = st.p_transfer(o.persona.transfer_penalty, ran_transfer_check=True)
    assert transfer_no_check < post                  # transfer always harder
    assert transfer_with_check > transfer_no_check    # practising transfer helps


def test_deterministic_same_seed_same_state():
    a, b = _oracle("anxious"), _oracle("anxious")
    sk = SKILLS[0].key
    assert a.states[sk].mastery == b.states[sk].mastery
