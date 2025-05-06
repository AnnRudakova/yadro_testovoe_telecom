import xml.etree.ElementTree as ET
import json
import os

"""
Класс парсер
"""
class FileParser:

    def __init__(self):
        self.classes = {}
        self.hierarchy = {}
        self.multiplicity = {}

    def parsing(self, xml_file):

        tree = ET.parse(xml_file)
        root = tree.getroot()

        for elem in root:

            if elem.tag == "Class":
                class_name = elem.attrib["name"]
                self.classes[class_name] = {
                    "is_root": elem.attrib["isRoot"],
                    "documentation": elem.attrib["documentation"],
                    "attributes": [
                        {"name": attr.attrib["name"], "type": attr.attrib["type"]}
                        for attr in elem.findall("Attribute")
                    ]
                }

            elif elem.tag == "Aggregation":
                parent = elem.attrib["target"]
                child = elem.attrib["source"]

                if parent not in self.hierarchy:
                    self.hierarchy[parent] = []
                self.hierarchy[parent].append(child)

                mult = elem.attrib["sourceMultiplicity"]

                if ".." in mult:
                    min_val, max_val = mult.split("..")
                else:
                    min_val = max_val = mult

                self.multiplicity[(parent, child)] = {
                    "min": min_val,
                    "max": max_val
                }

"""
Класс для генерации xml файла
"""
class GenerXml:
    def __init__(self, parser):
        self.parser = parser

    def gener_file(self):

        def gener_element(class_name):
            elem = ET.Element(class_name)

            for attr in self.parser.classes[class_name]["attributes"]:
                attr_elem = ET.SubElement(elem, attr["name"])
                attr_elem.text = attr["type"]

            for child in self.parser.hierarchy.get(class_name, []):
                elem.append(gener_element(child))

            return elem

        root_class = next(iter(self.parser.hierarchy))
        xml_file = gener_element(root_class)
        ET.indent(xml_file, space="    ")

        return '<?xml version="1.0" ?>\n' + ET.tostring(xml_file, encoding="unicode")

"""
Класс для генерации json файла
"""
class GenerJson:
    def __init__(self, parser):
        self.parser = parser

    def gener_file(self):

        json_file = []
        child_mult = {}

        for relation, mult in self.parser.multiplicity:
            child = relation[1]
            child_mult[child] = mult

        for class_name in self.parser.classes:
            class_data = self.parser.classes[class_name]
            info = {
                "class": class_name,
                "documentation": class_data["documentation"],
                "isRoot": class_data["is_root"],
                "parameters": class_data["attributes"]
            }

            if class_name in self.parser.hierarchy:
                info["parameters"].extend(
                    {"name": child, "type": "class"}
                    for child in self.parser.hierarchy[class_name]
                )

            if class_name in child_mult:
                info.update(child_mult[class_name])

            json_file.append(info)

        return json.dumps(json_file, indent=4)

def main():

    parser = FileParser()
    parser.parsing("input/test_input.xml")

    gener_xml = GenerXml(parser)
    gener_json = GenerJson(parser)

    os.makedirs("out", exist_ok=True)

    with open("out/config.xml", "w") as f:
        f.write(gener_xml.gener_file())

    with open("out/meta.json", "w") as f:
        f.write(gener_json.gener_file())

if __name__ == "__main__":
    main()