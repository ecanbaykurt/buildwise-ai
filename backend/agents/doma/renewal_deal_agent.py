from pydantic import BaseModel
from typing import Dict, Any, List

class Offer(BaseModel):
    rent_usd: float
    term_months: int
    incentives: List[str] = []

class RenewalPackage(BaseModel):
    primary: Offer
    alternatives: List[Offer]
    justification: str
    needs_manager_approval: bool = False

class RenewalDealAgent:
    def run(self, current_rent: float, comps_median: float, policy_floor: float, policy_ceiling: float) -> RenewalPackage:
        target = max(policy_floor, min(comps_median, policy_ceiling))
        primary = Offer(rent_usd=target, term_months=12, incentives=["touch-up paint"])
        alt1 = Offer(rent_usd=target*0.98, term_months=24, incentives=["one free month at end"])
        alt2 = Offer(rent_usd=target*1.01, term_months=12, incentives=["new appliance package"])
        approval = not (policy_floor <= primary.rent_usd <= policy_ceiling)
        just = f"Priced near market median ${comps_median:.0f}, within policy [{policy_floor:.0f}, {policy_ceiling:.0f}]."
        return RenewalPackage(primary=primary, alternatives=[alt1, alt2], justification=just, needs_manager_approval=approval)
