# Tested with Python2.7 on Linux Fedora x86_64 v24 

from decimal import Decimal
import json
import sainsburys_webpage_scraper
from mock import call, Mock, patch, PropertyMock
import unittest

class SainsburysWebpageScraperUnitTests(unittest.TestCase):
	def setUp(self):
		self.requests_patch = patch('sainsburys_webpage_scraper.requests')
		self.requests_mock = self.requests_patch.start()
		self.response_mock = Mock()
		type(self.response_mock).content = PropertyMock(return_value='')  # response.content should be a string
		self.requests_mock.get.return_value = self.response_mock

		self.html_patch = patch('sainsburys_webpage_scraper.html')
		self.html_mock = self.html_patch.start()
		self.tree_mock = Mock()
		self.html_mock.parse.return_value = self.tree_mock  # lxml.parse() in real life returns an lxml.etree._ElementTree

		self.StringIO_patch = patch('sainsburys_webpage_scraper.StringIO')
		self.StringIO_mock = self.StringIO_patch.start()

		self.logging_patch = patch('sainsburys_webpage_scraper.logging')
		self.logging_mock = self.logging_patch.start()

		self.ul_mock = Mock()
		self.li_mock1 = Mock()
		self.li_mock2 = Mock()
		self.li_mock3 = Mock()
		self.ul_mock.getchildren.return_value = [self.li_mock1, self.li_mock2, self.li_mock3]  # mocking 3 products

	def tearDown(self):
		self.requests_patch.stop()
		self.html_patch.stop()
		self.StringIO_patch.stop()
		self.logging_patch.stop()

	def test_get_ripe_fruits_json_1(self):
		'''Should return '' on failure of requests.get().'''
		self.requests_mock.get.side_effect = Exception()
		self.assertEqual(sainsburys_webpage_scraper.get_ripe_fruits_json(), '')
		self.requests_mock.get.assert_called_once_with(sainsburys_webpage_scraper.RIPE_FRUITS_URL, timeout=sainsburys_webpage_scraper.TIMEOUT)
		self.assertTrue(len(self.logging_mock.error.call_args_list) == 1)

	def test_get_ripe_fruits_json_2(self):
		'''Should return '' on failure to locate the <ul> element.'''		
		self.tree_mock.xpath.return_value = []
		self.assertEqual(sainsburys_webpage_scraper.get_ripe_fruits_json(), '')
		self.requests_mock.get.assert_called_once_with(sainsburys_webpage_scraper.RIPE_FRUITS_URL, timeout=sainsburys_webpage_scraper.TIMEOUT)
		self.assertTrue(len(self.logging_mock.error.call_args_list) == 1)

	def test_get_ripe_fruits_json_3(self):	
		'''If the page lists no products, that should be reflected in JSON string.'''	
		self.tree_mock.xpath.return_value = [self.ul_mock]
		self.ul_mock.getchildren.return_value = []
		expected = {
			"results": [],
			"total": "0"
		}
		output = sainsburys_webpage_scraper.get_ripe_fruits_json()
		self.requests_mock.get.assert_called_once_with(sainsburys_webpage_scraper.RIPE_FRUITS_URL, timeout=sainsburys_webpage_scraper.TIMEOUT)
		self.assertEqual(json.loads(output), expected)		

	@patch('sainsburys_webpage_scraper.get_product_details_dict')
	def test_get_ripe_fruits_json_4(self, get_product_details_dict_mock):
		'''If get_product_details_dict() returns {} for any product, that should be reflected in JSON string and a warning should be logged.'''		
		self.tree_mock.xpath.return_value = [self.ul_mock]
		get_product_details_dict_mock.return_value = {}
		expected = {
			"results": [],
			"total": "0"
		}
		output = sainsburys_webpage_scraper.get_ripe_fruits_json()
		self.requests_mock.get.assert_called_once_with(sainsburys_webpage_scraper.RIPE_FRUITS_URL, timeout=sainsburys_webpage_scraper.TIMEOUT)
		self.assertEqual(json.loads(output), expected)
		self.assertEqual(get_product_details_dict_mock.call_args_list, [call(self.li_mock1), call(self.li_mock2), call(self.li_mock3)])
		self.assertTrue(len(self.logging_mock.warn.call_args_list) == 3)
		
	@patch('sainsburys_webpage_scraper.get_product_details_dict')
	def test_get_ripe_fruits_json_5(self, get_product_details_dict_mock):
		'''Normal scenario, get_product_details_dict() returns for all products.'''		
		self.tree_mock.xpath.return_value = [self.ul_mock]
		get_product_details_dict_mock.return_value = {'unit_price': '0.5'}
		expected = {
			"results": 
				[
					{"unit_price": "0.5"}, 
					{"unit_price": "0.5"}, 
					{"unit_price": "0.5"}    
				], 
			"total": "1.5"
		}
		output = sainsburys_webpage_scraper.get_ripe_fruits_json()
		self.requests_mock.get.assert_called_once_with(sainsburys_webpage_scraper.RIPE_FRUITS_URL, timeout=sainsburys_webpage_scraper.TIMEOUT)
		self.assertEqual(json.loads(output), expected)
		self.assertEqual(get_product_details_dict_mock.call_args_list, [call(self.li_mock1), call(self.li_mock2), call(self.li_mock3)])

	@patch('sainsburys_webpage_scraper.get_product_details_dict')
	def test_get_ripe_fruits_json_6(self, get_product_details_dict_mock):	
		'''Scenario where get_product_details_dict() returns {} for one of the products.'''			
		self.tree_mock.xpath.return_value = [self.ul_mock]
		get_product_details_dict_mock.side_effect = [
			{'unit_price': '0.5'},
			{},
			{'unit_price': '0.6', 'some_attribute': 'xyz'}
		]
		expected = {
			"results": 
				[
					{"unit_price": "0.5"}, 
					{'unit_price': '0.6', 'some_attribute': 'xyz'}  
				], 
			"total": "1.1"
		}
		output = sainsburys_webpage_scraper.get_ripe_fruits_json()
		self.requests_mock.get.assert_called_once_with(sainsburys_webpage_scraper.RIPE_FRUITS_URL, timeout=sainsburys_webpage_scraper.TIMEOUT)
		self.assertEqual(json.loads(output), expected)
		self.assertEqual(get_product_details_dict_mock.call_args_list, [call(self.li_mock1), call(self.li_mock2), call(self.li_mock3)])
		self.assertTrue(len(self.logging_mock.warn.call_args_list) == 1)

	@patch('sainsburys_webpage_scraper.get_product_unit_price')
	@patch('sainsburys_webpage_scraper.get_product_link_element')
	@patch('sainsburys_webpage_scraper.get_product_additional_details_dict')
	def test_get_product_details_dict_1(self, get_product_additional_details_dict_mock,
											  get_product_link_element_mock,
											  get_product_unit_price_mock):
		'''Should return {} if any of the details could not be retrieved.'''
		# 1 - Could not get 'unit_price':
		get_product_unit_price_mock.return_value = None
		self.assertEqual(sainsburys_webpage_scraper.get_product_details_dict(self.li_mock1), {})
		get_product_unit_price_mock.assert_called_once_with(self.li_mock1)
		self.assertTrue(len(self.logging_mock.error.call_args_list) == 1)
		self.logging_mock.reset_mock()

		# 2 - Could not get link (case 1):
		get_product_unit_price_mock.return_value = '3.5'
		get_product_link_element_mock.return_value = None
		self.assertEqual(sainsburys_webpage_scraper.get_product_details_dict(self.li_mock1), {})
		get_product_link_element_mock.assert_called_once_with(self.li_mock1)
		self.assertTrue(len(self.logging_mock.error.call_args_list) == 1)
		self.logging_mock.reset_mock()

		# 3 - Could not get link (case 2):
		link_element_mock = Mock()
		link_element_mock.values.return_value = []
		get_product_link_element_mock.return_value = link_element_mock
		self.assertEqual(sainsburys_webpage_scraper.get_product_details_dict(self.li_mock1), {})
		self.assertTrue(len(self.logging_mock.error.call_args_list) == 1)
		self.logging_mock.reset_mock()

		# 4 - Link successfully retrieved but timed out during conection:
		link_mock = Mock()
		link_element_mock.values.return_value = [link_mock]
		self.requests_mock.get.side_effect = Exception()
		self.assertEqual(sainsburys_webpage_scraper.get_product_details_dict(self.li_mock1), {})
		self.requests_mock.get.assert_called_once_with(link_mock, timeout=sainsburys_webpage_scraper.TIMEOUT)
		self.requests_mock.get.reset_mock()
		self.requests_mock.get.side_effect = None 
		self.assertTrue(len(self.logging_mock.error.call_args_list) == 1)
		self.logging_mock.reset_mock()
		
		# 5 - Could not get 'description' (i.e. get_product_additional_details_dict() returned {}):
		get_product_additional_details_dict_mock.return_value = {}
		self.assertEqual(sainsburys_webpage_scraper.get_product_details_dict(self.li_mock1), {})
		self.requests_mock.get.assert_called_once_with(link_mock, timeout=sainsburys_webpage_scraper.TIMEOUT)
		get_product_additional_details_dict_mock.assert_called_once_with(self.response_mock.content)
		self.assertTrue(len(self.logging_mock.error.call_args_list) == 1)
		

	@patch('sainsburys_webpage_scraper.get_product_unit_price')
	@patch('sainsburys_webpage_scraper.get_product_link_element')
	@patch('sainsburys_webpage_scraper.get_product_additional_details_dict')
	def test_get_product_details_dict_2(self, get_product_additional_details_dict_mock,
											  get_product_link_element_mock,
											  get_product_unit_price_mock):
		'''Normal scenario, all product details retrieved successfully.'''
		# 'unit_price':
		get_product_unit_price_mock.return_value = '3.5'
		
		# link (used to get 'title' and 'description')
		link_element_mock = Mock()
		link_mock = Mock()
		link_element_mock.values.return_value = [link_mock]
		get_product_link_element_mock.return_value = link_element_mock

		# 'description':
		get_product_additional_details_dict_mock.return_value = {'description': '123'}

		expected = {
			'unit_price': '3.5',
			'title': link_element_mock.text.strip(),
			'size': '0kb',
			'description': '123'
		}
		output = sainsburys_webpage_scraper.get_product_details_dict(Mock())
		self.assertEqual(output, expected)
		self.requests_mock.get.assert_called_once_with(link_mock, timeout=sainsburys_webpage_scraper.TIMEOUT)
		get_product_additional_details_dict_mock.assert_called_once_with(self.response_mock.content)

	def test_get_product_unit_price(self):
		'''Should return None if unit_price could not be retrieved or if it is in bad shape.'''
		# Could not get unit price (case 1):
		self.li_mock1.xpath.return_value = []
		self.assertEqual(sainsburys_webpage_scraper.get_product_unit_price(self.li_mock1), None)
		self.assertTrue(len(self.logging_mock.error.call_args_list) == 1)
		self.logging_mock.reset_mock()

		div_mock_1 = Mock() # <div class="pricingAndTrolleyOptions">
		div_mock_2 = Mock() # <div id="addItem_****">
		div_mock_2.get.return_value = 'priceTab activeContainer priceTabContainer'  # to pass the second assert()
		p_mock = Mock()  # <p class="pricePerUnit">

		# Could not get unit price (case 2):
		div_mock_1.getchildren.return_value = []
		self.li_mock1.xpath.return_value = [div_mock_1]
		self.assertEqual(sainsburys_webpage_scraper.get_product_unit_price(self.li_mock1), None)
		self.assertTrue(len(self.logging_mock.error.call_args_list) == 1)
		self.logging_mock.reset_mock()

		with patch('sainsburys_webpage_scraper.isinstance') as isinstance_mock:
			# Could not get unit price (case 3):
			isinstance_mock.return_value = True 
			div_mock_1.getchildren.return_value = [Mock(), Mock()]  # more than 1 element in list after filter
			self.assertEqual(sainsburys_webpage_scraper.get_product_unit_price(self.li_mock1), None)
			self.assertTrue(len(self.logging_mock.error.call_args_list) == 1)
			self.logging_mock.reset_mock()

			# Could not get unit price (case 4):
			div_mock_1.getchildren.return_value = [div_mock_2]
			div_mock_2.xpath.return_value = []
			self.assertEqual(sainsburys_webpage_scraper.get_product_unit_price(self.li_mock1), None)	
			self.assertTrue(len(self.logging_mock.error.call_args_list) == 1)
			self.logging_mock.reset_mock()

			# unit_price retrieved but is in bad shape:
			div_mock_2.xpath.return_value = [p_mock]
			p_mock.text = '&poundabc1.23'
			self.assertEqual(sainsburys_webpage_scraper.get_product_unit_price(self.li_mock1), None)
			self.assertTrue(len(self.logging_mock.error.call_args_list) == 1)

			# Normal scenario:
			p_mock.text = '&pound1.23'	
			self.assertEqual(sainsburys_webpage_scraper.get_product_unit_price(self.li_mock1), '1.23')

	def test_get_product_link_element(self):
		'''Should return None if link element (<a>) could not be retrieved.'''
		self.li_mock1.xpath.return_value = []
		self.assertEqual(sainsburys_webpage_scraper.get_product_link_element(self.li_mock1), None)
		self.assertTrue(len(self.logging_mock.error.call_args_list) == 1)

		a_mock = Mock()
		self.li_mock1.xpath.return_value = [a_mock]
		self.assertEqual(sainsburys_webpage_scraper.get_product_link_element(self.li_mock1), a_mock)

	def test_get_product_additional_details_dict(self):
		'''Should return {} if any of the details could not be retrieved.'''
		self.tree_mock.xpath.return_value = []
		self.assertEqual(sainsburys_webpage_scraper.get_product_additional_details_dict('abc'), {})
		self.html_mock.parse.assert_called_once_with(self.StringIO_mock('abc'), parser=self.html_mock.HTMLParser())
		self.html_mock.parse.reset_mock()
		self.assertTrue(len(self.logging_mock.error.call_args_list) == 1)
		self.logging_mock.reset_mock()

		div_mock_1 = Mock()  # <div class="productText">
		p_mock = Mock()  # <p >
		p_mock.text = ' \t123 \n'

		div_mock_1.xpath.return_value = []
		self.tree_mock.xpath.return_value = [div_mock_1]
		self.assertEqual(sainsburys_webpage_scraper.get_product_additional_details_dict('abc'), {})
		self.html_mock.parse.assert_called_once_with(self.StringIO_mock('abc'), parser=self.html_mock.HTMLParser())
		self.html_mock.parse.reset_mock()
		self.assertTrue(len(self.logging_mock.error.call_args_list) == 1)

		# Normal scenario:
		div_mock_1.xpath.return_value = [p_mock]
		self.assertEqual(sainsburys_webpage_scraper.get_product_additional_details_dict('abc'), {'description': '123'})
		self.html_mock.parse.assert_called_once_with(self.StringIO_mock('abc'), parser=self.html_mock.HTMLParser())


class SainsburysWebpageScraperBehaviouralTests(unittest.TestCase):
	def test_1(self):
		json_string = sainsburys_webpage_scraper.get_ripe_fruits_json()
		json_dict = json.loads(json_string)
		self.assertTrue(isinstance(json_dict, dict))
		self.assertEqual(set(json_dict.keys()), set(['total', 'results']))
		results = json_dict['results']
		if not results:
			self.assertEqual(json_dict['total'], 0)
		else:
			total = 0
			for product_details_dict in results:
				self.assertEqual(set(product_details_dict.keys()), set(['title', 'unit_price', 'size', 'description']))
				total += Decimal(product_details_dict['unit_price'])
			self.assertEqual(json_dict['total'], str(total))


if __name__ == '__main__':
	unittest.main()