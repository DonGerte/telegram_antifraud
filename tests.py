#!/usr/bin/env python3
"""
Simple tests for Telegram Antifraud System
Run with: python tests.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.risk_assessment import assess_user_risk, RiskLevel
from engine import scoring


def test_imports():
    """Test that all modules can be imported"""
    try:
        from services import memory, strike_manager, ban_manager
        from engine import scoring
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False


def test_risk_assessment():
    """Test risk assessment functionality"""
    try:
        # Test basic risk assessment
        risk = assess_user_risk(12345, -100123, "hello world")
        assert 'level' in risk
        assert 'score' in risk
        assert isinstance(risk['level'], str)
        print("✓ Risk assessment working")
        return True
    except Exception as e:
        print(f"✗ Risk assessment error: {e}")
        return False


def test_scoring():
    """Test scoring system"""
    try:
        from engine import scoring

        # Test adding signals
        scoring.add_signal(12345, "test", 0.5, -100123)
        score = scoring.compute_score(12345)
        assert isinstance(score, float)
        assert score >= 0

        print("✓ Scoring system working")
        return True
    except Exception as e:
        print(f"✗ Scoring error: {e}")
        return False


def test_strike_system():
    """Test strike system logic"""
    try:
        from services import strike_manager

        # Test strike action values
        assert hasattr(strike_manager.StrikeAction, 'WARNING')
        assert hasattr(strike_manager.StrikeAction, 'MUTE')
        assert hasattr(strike_manager.StrikeAction, 'BAN')

        print("✓ Strike system structure correct")
        return True
    except Exception as e:
        print(f"✗ Strike system error: {e}")
        return False


def run_tests():
    """Run all tests"""
    print("🧪 Running Telegram Antifraud System Tests")
    print("=" * 50)

    tests = [
        test_imports,
        test_risk_assessment,
        test_scoring,
        test_strike_system
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)