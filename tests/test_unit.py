"""
Unit tests — no database required.
Tests cover password hashing, Pydantic schema validation,
factory pattern, and individual calculation operations.
"""
import pytest
from pydantic import ValidationError

from app.auth import hash_password, verify_password
from app.schemas import UserCreate, UserRead, CalculationCreate
from app.calculator import (
    OperationType,
    AddOperation,
    SubOperation,
    MultiplyOperation,
    DivideOperation,
    CalculationFactory,
)


# ── Password hashing ─────────────────────────────────────────────────────────

def test_hash_password_returns_string():
    assert isinstance(hash_password("secret123"), str)


def test_hash_is_not_plaintext():
    assert hash_password("secret123") != "secret123"


def test_verify_correct_password():
    hashed = hash_password("mypassword")
    assert verify_password("mypassword", hashed) is True


def test_verify_wrong_password():
    hashed = hash_password("mypassword")
    assert verify_password("wrongpassword", hashed) is False


def test_same_password_produces_different_hashes():
    h1 = hash_password("samepassword")
    h2 = hash_password("samepassword")
    assert h1 != h2


def test_hash_is_bcrypt_format():
    hashed = hash_password("test")
    assert hashed.startswith("$2b$")


# ── UserCreate schema ────────────────────────────────────────────────────────

def test_user_create_valid():
    user = UserCreate(username="alice", email="alice@example.com", password="secret")
    assert user.username == "alice"


def test_user_create_invalid_email():
    with pytest.raises(ValidationError):
        UserCreate(username="alice", email="not-an-email", password="secret")


def test_user_create_missing_password():
    with pytest.raises(ValidationError):
        UserCreate(username="alice", email="alice@example.com")


# ── UserRead schema ──────────────────────────────────────────────────────────

def test_user_read_has_no_password_field():
    fields = set(UserRead.model_fields.keys())
    assert "password" not in fields
    assert "password_hash" not in fields


def test_user_read_has_required_fields():
    fields = set(UserRead.model_fields.keys())
    assert {"id", "username", "email"}.issubset(fields)


# ── Individual operation classes ─────────────────────────────────────────────

def test_add_operation():
    assert AddOperation().compute(3, 4) == 7


def test_add_operation_negative():
    assert AddOperation().compute(-5, 3) == -2


def test_sub_operation():
    assert SubOperation().compute(10, 4) == 6


def test_sub_operation_negative_result():
    assert SubOperation().compute(2, 9) == -7


def test_multiply_operation():
    assert MultiplyOperation().compute(3, 5) == 15


def test_multiply_by_zero():
    assert MultiplyOperation().compute(100, 0) == 0


def test_divide_operation():
    assert DivideOperation().compute(10, 2) == 5.0


def test_divide_operation_float_result():
    assert DivideOperation().compute(7, 2) == 3.5


def test_divide_by_zero_raises():
    with pytest.raises(ValueError, match="Division by zero"):
        DivideOperation().compute(10, 0)


# ── CalculationFactory ───────────────────────────────────────────────────────

def test_factory_returns_add_operation():
    op = CalculationFactory.get_operation(OperationType.Add)
    assert isinstance(op, AddOperation)


def test_factory_returns_sub_operation():
    op = CalculationFactory.get_operation(OperationType.Sub)
    assert isinstance(op, SubOperation)


def test_factory_returns_multiply_operation():
    op = CalculationFactory.get_operation(OperationType.Multiply)
    assert isinstance(op, MultiplyOperation)


def test_factory_returns_divide_operation():
    op = CalculationFactory.get_operation(OperationType.Divide)
    assert isinstance(op, DivideOperation)


def test_factory_compute_add():
    assert CalculationFactory.compute(OperationType.Add, 6, 4) == 10


def test_factory_compute_sub():
    assert CalculationFactory.compute(OperationType.Sub, 10, 3) == 7


def test_factory_compute_multiply():
    assert CalculationFactory.compute(OperationType.Multiply, 4, 5) == 20


def test_factory_compute_divide():
    assert CalculationFactory.compute(OperationType.Divide, 20, 4) == 5.0


# ── CalculationCreate schema ─────────────────────────────────────────────────

def test_calculation_create_valid_add():
    calc = CalculationCreate(a=5, b=3, type="Add", user_id=1)
    assert calc.type == OperationType.Add
    assert calc.a == 5
    assert calc.b == 3


def test_calculation_create_valid_divide():
    calc = CalculationCreate(a=10, b=2, type="Divide", user_id=1)
    assert calc.type == OperationType.Divide


def test_calculation_create_divide_by_zero_rejected():
    with pytest.raises(ValidationError, match="Division by zero"):
        CalculationCreate(a=10, b=0, type="Divide", user_id=1)


def test_calculation_create_invalid_type_rejected():
    with pytest.raises(ValidationError):
        CalculationCreate(a=5, b=3, type="Power", user_id=1)


def test_calculation_create_all_types_accepted():
    for op in ["Add", "Sub", "Multiply", "Divide"]:
        b = 1 if op == "Divide" else 3
        calc = CalculationCreate(a=9, b=b, type=op, user_id=1)
        assert calc.type.value == op


def test_calculation_create_missing_type_rejected():
    with pytest.raises(ValidationError):
        CalculationCreate(a=5, b=3, user_id=1)


def test_calculation_create_missing_operand_rejected():
    with pytest.raises(ValidationError):
        CalculationCreate(a=5, type="Add", user_id=1)
