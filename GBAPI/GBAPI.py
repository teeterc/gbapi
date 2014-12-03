import re
import datetime

from requests_oauthlib import OAuth2Session
from xml.etree import ElementTree
from xml.dom import minidom

class RequestFailedException(Exception):
    pass

def string_to_dict(string):
    ret = {}
    for kv in string.split(";"):
        kv = kv.split("=")
        ret[kv[0]] = kv[1]
    return ret

def convert_to_python_name(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

NAMESPACES = {
    'ns3': 'http://www.w3.org/2005/Atom',
    'espi': 'http://naesb.org/espi',
    '': 'http://www.w3.org/2005/Atom'
}
for key, value in NAMESPACES.items():
    ElementTree._namespace_map[value] = key

class GBAPIObject(object):
    __header_tags = ['id', 'title', 'updated']
    __entity_types = [['ApplicationInformation', 'GBAPIApplicationInformation'],
                      ['UsagePoint', 'GBAPIUsagePoint'],
                      ['MeterReading', 'GBAPIMeterReading'],
                      ['ReadingType', 'GBAPIReadingType'],
                      ['IntervalBlock', 'GBAPIIntervalBlock'],
                      ['LocalTimeParameters', 'GBAPILocalTimeParameters'],
                      ['ElectricPowerUsageSummary', 'GBAPIElectricPowerUsageSummary'],
                      ['ElectricPowerQualitySummary', 'GBAPIElectricPowerQualitySummary']]
                      
    def __init__(self, gbapi, et, ignore_entries=False):
        self.gbapi = gbapi
        self.element_type = et.tag.split("}")[-1]
        self.et = et
        self.__links = {}
        self.elements = []
        self.__parse_header()
        if not ignore_entries:
            self.__parse_entry()

    def self(self):
        return self.follow("self")

    def links(self): 
        return self.__links

    def get_links(self):
        return self.__links.keys()

    def follow(self, link_key):
        if not self.__links.has_key(link_key):
            raise Exception("Can't follow %s" % link_key)
        return self.gbapi._generic_request(self.__links[link_key], absolute = True)
    
    def __parse_header(self):
        for tag in self.__header_tags:
            node = self.et.find("ns3:%s" % (tag,), NAMESPACES)
            if node is not None:
                setattr(self, convert_to_python_name(tag), node.text)

        for node in self.et.findall('ns3:link', NAMESPACES):
            link_key = node.attrib['rel']
            if link_key == "related":
                link_segments = node.attrib['href'].split("/")
                for i in range(1, len(link_segments)):
                    link_key = node.attrib['href'].split("/")[0 - i]
                    try: 
                        float(link_key)
                        continue
                    except:
                        break

                link_key = convert_to_python_name(link_key)
            self.__links[link_key] = node.attrib['href']

    def __parse_entry(self):
        entries = self.et.findall('ns3:entry', NAMESPACES)
        if len(entries) == 0 and self.et.tag.endswith('entry'):
            entries.append(self.et)

        for entry in entries:
            ### inspect the content subtype and generate the correct instance
            content = entry.find('ns3:content', NAMESPACES)
            for entity_type in self.__entity_types:
                for ai_element in content.findall("espi:%s" % entity_type[0], NAMESPACES):
                    element = globals()[entity_type[1]](self.gbapi, entry, ai_element)
                    element.element_type = entity_type[0]
                    self.elements.append(element)

    def __str__(self):
        kv = [' --element_type: %s' % self.element_type]
        for tag in self.__header_tags:
            kv.append(' --%s: %s' % (tag, getattr(self, convert_to_python_name(tag))))
        kv.append(' --links:')
        for key, value in self.__links.items():
            kv.append('\t--%s: %s' % (key, value))
        for element in self.elements: 
            kv.append("---------")
            kv.append('\t%s' % str(element).replace("\n", "\n\t"))
        return "\n".join(kv)
        
    def prettify(self, elem):
        """Return a pretty-printed XML string for the Element.
        """
        rough_string = ElementTree.tostring(elem, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="\t")

class GBAPIObjectEntity(GBAPIObject):
    entity_nodes = []
    entity_tags = []
    entity_tags_list = []

    def __init__(self, gbapi, entry, element=None):
        if element == None:
            element = entry

        super(GBAPIObjectEntity, self).__init__(gbapi, entry, ignore_entries = True)
        self.__init_subtype(element)

    def __str__(self):
        metadata = super(GBAPIObjectEntity, self).__str__()
        kv = [metadata]
        for tag in self.entity_tags:
            kv.append(' --%s: %s' % (convert_to_python_name(tag[0]), getattr(self, convert_to_python_name(tag[0]))))
        for tag in self.entity_tags_list:
            kv.append(' --%s: %s' % (convert_to_python_name(tag[0]), getattr(self, convert_to_python_name(tag[0]))))
        for tag in self.entity_nodes:
            if len(tag) == 3:            
                kv.append(' --%s: %s' % (convert_to_python_name(tag[0]), "\n".join([str(x) for x in getattr(self, convert_to_python_name(tag[0]))] )))
            else:
                kv.append(' --%s: %s' % (convert_to_python_name(tag[0]), getattr(self, convert_to_python_name(tag[0]), None)))
        return '\n'.join(kv)

    def __init_subtype(self, element):
        for tag in self.entity_tags:
            node = element.find("espi:%s" % (tag[0]), NAMESPACES)
            setattr(self, convert_to_python_name(tag[0]), node if node is None else tag[1](node))

        for tag in self.entity_tags_list:
            nodes = element.findall("espi:%s" % (tag[0]), NAMESPACES)
            local_attribute = convert_to_python_name(tag[0])
            setattr(self, local_attribute, [])
            for node in nodes:
                getattr(self, local_attribute).append(tag[1](node))

        for tag in self.entity_nodes:
            nodes = element.findall("espi:%s" % (tag[0]), NAMESPACES)
            for node in nodes:
                if len(tag) == 3:
                    d = getattr(self, convert_to_python_name(tag[0]), [])
                    d.append(getattr(self, tag[1])(node))
                    setattr(self, convert_to_python_name(tag[0]), d) 
                else:
                    setattr(self, convert_to_python_name(tag[0]), 
                        getattr(self, tag[1])(node))

    class BaseSubNode(object):
        entity_tags = []
        def __init__(self, et):
            for tag in self.entity_tags:
                setattr(self, convert_to_python_name(tag[0]), None)
                if et is not None:
                    node = et.find('espi:%s' % tag[0], NAMESPACES)
                    if node is not None:
                        setattr(self, convert_to_python_name(tag[0]), tag[1](node))
        def __str__(self):
            ret = ['']
            for tag in self.entity_tags:
                if len(tag) == 3:
                    ret.append('\t\t%s:\t%s' % (convert_to_python_name(tag[0]), [ str(x) for x in getattr(self, convert_to_python_name(tag[0]))] ))
                else:
                    ret.append('\t\t%s:\t%s' % (convert_to_python_name(tag[0]), getattr(self, convert_to_python_name(tag[0]))))
            return "\n".join(ret)

    class IntervalSubNode(object):
        def __init__(self, et):
            """ 
            Used as a helper to generate a timedelta object for nodes with "start" and "duration"
            """
            self.start = et.find('espi:start', NAMESPACES)
            self.duration = et.find('espi:duration', NAMESPACES)
            if self.start is not None and self.duration is not None:
                self.start = datetime.datetime.fromtimestamp(float(self.start.text))
                self.duration = datetime.timedelta(seconds = int(self.duration.text))
        def __str__(self):
            return " %s for %ss" % (self.start, self.duration)


class GBAPIApplicationInformation(GBAPIObjectEntity):
    entity_tags = [['dataCustodianApplicationStatus', lambda x: x.text], 
                     ['thirdPartyNotifyUri', lambda x: x.text],
                     ['dataCustodianBulkRequestURI', lambda x: x.text],
                     ['dataCustodianResourceEndpoint', lambda x: x.text],
                     ['client_secret', lambda x: x.text],
                     ['contacts', lambda x: x.text],
                     ['token_endpoint_auth_method', lambda x: x.text],
                     ['grant_types', lambda x: x.text.split(",")],
                     ['dataCustodianId', lambda x: x.text],
                     ['thirdPartyApplicationName', lambda x: x.text]]

    entity_tags_list = [['scope', lambda x: string_to_dict(x.text)]]


class GBAPILocalTimeParameters(GBAPIObjectEntity):
    entity_tags = [['dstEndRule', lambda x: x.text],
                   ['dstOffset', lambda x: x.text],
                   ['dstStartRule', lambda x: x.text],
                   ['tzOffset', lambda x: x.text]]

class GBAPIMeterReading(GBAPIObjectEntity):
    pass

class GBAPIUsagePoint(GBAPIObjectEntity):
    entity_nodes = [['ServiceCategory', 'ServiceCategory'],
                    ['ServiceDeliveryPoint', 'ServiceDeliveryPoint']]

    class ServiceCategory(GBAPIObjectEntity.BaseSubNode):
        entity_tags = [['kind', lambda x: x.text]]

    class ServiceDeliveryPoint(GBAPIObjectEntity.BaseSubNode):
        entity_tags = [['name', lambda x: x.text],
                       ['trafficProfile', lambda x: x.text]]

class GBAPIIntervalBlock(GBAPIObjectEntity):
    entity_nodes = [['IntervalReading', 'IntervalReading', 'array'],
                    ['interval', 'Interval']]

    class Interval(GBAPIObjectEntity.IntervalSubNode):
        pass

    class IntervalReading(GBAPIObjectEntity.BaseSubNode):
        entity_tags = [['cost', lambda x: x.text],
                       ['value', lambda x: x.text],
                       ['timePeriod', GBAPIObjectEntity.IntervalSubNode]]
    

class GBAPIReadingType(GBAPIObjectEntity):
    entity_tags = [['accumulationBehaviour', lambda x: x.text],
                   ['commodity', lambda x: x.text],
                   ['currency', lambda x: x.text],
                   ['dataQualifier', lambda x: x.text],
                   ['flowDirection', lambda x: x.text],
                   ['intervalLength', lambda x: x.text],
                   ['kind', lambda x: x.text],
                   ['phase', lambda x: x.text],
                   ['powerOfTenMultiplier', lambda x: x.text],
                   ['timeAttribute', lambda x: x.text],
                   ['uom', lambda x: x.text]]

class GBAPIElectricPowerQualitySummary(GBAPIObjectEntity):
    pass

class GBAPIElectricPowerUsageSummary(GBAPIObjectEntity):
    entity_tags = [['billLastPeriod', lambda x: x.text],
                   ['billToDate', lambda x: x.text],
                   ['costAdditionalLastPeriod', lambda x: x.text],
                   ['currency', lambda x: x.text],
                   ['qualityOfReading', lambda x: x.text],
                   ['statusTimeStamp', lambda x: x.text]]

    entity_nodes = [['billingPeriod', 'BillingPeriod'],
                     ['overallConsumptionLastPeriod', 'OverallConsumptionLastPeriod'],
                     ['currentBillingPeriodOverAllConsumption', 'CurrentBillingPeriodOverAllConsumption']]


    class BillingPeriod(GBAPIObjectEntity.IntervalSubNode):
        pass

    class OverallConsumptionLastPeriod(GBAPIObjectEntity.BaseSubNode):
        entity_tags = [['powerOfTenMultiplier', lambda x: x.text],
                       ['uom', lambda x: x.text],
                       ['value', lambda x: x.text]]

    class CurrentBillingPeriodOverAllConsumption(GBAPIObjectEntity.BaseSubNode):
        entity_tags = [['powerOfTenMultiplier', lambda x: x.text],
                       ['timeStamp', lambda x: x.text],
                       ['uom', lambda x: x.text],
                       ['value', lambda x: x.text]]

        


class GBAPI(object):
    __GB_Request = None
    def __init__(self, access_token, baseurl):
        self.__BASEURL = baseurl
        self.__TOKEN = access_token
        self.__GB_Request = OAuth2Session(r'clientid', token = self.__TOKEN)

    def get_ApplicationInformation(self, application_information_id = None):
        path = "/espi/1_1/resource/ApplicationInformation"

        if application_information_id is not None:
            path = "/".join([path, str(application_information_id)])
        
        g = self._generic_request(path)
        return g

    def post_ApplicationInformation(self):
        pass

    def put_ApplicationInformation(self):
        pass

    def delete_ApplicationInformation(self):
        pass

    def get_UsagePoint(self, usage_point_id=None, subscription_id=None):
        path = "/espi/1_1/resource/UsagePoint"

        if usage_point_id is not None and subscription_id is not None:
            path = "/espi/1_1/resource/Subscription/%s/UsagePoint/%s" % (subscription_id, usage_point_id)
        elif usage_point_id is None and subscription_id is not None:
            path = "/espi/1_1/resource/Subscription/%s/UsagePoint" % (subscription_id,)
        elif usage_point_id is None and subscription_id is None:
            path = "/espi/1_1/resource/UsagePoint"
        elif usage_point_id is not None and subscription_id is None:
            path = "/espi/1_1/resource/UsagePoint/%s" % usage_point_id
        else:
            raise Exception

        g = self._generic_request(path)
        return g

    def get_ReadingType(self, reading_type_id=None):
        path = "/espi/1_1/resource/ReadingType"

        if reading_type_id is not None:
            path = "/".join([path, str(reading_type_id)])

        g = self._generic_request(path)
        return g

    def get_MeterReading(self, meter_reading_id=None,usage_point_id=None, subscription_id=None):
        path = "/espi/1_1/resource/MeterReading"
        path_2 = "/espi/1_1/resource/Subscription/%s" % subscription_id

        if subscription_id is not None and usage_point_id is not None and meter_reading_id is None:
            path = "/".join([path_2, 'UsagePoint', str(usage_point_id), 'MeterReading'])

        elif subscription_id is not None and usage_point_id is not None and meter_reading_id is not None:
            path = "/".join([path_2, 'UsagePoint', str(usage_point_id), 'MeterReading', str(meter_reading_id)])

        elif usage_point_id is None and meter_reading_id is not None:
            path = "/".join([path, str(meter_reading_id)])

        g = self._generic_request(path)
        return g

    def get_LocalTimeParameters(self, local_time_parameter_id=None):
        path = "/espi/1_1/resource/LocalTimeParameters"

        if local_time_parameter_id is not None:
            path = "/".join([path, str(local_time_parameter_id)])

        g = self._generic_request(path)
        return g

    def get_IntervalBlock(self, subscription_id=None, usage_point_id=None, meter_reading_id = None, interval_block_id = None):
        path = "/espi/1_1/resource"
        if subscription_id is not None and usage_point_id is not None and meter_reading_id is not None and interval_block_id is not None:
            path += "/Subscription/%s/UsagePoint/%s/MeterReading/%s/IntervalBlock/%s" % (subscription_id, 
                                                                                         usage_point_id, 
                                                                                         meter_reading_id, 
                                                                                         interval_block_id)
        
        elif subscription_id is not None and usage_point_id is not None and meter_reading_id is not None and interval_block_id is None:
            path += "/Subscription/%s/UsagePoint/%s/MeterReading/%s/IntervalBlock" % (subscription_id, 
                                                                                      usage_point_id, 
                                                                                      meter_reading_id)
        elif subscription_id is None and usage_point_id is None and meter_reading_id is None and interval_block_id is not None:
            path += "/IntervalBlock/%s" % interval_block_id

        elif subscription_id is None and usage_point_id is None and meter_reading_id is None and interval_block_id is None:
            path += "/IntervalBlock"
            
        else:
            raise Exception()

        g = self._generic_request(path)
        return g

    def get_ElectricPowerUsageSummary(self, subscription_id, usage_point, electric_power_usage_summary_id=None):
        path = "/espi/1_1/resource/Subscription/%s/UsagePoint/%s/ElectricPowerUsageSummary" % (subscription_id, usage_point)

        if electric_power_usage_summary_id is not None:
            path = "/".join([path, str(electric_power_usage_summary_id)])

        g = self._generic_request(path)
        return g

        
    def get_ElectricPowerQualitySummary(self, subscription_id, usage_point, electric_power_quality_summary_id=None):
        path = "/espi/1_1/resource/Subscription/%s/UsagePoint/%s/ElectricPowerQualitySummary" % (subscription_id, usage_point)

        if electric_power_quality_summary_id is not None:
            path = "/".join([path, str(electric_power_quality_summary_id)])
        g = self._generic_request(path)
        return g

    def get_Batch(self, bulk_id = None, subscription_id = None, retail_customer_id = None, usage_point_id = None):
        if bulk_id is not None:
            path = "/espi/1_1/resource/Batch/Bulk/%s" % builk_id
        elif subscription_id is not None:
            path = "/espi/1_1/resource/Batch/Subscription/%s" % subscription_id
        elif retail_customer_id is not None and usage_point_id is not None:
            path = "/espi/1_1/resource/Batch/RetailCustomer/%s/UsagePoint/%s" % (retail_customer_id, usage_point_id)
        elif retail_customer_id is not None:
            path = "/espi/1_1/resource/Batch/RetailCustomer/%s/UsagePoint" % retail_customer_id

        else:
            raise Exception

        g = self._generic_request(path)
        return g

    def _generic_request(self, path, absolute = False):
        if absolute: 
            response = self.__GB_Request.get(path)
        else:
            response = self.__GB_Request.get("%s%s" % (self.__BASEURL, path))

        if response.status_code != 200:
            raise RequestFailedException()

        et = ElementTree.fromstring(response.text)
        g = GBAPIObject(self, et)
        if g.element_type != "feed":
            return g.elements[0]
        return g


