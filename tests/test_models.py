import pytest

from voluptuous import Schema, Coerce, Invalid
import ttdwr.models
from ttdwr.exceptions import TTDConfigError

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
    with pytest.raises(TTDConfigError):
        list(ttdwr.models.csv_to_json(csv_infile.strpath, id_column=['id']))

def test_parsing_and_validating_csv_no_id_column(tmpdir):
    csv_infile = tmpdir.join('input.csv')
    csv_infile.write("""id,path,value
1,"Robin",42
1,Ahoj,666""")

    expected = [{"Robin": 42, "id": "1", "Ahoj": "666" }]
    schema = Schema({"id": str,
                     "Robin": Coerce(int),
                     "Ahoj": str})

    validated_and_coerced = ttdwr.models.validate_input_csv(csv_infile,
                                                          schema,
                                                          id_column=['id'],
                                                          include_id_column=True)
    assert list(validated_and_coerced) == expected


def test_validating_csv_completely_fails_on_invalid_input():

    obj = {"foo": "hoj", "count": "THIS SHULD FAIL"}
    sch = Schema({"foo": str, "count": Coerce(int)})

    with pytest.raises(Invalid):
        ttdwr.models.validate_json(obj, sch)


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
    serialized = list(ttdwr.models.csv_to_json(
        csv_infile.strpath,
        id_column=['campaign_id'],
        include_id_column=True))
    assert expected[0] == serialized[0]

def test_converting_csv_row_format_to_column_format():

    # as returned by csv.DictReader
    raw_csv_values = [
        {"path": "campaign__name",
         "value": "Ucelovka",
         "campaign_id": 1,
         "subcampaign_id": 1},
        {"path": "campaign__description",
         "value": "kampan proti babisovi",
         "campaign_id": 1,
         "subcampaign_id": 1},
    ]

    expected = [
        {
            "campaign__name": "Ucelovka",
            "campaign_id": 1,
            "subcampaign_id": 1

        },
        {
            "campaign__description": "kampan proti babisovi",
            "campaign_id": 1,
            "subcampaign_id": 1
        }
    ]

    converted_with_ids = list(ttdwr.models._column_to_row_format(
        raw_csv_values,
        id_columns=['campaign_id', 'subcampaign_id']))
    assert converted_with_ids[0]  == expected[0]


    expected_without_ids = [
        {
            "campaign__name": "Ucelovka"
        },
        {
            "campaign__description": "kampan proti babisovi",
        }
    ]


    converted_without_ids = list(ttdwr.models._column_to_row_format(
        raw_csv_values,
        id_columns=None))
    assert converted_without_ids[0] == expected_without_ids[0]
