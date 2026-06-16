"""Domain layer — bounded contexts for core business logic.

Six bounded contexts:
- claims: Claim lifecycle management, models, and persistence
- decision: Final claim adjudication aggregation
- documents: Document verification and data extraction
- fraud: Fraud signal detection and risk scoring
- member: Member identity, eligibility, and claims history
- policy: Policy terms loading and rule evaluation
"""

__all__: list[str] = []
