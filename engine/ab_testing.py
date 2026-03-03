"""A/B Testing framework for antifraud rules.

Allows running rule variants in parallel to compare effectiveness.
Tracks: control vs variant, conversion rates, false positives, latency.
"""

import time
import json
import random
from typing import Dict, List, Tuple
from dataclasses import dataclass, field
import redis

@dataclass
class RuleVariant:
    """Represents a rule variant for A/B testing."""
    variant_id: str
    rule_id: str
    version: str  # "control" or "variant_v1", "variant_v2", etc
    conditions: Dict
    actions: List[str]
    enabled: bool = True
    sample_rate: float = 1.0  # % of traffic to test (0.0-1.0)
    created_at: float = field(default_factory=time.time)

@dataclass
class ExperimentMetrics:
    """Aggregated metrics for an experiment."""
    variant_id: str
    rule_id: str
    total_evaluations: int = 0
    triggered_count: int = 0
    false_positives: int = 0
    true_positives: int = 0
    avg_latency_ms: float = 0.0
    conversion_rate: float = 0.0  # true_positives / triggered_count


class ABTestingEngine:
    """Manage A/B tests for rule variants."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)
        self.experiments: Dict[str, List[RuleVariant]] = {}
        self.metrics: Dict[str, ExperimentMetrics] = {}

    def create_experiment(self, rule_id: str, control: Dict, variants: List[Dict]) -> str:
        """Start a new experiment with control + variants.
        
        Args:
            rule_id: Base rule ID
            control: Control rule condition/actions
            variants: List of variant dicts with 'version', 'conditions', 'actions'
            
        Returns:
            Experiment ID
        """
        experiment_id = f"exp_{rule_id}_{int(time.time())}"
        
        # Create control variant
        control_variant = RuleVariant(
            variant_id=f"{experiment_id}_control",
            rule_id=rule_id,
            version="control",
            conditions=control.get("conditions", {}),
            actions=control.get("actions", [])
        )
        
        # Create test variants
        variant_list = [control_variant]
        for v in variants:
            test_variant = RuleVariant(
                variant_id=f"{experiment_id}_{v['version']}",
                rule_id=rule_id,
                version=v['version'],
                conditions=v.get("conditions", {}),
                actions=v.get("actions", []),
                sample_rate=v.get("sample_rate", 0.5)
            )
            variant_list.append(test_variant)
        
        self.experiments[experiment_id] = variant_list
        
        # Store in Redis for persistence
        self.redis.hset(
            f"experiment:{experiment_id}",
            mapping={
                "rule_id": rule_id,
                "control": json.dumps(control),
                "variants": json.dumps([v.__dict__ for v in variant_list]),
                "created_at": time.time()
            }
        )
        
        return experiment_id

    def select_variant(self, experiment_id: str) -> RuleVariant:
        """Select a variant for this evaluation (control vs test).
        
        Uses bucket sampling: control gets (1-sum(sample_rates)) traffic,
        variants get their allocated sample_rate.
        """
        if experiment_id not in self.experiments:
            return None
        
        variants = self.experiments[experiment_id]
        control = variants[0]  # First is always control
        test_variants = variants[1:]
        
        rand = random.random()
        cumulative = 0
        
        # Test variants get their sample_rate
        for variant in test_variants:
            if rand < cumulative + variant.sample_rate:
                return variant
            cumulative += variant.sample_rate
        
        # Control gets the rest
        return control

    def record_evaluation(
        self,
        experiment_id: str,
        variant: RuleVariant,
        triggered: bool,
        latency_ms: float,
        label: str = None  # "true_positive", "false_positive", "true_negative"
    ):
        """Record the outcome of a rule evaluation."""
        key = f"exp_metrics:{variant.variant_id}"
        
        # Increment counters
        self.redis.hincrby(key, "total_evaluations", 1)
        if triggered:
            self.redis.hincrby(key, "triggered_count", 1)
        
        if label == "false_positive":
            self.redis.hincrby(key, "false_positives", 1)
        elif label == "true_positive":
            self.redis.hincrby(key, "true_positives", 1)
        
        # Track latency (moving average)
        self.redis.hincrbyfloat(key, "total_latency", latency_ms)

    def get_metrics(self, experiment_id: str) -> Dict[str, ExperimentMetrics]:
        """Get aggregated metrics for all variants in experiment."""
        results = {}
        
        if experiment_id not in self.experiments:
            return results
        
        for variant in self.experiments[experiment_id]:
            key = f"exp_metrics:{variant.variant_id}"
            raw = self.redis.hgetall(key)
            
            if not raw:
                continue
            
            total = int(raw.get(b"total_evaluations", 0))
            triggered = int(raw.get(b"triggered_count", 0))
            true_pos = int(raw.get(b"true_positives", 0))
            false_pos = int(raw.get(b"false_positives", 0))
            total_latency = float(raw.get(b"total_latency", 0))
            
            metrics = ExperimentMetrics(
                variant_id=variant.variant_id,
                rule_id=variant.rule_id,
                total_evaluations=total,
                triggered_count=triggered,
                true_positives=true_pos,
                false_positives=false_pos,
                avg_latency_ms=total_latency / max(total, 1),
                conversion_rate=true_pos / max(triggered, 1)
            )
            
            results[variant.version] = metrics
        
        return results

    def stop_experiment(self, experiment_id: str, winning_variant: str = None) -> Dict:
        """End experiment and optionally promote winning variant.
        
        Returns summary with winner + metrics.
        """
        metrics = self.get_metrics(experiment_id)
        
        if not metrics:
            return {"status": "no_data"}
        
        # Determine winner if not specified
        if not winning_variant:
            # Winner = highest conversion_rate with low false_positive_rate
            candidates = {
                v: m.conversion_rate - (m.false_positives / max(m.triggered_count, 1))
                for v, m in metrics.items()
            }
            winning_variant = max(candidates, key=candidates.get)
        
        # Archive experiment
        self.redis.hset(
            f"experiment_archived:{experiment_id}",
            mapping={
                "winning_variant": winning_variant,
                "metrics": json.dumps({k: v.__dict__ for k, v in metrics.items()}),
                "ended_at": time.time()
            }
        )
        
        return {
            "experiment_id": experiment_id,
            "winner": winning_variant,
            "metrics": metrics
        }


# Example usage
if __name__ == "__main__":
    ab = ABTestingEngine()
    
    # Create experiment: compare 2 rule variants for honeypot detection
    exp_id = ab.create_experiment(
        rule_id="honeypot_detection",
        control={
            "conditions": {"has_signal": "honeypot", "velocity_gt": 20},
            "actions": ["kick"]
        },
        variants=[
            {
                "version": "variant_stricter",
                "conditions": {"has_signal": "honeypot", "velocity_gt": 10},  # Lower threshold
                "actions": ["kick"],
                "sample_rate": 0.3  # Test with 30% traffic
            },
            {
                "version": "variant_warning_first",
                "conditions": {"has_signal": "honeypot", "velocity_gt": 20},
                "actions": ["shadow_mute"],  # Softer action first
                "sample_rate": 0.2  # Test with 20% traffic
            }
        ]
    )
    
    print(f"Experiment started: {exp_id}")
    
    # Simulate 100 evaluations
    for i in range(100):
        variant = ab.select_variant(exp_id)
        triggered = random.random() < 0.3  # 30% trigger rate
        latency = random.uniform(10, 100)
        label = "true_positive" if triggered else None
        
        ab.record_evaluation(exp_id, variant, triggered, latency, label)
    
    # Get results
    print("\n=== Experiment Results ===")
    results = ab.get_metrics(exp_id)
    for version, metrics in results.items():
        print(f"\n{version}:")
        print(f"  Total evaluations: {metrics.total_evaluations}")
        print(f"  Trigger rate: {metrics.triggered_count / max(metrics.total_evaluations, 1) * 100:.1f}%")
        print(f"  Conversion rate: {metrics.conversion_rate * 100:.1f}%")
        print(f"  False positives: {metrics.false_positives}")
        print(f"  Avg latency: {metrics.avg_latency_ms:.2f}ms")
    
    # End experiment
    summary = ab.stop_experiment(exp_id)
    print(f"\n✅ Winner: {summary['winner']}")
