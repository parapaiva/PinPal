"""Event type string constants (open set, not enum).

Using plain strings keeps the set extensible without schema migrations.
"""

GROUP_IMPORTED = "pinpal.group.imported.v1"
MEMBERSHIP_OBSERVED = "pinpal.membership.observed.v1"
IDENTITY_LINKED = "pinpal.identity.linked.v1"
FACT_RECORDED = "pinpal.fact.recorded.v1"
RELATIONSHIP_SUGGESTED = "pinpal.relationship.suggested.v1"
FOLLOW_OBSERVED = "pinpal.follow.observed.v1"
OBSERVATION_RECORDED = "pinpal.observation.recorded.v1"
