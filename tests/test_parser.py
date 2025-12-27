import pytest
from xml_parser import EdiXmlParser

# данные, которые готовятся перед тестом
@pytest.fixture
def parser():
    return EdiXmlParser()

def test_parse_valid_invoice(parser):
    xml = """
    <Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
             xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
        <cbc:ID>INV-1</cbc:ID>
    </Invoice>
    """
    # жду, что парсер вернет dict с ID
    result = parser.parse_invoice(xml)
    assert result['invoice_id'] == "INV-1"

def test_parse_invalid_xml(parser):
    xml = "<Invoice>Broken Tag"
    # жду, что парсер выбросит ошибку ValueError
    with pytest.raises(ValueError):
        parser.parse_invoice(xml)