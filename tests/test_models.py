import pytest

from voluptuous import Schema, Coerce, Invalid
import tdd.models
from tdd.exceptions import TDDConfigError

def _prepare_incsv(tmpdir, csv_contents):

    csv_infile = tmpdir.join('input.csv')
    csv_infile.write(csv_contents)
    return csv_infile


def test_parsing_csv_raises_on_missing_column(tmpdir):
    csv_infile = _prepare_incsv(
        tmpdir,
        """id,missing,value
1,"Robin",42
1,Ahoj,666""")
    with pytest.raises(TDDConfigError):
        list(tdd.models.csv_to_json(csv_infile.strpath, id_column='id'))

def test_parsing_and_validating_csv_no_id_column(tmpdir):
    csv_infile = tmpdir.join('input.csv')
    csv_infile.write("""id,path,value
1,"Robin",42
1,Ahoj,666""")

    expected = [{"Robin": 42, "id": "1", "Ahoj": "666" }]
    schema = Schema({"id": str,
                     "Robin": Coerce(int),
                     "Ahoj": str})

    validated_and_coerced = tdd.models.validate_input_csv(csv_infile,
                                                          schema,
                                                          id_column='id',
                                                          include_id_column=True)
    assert list(validated_and_coerced) == expected


def test_validating_csv_completely_fails_on_invalid_input():

    obj = {"foo": "hoj", "count": "THIS SHULD FAIL"}
    sch = Schema({"foo": str, "count": Coerce(int)})

    with pytest.raises(Invalid):
        tdd.models.validate_json(obj, sch)


def test_serialize_csv_to_json(tmpdir):
    expected = [{
        "campaign_id": "campA",
        "campaignName": "ucelovka proti babisovi",
        "budget": {
            "Cost": "666",
            "Currency": "USD"
        }
    }
    ]

    contents = '''campaign_id,path,value
campA,campaignName,"ucelovka proti babisovi"
campA,budget__Cost,666
campA,budget__Currency,USD'''

    csv_infile = _prepare_incsv(tmpdir, contents)
    serialized = list(tdd.models.csv_to_json(
        csv_infile.strpath,
        id_column='campaign_id',
        include_id_column=True))
    assert expected[0] == serialized[0]
