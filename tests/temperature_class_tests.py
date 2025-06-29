import pytest
from pysensorlinx import Temperature

def test_init_valid_celsius():
  t = Temperature(25, "C")
  assert t.value == 25.0
  assert t.unit == "C"

def test_init_valid_fahrenheit():
  t = Temperature(77, "F")
  assert t.value == 77.0
  assert t.unit == "F"

def test_init_unit_case_insensitive():
  t = Temperature(0, "f")
  assert t.unit == "F"
  t2 = Temperature(0, "c")
  assert t2.unit == "C"

def test_init_default_unit():
  t = Temperature(10)
  assert t.unit == "C"

def test_init_invalid_unit():
  with pytest.raises(ValueError):
    Temperature(10, "K")
  with pytest.raises(ValueError):
    Temperature(10, None)

def test_init_non_float_value():
  t = Temperature("42", "C")
  assert t.value == 42.0
  with pytest.raises(ValueError):
    Temperature("not_a_number", "C")

def test_to_celsius_from_celsius():
  t = Temperature(100, "C")
  assert t.to_celsius() == 100

def test_to_celsius_from_fahrenheit():
  t = Temperature(32, "F")
  assert pytest.approx(t.to_celsius(), 0.01) == 0

def test_to_fahrenheit_from_fahrenheit():
  t = Temperature(212, "F")
  assert t.to_fahrenheit() == 212

def test_to_fahrenheit_from_celsius():
  t = Temperature(100, "C")
  assert pytest.approx(t.to_fahrenheit(), 0.01) == 212

def test_as_celsius():
  t = Temperature(32, "F")
  c = t.as_celsius()
  assert isinstance(c, Temperature)
  assert c.unit == "C"
  assert pytest.approx(c.value, 0.01) == 0

def test_as_fahrenheit():
  t = Temperature(0, "C")
  f = t.as_fahrenheit()
  assert isinstance(f, Temperature)
  assert f.unit == "F"
  assert pytest.approx(f.value, 0.01) == 32

def test_repr():
  t = Temperature(12.345, "C")
  assert repr(t) == "Temperature(12.35, 'C')"

def test_str_celsius():
  t = Temperature(25, "C")
  assert str(t) == "25.00°C"

def test_str_fahrenheit():
  t = Temperature(77, "F")
  assert str(t) == "77.00°F"