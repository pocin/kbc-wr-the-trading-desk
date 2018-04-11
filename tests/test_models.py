import pytest

from voluptuous import Schema, Coerce, Invalid
import tdd.models

def test_validating_csv_completely(tmpdir):
    csv_infile = tmpdir.join('input.csv')
    csv_infile.write("""foo,count
"Robin",42
Ahoj,666""")

    expected = [{
        "foo": "Robin",
        "count": 42
    },{
        "foo": "Ahoj",
        "count": 666
    }]
    schema = Schema({
        "foo": str,
        "count": Coerce(int)
        })

    validated_and_coerced = tdd.models.validate_input_csv(csv_infile, schema)
    assert list(validated_and_coerced) == expected


def test_validating_csv_completely_fails_on_invalid_input(tmpdir):
    csv_infile = tmpdir.join('input.csv')
    csv_infile.write("""foo,count
"Robin",42
Ahoj,xxxx""")

    sch = Schema({
        "foo": str,
        "count": Coerce(int)
        })

    with pytest.raises(Invalid):
        list(tdd.models.validate_input_csv(csv_infile, sch))

def test_serialize_csv_to_json(tmpdir):

    expected = [{
        "foo": "Robin",
        "count": "42"
    },{
        "foo": "Ahoj",
        "count": "666"
    }]

    csv_infile = tmpdir.join('input.csv')
    csv_infile.write("""foo,count
"Robin",42
Ahoj,666""")

    schema = Schema({
        "foo": str,
        "count": Coerce(int)
        })

    serialized = tdd.models.csv_to_json(csv_infile.strpath)
    assert list(serialized) == expected


def test_nesting_json_no_nesting_needed():
    inp = {
        'col1': 42,
        'col2': "foo"
    }
    # expected
    exp = {
        'col1': 42,
        'col2': "foo"
    }
    assert exp == tdd.models._nest_json(inp)


def test_nesting_json_single_level():
    inp = {
        'col1__nested': 42,
        'col2': "foo"
    }
    # expected
    exp = {
        'col1': {'nested': 42},
        'col2': "foo"
    }
    assert exp == tdd.models._nest_json(inp)
