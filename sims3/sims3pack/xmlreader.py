import re
import xml.etree.ElementTree as ET

class Sims3PackError(Exception):
    pass

class Sims3Pack:
    MAGIC_LENGTH = 11
    MAGIC = bytes('\x07\x00\x00\x00TS3Pack', 'utf-8')
    XML_END = '</Sims3Package>' # sim3pack files are just DBPF/DBPP with XML header
    UNKNOWN_FIELD_1_LENGTH = 6

    filename = None
    handle = None
    xml_root = None

    def __init__(self, handle):
        self.filename = handle.name
        self.handle = handle
        ts3pack_magic = self.handle.read(self.MAGIC_LENGTH)

        if ts3pack_magic != self.MAGIC:
            raise Sims3PackError('File is missing magic ("TS3Pack" near beginning of file)')

        self.handle.seek(self.UNKNOWN_FIELD_1_LENGTH, 1)

        xml_str = ''
        found_end = False

        while found_end is False:
            try:
                last_pos = self.handle.tell()
                line = self.handle.readline().decode('utf-8')
            except UnicodeDecodeError as e:
                # Most likely hit end but there's no true terminator here; instead DBPF or DBPP come right after the last XML tag
                self.handle.seek(last_pos)

                temp_str = ''

                while self.XML_END not in temp_str:
                    try:
                        value = self.handle.read(1).decode('utf-8').strip()
                        if value:
                            temp_str += value
                    except UnicodeDecodeError:
                        break

                line = temp_str

            xml_str += line

            if self.XML_END in xml_str:
                found_end = True

        xml_str = xml_str.strip()
        xml_str = re.sub('\/Sims3Package>.*', '/Sims3Package>', xml_str)

        try:
            self.xml_root = ET.fromstring(xml_str)
        except ET.ParseError as e:
            print(xml_str)
            raise Sims3PackError(str(e))

    def __str__(self):
        return '''Filename: %s
Type: %s
SubType: 0x%x
Name: %s
Descrption: %s''' % (
                self.filename,
                self.get_type(),
                self.get_subtype(),
                self.get_name(),
                self.get_description(),
            )

    def dump_xml(self):
        ET.dump(self.xml_root)

    def get_type(self):
        return self.xml_root.attrib['Type']

    def get_subtype(self):
        return int(self.xml_root.attrib['SubType'], 16)

    def get_name(self, locale='en-US'):
        found_text = None
        found_en_us = None

        for child in self.xml_root.findall('LocalizedNames')[0]:
            if child.attrib['Language'] == 'en-US':
                found_en_us = child.text
            if child.attrib['Language'] == locale:
                found_text = child.text

        if found_text:
            return found_text

        return found_en_us

    def get_description(self, locale='en-US'):
        found_text = None
        found_en_us = None

        for child in self.xml_root.findall('LocalizedDescriptions')[0]:
            if child.attrib['Language'] == 'en-US':
                found_en_us = child.text
            if child.attrib['Language'] == locale:
                found_text = child.text

        if found_text:
            return found_text

        return found_en_us
