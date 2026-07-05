"""Risk-based approval policies."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class RiskLevel(str, Enum):
    """Risk levels for actions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ApprovalPolicy:
    """Policy for requiring approval based on risk level."""
    risk_level: RiskLevel
    requires_approval: bool = True
    approvers: list[str] = field(default_factory=list)
    auto_approve: bool = False
    description: str = ""

    @classmethod
    def for_action(
        cls,
        action: str,
        risk_threshold: RiskLevel = RiskLevel.MEDIUM,
    ) -> ApprovalPolicy:
        """Determine approval policy for an action."""
        risk = cls.calculate_risk(action)
        
        return cls(
            risk_level=risk,
            requires_approval=risk.value >= risk_threshold.value,
            description=f"Risk level for '{action}': {risk.value}",
        )

    @classmethod
    def calculate_risk(cls, action: str) -> RiskLevel:
        """Calculate risk level for an action."""
        action_lower = action.lower()
        
        critical_patterns = [
            r"rm\s+-rf",
            r"drop\s+table",
            r"delete\s+.*database",
            r"sudo\s+",
            r"chmod\s+777",
            r"rm\s+/\s*",
        ]
        
        high_patterns = [
            r"git\s+push\s+--force",
            r"docker\s+rm\s+-f",
            r"kubectl\s+delete",
            r"rm\s+-r",
            r"shutdown",
            r"reboot",
            r"deploy",
            r"release",
        ]
        
        medium_patterns = [
            r"git\s+push",
            r"docker\s+run",
            r"kubectl\s+apply",
            r"curl\s+",
            r"wget\s+",
            r"pip\s+install",
            r"npm\s+install",
            r"write\s+file",
            r"edit\s+file",
        ]
        
        for pattern in critical_patterns:
            if re.search(pattern, action_lower):
                return RiskLevel.CRITICAL
        
        for pattern in high_patterns:
            if re.search(pattern, action_lower):
                return RiskLevel.HIGH
        
        for pattern in medium_patterns:
            if re.search(pattern, action_lower):
                return RiskLevel.MEDIUM
        
        return RiskLevel.LOW


@dataclass
class ApprovalRule:
    """A rule for determining approval requirements."""
    name: str
    pattern: str
    risk_level: RiskLevel
    description: str = ""
    enabled: bool = True

    def matches(self, action: str) -> bool:
        """Check if action matches this rule."""
        if not self.enabled:
            return False
        return bool(re.search(self.pattern, action, re.IGNORECASE))


class PolicyEngine:
    """Engine for evaluating approval policies."""

    def __init__(self):
        self._rules: list[ApprovalRule] = []
        self._default_risk_level = RiskLevel.MEDIUM
        self._default_requires_approval = True

    def add_rule(self, rule: ApprovalRule) -> None:
        """Add an approval rule."""
        self._rules.append(rule)

    def remove_rule(self, name: str) -> bool:
        """Remove an approval rule."""
        for i, rule in enumerate(self._rules):
            if rule.name == name:
                del self._rules[i]
                return True
        return False

    def evaluate(self, action: str) -> ApprovalPolicy:
        """Evaluate an action against policies."""
        for rule in reversed(self._rules):
            if rule.matches(action):
                return ApprovalPolicy(
                    risk_level=rule.risk_level,
                    requires_approval=True,
                    description=rule.description or f"Matched rule: {rule.name}",
                )
        
        calculated_risk = ApprovalPolicy.calculate_risk(action)
        
        return ApprovalPolicy(
            risk_level=calculated_risk,
            requires_approval=calculated_risk != RiskLevel.LOW,
            description=f"Default policy for risk level: {calculated_risk.value}",
        )

    def should_require_approval(
        self,
        action: str,
        risk_threshold: RiskLevel = RiskLevel.MEDIUM,
    ) -> tuple[bool, RiskLevel]:
        """Determine if approval should be required."""
        policy = self.evaluate(action)
        return policy.requires_approval, policy.risk_level


DEFAULT_POLICY_ENGINE = PolicyEngine()
DEFAULT_POLICY_ENGINE.add_rule(ApprovalRule(
    name="delete_all",
    pattern=r"rm\s+-rf|delete\s+\*|drop\s+table\s+\*",
    risk_level=RiskLevel.CRITICAL,
    description="Deleting all resources",
))

DEFAULT_POLICY_ENGINE.add_rule(ApprovalRule(
    name="system_commands",
    pattern=r"sudo|chmod\s+777|shutdown|reboot",
    risk_level=RiskLevel.HIGH,
    description="System-level commands",
))

DEFAULT_POLICY_ENGINE.add_rule(ApprovalRule(
    name="deployment",
    pattern=r"deploy|release|publish\s+docker",
    risk_level=RiskLevel.HIGH,
    description="Deployment operations",
))