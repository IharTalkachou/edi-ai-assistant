# парсинг XML (упрощённый формат UBL)
from lxml import etree
from logger_config import logger

class EdiXmlParser:
    """
    Класс для разбора XML-накладных
    """
    def parse_invoice(self, xml_content: str):
        try:
            # lxml работает с байтами, поэтому конвертирую строку в байты
            root = etree.fromstring(xml_content.encode('utf-8'))
            
            # применяю XPath для поиска данных
            # тэги для поиска через XPath: InvoiceID, TotalAmount
            # @currencyID - атрибут тэга TotalAmount
            invoice_id = root.xpath('//InvoiceID/text()')
            total_amount = root.xpath('//TotalAmount/text()')
            currency = root.xpath('//TotalAmount/@currencyID')
            
            # XPath должен вернуть списки, забираю первый элемент списка или None
            data = {
                'invoice_id': invoice_id[0] if invoice_id else None,
                'amount': total_amount[0] if total_amount else 0.0,
                'currency': currency[0] if currency else 'UNK'
            }
            
            # создание структруного лога
            # extra - словарь для наполнения JSON
            logger.info(
                'XML parsed successfully', extra={
                    'event': 'xml_parse_success',
                    'invoice_id': data['invoice_id'],
                    'amount': data['amount']
                }
            )
            return data
        except etree.XMLSyntaxError as e:
            logger.error(
                'XML Syntax Error', 
                extra={
                    'event': 'xml_parse_error',
                    'error_details': str(e)
                }
            )
            raise ValueError(f'Invalid XML format: {e}')
        except Exception as e:
            logger.error(
                'Unknown parser error', 
                extra={
                    'event': 'parser_crush',
                    'error': str(e)
                }
            )
            raise e

# блок тестирования
if __name__ == '__main__':
    sample_xml = """
    <Invoice>
        <InvoiceID>INV-0612001</InvoiceID>
        <Sender>OOO Romashka</Sender>
        <TotalAmount currencyID="EUR">1500.50</TotalAmount>
    </Invoice>
    """
    parser = EdiXmlParser()
    result = parser.parse_invoice(sample_xml)
    print('Результат:', result)