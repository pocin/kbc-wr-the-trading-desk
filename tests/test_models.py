import pytest

from voluptuous import Schema, Coerce
import tdd.models

def test_serialize_csv_to_json_and_validate_schema(tmpdir):
    schema = Schema({
        "foo": str,
        "count": Coerce(int)
        }
    )

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

    potentially_invalid_json = tdd.models.csv_to_json(csv_infile.strpath)

    for i, obj in enumerate(potentially_invalid_json):
        validated_and_coerced = tdd.models.validate_json(obj, schema)
        assert validated_and_coerced == expected[i]
