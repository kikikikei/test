import json
import xml.etree.ElementTree as ET
import yaml   

tree = ET.parse("customer.xml")
root = tree.getroot()


def xml_to_dict(elem):
    children = list(elem)
    if not children:   
        return elem.text
    d = {}
    for child in children:
        d[child.tag] = xml_to_dict(child)
    return d

xml_dict = xml_to_dict(root)

# store JSON
with open("from_xml.json", "w") as f:
    json.dump(xml_dict, f, indent=2)

print(" XML to JSON → from_xml.json")


# ---------------------------
# 2. Read JSON → Convert to YAML
# ---------------------------

# read JSON 檔
with open("customer.json") as f:
    json_obj = json.load(f)

# store YAML
with open("from_json.yaml", "w") as f:
    yaml.dump(json_obj, f, sort_keys=False)

print("JSON to YAML → from_json.yaml")
