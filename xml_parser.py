# парсинг XML (упрощённый формат UBL)
from lxml import etree
from logger_config import logger

class EdiXmlParser:
    """
    Класс для разбора XML-накладных
    """
    # пространства для имен UBL 2.1
    NS = {
        'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
        'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
        'ubl': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2'
    }
    
    def parse_invoice(self, xml_content: str):
        try:
            # парсинг XML 
            # удаление ByteOrderMark (BOM) если есть - чтобы lxml мог работать с файлом
            if isinstance(xml_content, str):
                xml_bytes = xml_content.encode('utf-8')
            else:
                xml_bytes = xml_content

            root = etree.fromstring(xml_bytes)
            
            # вспомогательная функция для поиска с NameSpaces
            def get_text(xpath_query, element=root):
                # lxml требует явного указания NameSpaces
                res = element.xpath(xpath_query, namespaces=self.NS)
                return res[0].text if res else None
            
            # шапка документа
            data = {
                "invoice_id": get_text('//cbc:ID'),
                "issue_date": get_text('//cbc:IssueDate'),
                "currency": get_text('//cbc:DocumentCurrencyCode'),
                "supplier_name": get_text('//cac:AccountingSupplierParty/cac:Party/cac:PartyName/cbc:Name'),
                "customer_name": get_text('//cac:AccountingCustomerParty/cac:Party/cac:PartyName/cbc:Name'),
                # Суммы
                "total_payable": float(get_text('//cac:LegalMonetaryTotal/cbc:PayableAmount') or 0),
                "total_tax_excl": float(get_text('//cac:LegalMonetaryTotal/cbc:TaxExclusiveAmount') or 0),
                "lines": []
            }
            
            # строки товаров
            lines = root.xpath('//cac:InvoiceLine', namespaces=self.NS)
            for line in lines:
                item = {
                    "line_id": get_text('cbc:ID', line),
                    "quantity": float(get_text('cbc:InvoicedQuantity', line) or 0),
                    "line_amount": float(get_text('cbc:LineExtensionAmount', line) or 0),
                    "item_name": get_text('cac:Item/cbc:Name', line)
                }
                data["lines"].append(item)
            
            # математическая валидация
            # сумма всех строк должна быть равна Total Tax Exclusive Amount
            calculated_total = sum(l['line_amount'] for l in data['lines'])
            if abs(calculated_total - data['total_tax_excl']) > 0.01:
                logger.warning("Math mismatch in invoice", extra={
                    "calculated": calculated_total,
                    "declared": data['total_tax_excl']
                })
                data["validation_error"] = f"Сумма строк ({calculated_total}) не совпадает с итогом ({data['total_tax_excl']})"
            else:
                data["validation_error"] = None

            logger.info("UBL Invoice parsed", extra={"id": data["invoice_id"], "lines_count": len(lines)})
            return data
        
        except etree.XMLSyntaxError as e:
            logger.error("XML Syntax Error", extra={"error": str(e)})
            raise ValueError(f"Invalid XML: {e}")
        except Exception as e:
            logger.error("Parser crash", extra={"error": str(e)})
            raise e