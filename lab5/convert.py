import json
import xml.etree.ElementTree as ET
import yaml   # 如果無就 pip install pyyaml

# 1. 建立一個 Sample Customer Record
customer = {
    "customer_id": "C001",
    "first_name": "Annie",
    "last_name": "Chang",
    "email": "anniez@example.com",
    "phone": "+1 647 555 0134",
    "address": {
        "street": "12 Market Street",
        "city": "San Francisco",
        "state": "CA",
        "postal": "94105",
        "country": "US"
    }
}

# -------------------------
# 2. Save as JSON
with open("customer.json", "w") as f:
    json.dump(customer, f, indent=2)

# -------------------------
# 3. Save as XML
def dict_to_xml(tag, d):
    elem = ET.Element(tag)
    for k, v in d.items():
        if isinstance(v, dict):
            elem.append(dict_to_xml(k, v))
        else:
            child = ET.SubElement(elem, k)
            child.text = str(v)
    return elem

xml_root = dict_to_xml("customer", customer)
ET.ElementTree(xml_root).write("customer.xml", encoding="utf-8", xml_declaration=True)

# -------------------------
# 4. Save as YAML
with open("customer.yaml", "w") as f:
    yaml.dump(customer, f, sort_keys=False)
