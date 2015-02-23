#!/usr/bin/env python

import unittest
from GBAPI import GBAPI, RequestFailedException
class BaseGBAPITestCase(unittest.TestCase):
    def setUp(self):
        BASEURL = "https://services.greenbuttondata.org:443/DataCustodian"
        token = {
            'access_token': '688b026c-665f-4994-9139-6b21b13fbeee',
            'refresh_token': 'asdfkljh23490sdf',
            'token_type': 'Bearer',
            'expires_in': '3600',     # initially 3600, need to be updated by you
            }
        self.GBAPI = GBAPI(token, BASEURL)

class TestMeterReading(BaseGBAPITestCase):
    def test_meter_reading(self):
        res = self.GBAPI.get_MeterReading()
        self.assertTrue(len(res.elements) > 0)

    def test_meter_reading_with_meter_id(self):
        res = self.GBAPI.get_MeterReading(meter_reading_id = 1)
        self.assertEqual(res.element_type, "MeterReading")

    def test_meter_reading_with_subscription_and_usagepoint(self):
        res = self.GBAPI.get_MeterReading(subscription_id = 5, usage_point_id = 1)
        self.assertTrue(len(res.elements) > 0)
        self.assertEqual(res.element_type, "feed")        

    def test_meter_reading_with_subscription_and_usagepoint_and_meter_reading(self):
        res = self.GBAPI.get_MeterReading(subscription_id = 5, usage_point_id = 1, meter_reading_id = 1)
        self.assertEqual(res.element_type, "MeterReading")

    def test_meter_reading_with_subscription_and_usagepoint_and_meter_reading_links(self):
        res = self.GBAPI.get_MeterReading(subscription_id = 5, usage_point_id = 1, meter_reading_id = 1)
        self.assertEqual(res.element_type, "MeterReading")
        ib = res.follow('interval_block')
        self.assertTrue(ib.elements > 0)
        self.assertEqual(ib.element_type, "feed")

class TestReadingType(BaseGBAPITestCase):
    def test_get_reading_type(self):
        res = self.GBAPI.get_ReadingType()
        self.assertTrue(res.elements > 0)

    def test_get_reading_type_with_reading_type(self):
        res = self.GBAPI.get_ReadingType(reading_type_id = 1)
        self.assertEqual(res.element_type, "ReadingType")

class TestServiceStatus(BaseGBAPITestCase):
    pass

class TestUsagePoint(BaseGBAPITestCase):
    def test_get_usage_point(self):
        res = self.GBAPI.get_UsagePoint()
        self.assertTrue(len(res.elements) > 0)

    def test_get_usage_point_with_usage_point(self):
        res = self.GBAPI.get_UsagePoint(usage_point_id=1)
        self.assertEqual(res.element_type, "UsagePoint")
    
    def test_get_usage_point_with_usage_point_and_follow(self):
        pass

    def test_get_usage_point_with_subscription(self):
        res = self.GBAPI.get_UsagePoint(subscription_id = 5)
        self.assertTrue(len(res.elements) > 0)

    def test_get_usage_point_with_subscription_and_usage_point(self):
        res = self.GBAPI.get_UsagePoint(subscription_id = 5, usage_point_id = 1)        
        self.assertEqual(res.element_type, "UsagePoint")

class TestElectricPowerQualitySummary(BaseGBAPITestCase):
    def test_get_electric_power_quality_summary_with_no_parameters(self):
        try: 
            res = self.GBAPI.get_ElectricPowerQualitySummary()
            self.assertTrue(False)
        except TypeError:
            self.assertTrue(True)            

    def test_get_electric_power_quality_summary_with_subscription_id_and_usage_point_id(self):
        res = self.GBAPI.get_ElectricPowerQualitySummary(5, 1)
        self.assertEqual(res.element_type, "feed")
        ### not sure how else to test this... no data

    def test_get_electric_power_quality_summary_with_subscription_and_usage_point_and_electric_power_quality_summary_id(self):
        res = self.GBAPI.get_ElectricPowerQualitySummary(5, 1, electric_power_quality_summary_id=1)
        self.assertEqual(res.element_type, "feed")
        ### not sure how else to test this... no data

class TestElectricPowerUsageSummary(BaseGBAPITestCase):
    def test_get_electric_power_usage_summary_with_no_parameters(self):
        try: 
            res = self.GBAPI.get_ElectricPowerUsageSummary()
            self.assertTrue(False)
        except TypeError:
            self.assertTrue(True)            

    def test_get_electric_power_usage_summary_with_subscription_id_and_usage_point_id(self):
        res = self.GBAPI.get_ElectricPowerUsageSummary(5, 1)
        self.assertEqual(res.element_type, "feed")
        self.assertTrue(len(res.elements) > 0)

    def test_get_electric_power_usage_summary_with_subscription_and_usage_point_and_electric_power_quality_summary_id(self):
        res = self.GBAPI.get_ElectricPowerUsageSummary(5, 1, electric_power_usage_summary_id=1)
        self.assertEqual(res.element_type, "ElectricPowerUsageSummary")

class TestBatch(BaseGBAPITestCase):
    def test_get_batch_with_bulk_id(self):
        ### expected to fail... not implemented
        self.assertTrue(False)

    def test_get_batch_with_subscription(self):
        res = self.GBAPI.get_Batch(subscription_id=5)
        self.assertTrue(len(res.elements) > 0)

    def test_get_batch_with_retail_customer(self):
        res = self.GBAPI.get_Batch(retail_customer_id=1)
        self.assertTrue(len(res.elements) > 0)
    def test_get_batch_with_retail_customer_and_usage(self):
        res = self.GBAPI.get_Batch(retail_customer_id=1, usage_point_id = 1)
        self.assertTrue(len(res.elements) > 0)

class TestIntervalBlock(BaseGBAPITestCase):
    def test_get_interval_block_with_no_parameters(self):
        ### no response from server
        pass

    def test_get_interval_block_with_only_interval_block(self):
        res = self.GBAPI.get_IntervalBlock(interval_block_id = 1)
        self.assertEqual(res.element_type, "IntervalBlock")
        self.assertTrue(len(res.interval_reading) > 0)

    def test_get_interval_block_with_subscription_and_no_usage_poin(self):
        try: 
            res = self.GBAPI.get_IntervalBlock(subscription_id = 1)
            self.assertTrue(False)
        except:
            self.assertTrue(True)

    def test_get_interval_block_with_subscription_and_usage_point(self):
        try: 
            res = self.GBAPI.get_IntervalBlock(subscription_id = 1, usage_point_id = 1)
            self.assertTrue(False)
        except:
            self.assertTrue(True)

    def test_get_interval_block_with_subscription_and_usage_poin_and_meter_reading(self):
        res = self.GBAPI.get_IntervalBlock(subscription_id = 1, usage_point_id = 1, meter_reading_id = 1)
        self.assertEqual(res.element_type, "feed")

    def test_get_interval_block_with_subscription_and_usage_poin_and_meter_reading_and_interval_block(self):
        res = self.GBAPI.get_IntervalBlock(subscription_id = 1, usage_point_id = 1, meter_reading_id = 1, interval_block_id = 1)
        self.assertEqual(res.element_type, "IntervalBlock")
        self.assertTrue(len(res.interval_reading) > 0)        

class TestLocalTimeParameters(BaseGBAPITestCase):
    def test_get_local_time_parameters(self):
        res = self.GBAPI.get_LocalTimeParameters()
        self.assertEqual(res.element_type, "feed")
        self.assertTrue(len(res.elements) > 0)

class TestApplicationInformation(BaseGBAPITestCase):
    def test_get_application_information_with_no_application_id(self):
        res = self.GBAPI.get_ApplicationInformation()

    def test_get_application_information_with_application_id(self):
        res = self.GBAPI.get_ApplicationInformation(1)

    def test_get_application_information_with_application_id_and_follow_self(self):
        res = self.GBAPI.get_ApplicationInformation(1)
        self.assertEqual(res.self().id, res.id)

    def test_get_application_information_with_application_id_and_follow_up(self):
        res = self.GBAPI.get_ApplicationInformation(1)
        up = res.follow("up")
        passed = False
        for element in up.elements:
            if res.id  == element.id:
                passed = True
        self.assertTrue(passed)

    def test_get_application_information_with_invalid_application_id(self):
        try: 
            self.GBAPI.get_ApplicationInformation(-1)
        except RequestFailedException:
            assert(True)

    def test_get_application_information_with_invalid_string_application_id(self):
        try: 
            self.GBAPI.get_ApplicationInformation("failed")
        except RequestFailedException:
            assert(True)

    def test_get_application_information_and_print(self):
        res = self.GBAPI.get_ApplicationInformation(1)
        g = str(res)
        self.assertTrue(len(g) > 10)

class TestLocalFileSource(BaseGBAPITestCase):
    def test_get_local_file_sources(self):
        gb = GBAPI(None, None, source_file = '../data/gb_xml/51.xml')
        res = gb.get_LocalTimeParameters('01')
        self.assertEqual(res.element_type, "LocalTimeParameters")

if __name__ == "__main__":
    unittest.main()

        
