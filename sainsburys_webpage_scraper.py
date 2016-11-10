# Tested with Python2.7 on Linux Fedora x86_64 v24 

from cStringIO import StringIO
from decimal import Decimal
import json
import logging
from lxml import html
import requests

logging.basicConfig(format="[%(levelname)-8s %(filename)s: %(lineno)3s - %(funcName)-25s] %(message)s", level=logging.WARNING)

RIPE_FRUITS_URL = 'http://hiring-tests.s3-website-eu-west-1.amazonaws.com/2015_Developer_Scrape/5_products.html'
TIMEOUT = 5

def get_ripe_fruits_json():
	""" Uses lxml's support for XPath syntax to return a JSON string based on the products listed in RIPE_FRUITS_URL.
	
	Example (if RIPE_FRUITS_URL listed 2 products):
		{
		    "results": [
				{
		            "description": "Apricots", 
		            "size": "38kb", 
		            "title": "Sainsbury's Apricot Ripe & Ready x5", 
		            "unit_price": "3.50"
		        }, 

		        {
		            "description": "Kiwi", 
		            "size": "38kb", 
		            "title": "Sainsbury's Kiwi Fruit, Ripe & Ready x4", 
		            "unit_price": "1.80"
		        }
		    ], 
		    "total": "5.30"
		}

	"description" is retrieved from the embedded link which leads to the individual product's page.
	"size" is the size (in kb) of the individual product's page contents excluding images etc. (i.e. just the markup).
	"size" is presented as "0kb" for pages less than 1kb.
	"total" is the sum of the "unit_price" across all products.
	"title" and "unit_price" are both retrieved directly from RIPE_FRUITS_URL and not from the embedded link (same result).
	
	This function returns an empty string in two cases:
		1 - Connection to RIPE_FRUITS_URL timed out.
		2 - HTML parser unable to locate the <ul> element which lists the products.
	"""
	try:
		response = requests.get(RIPE_FRUITS_URL, timeout=TIMEOUT)
	except Exception as ex:
		logging.error('Connecting to "%s" failed with:\n\t%s' %(RIPE_FRUITS_URL, ex))
		return ''

	tree = html.parse(StringIO(response.content), parser=html.HTMLParser())
	ul = tree.xpath('''body/
						div[@id='page']/
							div[@id='main']/
								div[@id='content']/
									div[@id='productsContainer']/
										div[@id='productLister']/
											ul[@class='productLister listView']''')
	try:
		ul = ul[0]
	except IndexError:
		logging.error('XPath expression failed')
		return ''
	
	i = 0
	total = 0
	results = []
	
	# The <ul> tag has multiple <li> tags, each which represents a single product.
	ul_children = ul.getchildren()
	logging.info('Found %s products listed on "%s"' %(len(ul_children), RIPE_FRUITS_URL))
	for li in ul_children:  
		i += 1
		logging.info('Processing product number %s' %i)
		product_details_dict = get_product_details_dict(li)
		if not product_details_dict:
			logging.warn('Could not build product_details_dict for product number %s, skipping' %i)
			continue
		results.append(product_details_dict)
		total += Decimal(product_details_dict['unit_price'])

	# total is cast back to a str since json.dumps cannot handle decimal.Decimal types
	return json.dumps({'results': results, 'total': str(total)}, indent=4, sort_keys=True)  

def get_product_details_dict(li):
	"""Returns a dictionary with details of the product in the <li> tag.
	
	If any of the details could not be found an empty dictionary is returned even if other details were retrieved.
	"""
	product_details_dict = {}

	unit_price = get_product_unit_price(li)
	if unit_price is None:
		logging.error('Could not get "unit_price" for product')
		return {}
	product_details_dict['unit_price'] = unit_price

	link_element = get_product_link_element(li)
	if link_element is None:
		logging.error('Could not get link to product page')
		return {}
	
	product_details_dict['title'] = link_element.text.strip()
	
	try:
		link = link_element.values()[0]
	except IndexError: 
		logging.error('Could not get link to product page')
		return {}

	try:
		response = requests.get(link, timeout=TIMEOUT)
	except Exception as ex:
		logging.error('Connecting to "%s" failed with:\n\t%s' %(link, ex))
		return {}
	
	# In Python2, len(str) == the no. of bytes used to represent it, unlike in Python3 where 
	# a str  needs to be explicitly converted to a `bytes` object using a particular encoding.
	product_page_content = response.content
	product_details_dict['size'] = str(len(product_page_content)/1024)+'kb'  

	product_additional_details_dict = get_product_additional_details_dict(product_page_content)
	description = product_additional_details_dict.get('description')
	if description is None:
		logging.error('Could not get "description" for product')
		return {}
	product_details_dict['description'] = description
	
	return product_details_dict

def get_product_unit_price(li):
	"""Returns the product's unit price as a str (e.g. '3.50') or None if it couldn't retrieve it.

	Retrieving the product's unit price is tricky since the <div> element we need has a dynamically generated id 
	attribute so it is not possible to reference it directly using a single XPath expression, we need to do some work.
	"""
	pricingAndTrolleyOptionsDiv = li.xpath('''div[@class='product ']/
												div[@class='productInner']/
													div[@class='addToTrolleytabBox']/
														div[@class='addToTrolleytabContainer addItemBorderTop']/
															div[@class='pricingAndTrolleyOptions']''')
	try:
		pricingAndTrolleyOptionsDiv = pricingAndTrolleyOptionsDiv[0]
	except IndexError:
		logging.error('XPath expression failed')
		return None

	# Below, we get pricingAndTrolleyOptionsDiv's child elements and filter out the comments to get addItemDiv.
	# addItemDiv is the <div> element mentioned in the docstring, which looks something like: 
	# 		<div id="addItem_149117" class="priceTab activeContainer priceTabContainer">
	# where the '_149117' part is different for each product.
	# Techinically we could have just used the class attribute to get it, but when given a choice between id
	# and class it is better to use id since that is less likely to change.
	addItemDiv = filter(lambda x: isinstance(x, html.HtmlElement), pricingAndTrolleyOptionsDiv.getchildren())  # getting rid of comments
	try:
		assert(len(addItemDiv) == 1)  # sanity check, there should be only 1 child element (a single <div>) left after filtering
		addItemDiv = addItemDiv[0]
		assert(addItemDiv.get('class') == 'priceTab activeContainer priceTabContainer')  # just to make sure it's the one
	except AssertionError:
		logging.error('XPath expression failed')
		return None

	unit_price_text = addItemDiv.xpath('''div[@class='pricing']/
											p[@class='pricePerUnit']''')
	try:
		unit_price_text = unit_price_text[0].text
	except IndexError:
		logging.error('XPath expression failed')
		return None

	unit_price = unit_price_text.strip().replace('&pound', '')
	if not unit_price.replace('.', '').isdigit():
		logging.error('"%s" is not a valid price' % unit_price)
		return None

	return unit_price

def get_product_link_element(li): 
	"""Returns the <a> element which contains the product's name and the link to the product's individual page.
	
	Returns None if the <a> element could not be retrieved.
	"""
	a = li.xpath('''div[@class='product ']/
						div[@class='productInner']/
							div[@class='productInfoWrapper']/
								div[@class='productInfo']/
									h3/
										a''')
	try:
		a = a[0]
		return a
	except IndexError:
		logging.error('XPath expression failed')
		return None

def get_product_additional_details_dict(product_page_content):
	"""Returns a dictionary with additional details about the individual product.

	While get_product_dict() retrieves any information directly from RIPE_FRUITS_URL, get_product_details_dict()
	retrieves information by following the link embedded in RIPE_FRUITS_URL which leads to the product's actual page 
	which holds more information.

	This function currently only returns the "description" key but should be broken down into smaller functions if  
	more keys are required.

	This function is guaranteed to return at least an empty dictionary if details could not be retrieved.
	"""

	product_additional_details_dict = {}

	subtree = html.parse(StringIO(product_page_content), parser=html.HTMLParser())
	productTextDiv = subtree.xpath('''body/
										div[@id='page']/
											div[@id='main']/
												div[@id='content']/
													div[@class='section productContent']/
														div[@class='mainProductInfoWrapper']/
															div[@class='mainProductInfo']/
																div[@class='tabs']/
																	div[@id='information']/
																		productcontent/
																			htmlcontent/
																				div[@class='productText']''')
	try:
		productTextDiv = productTextDiv[0]
		productNameElement = productTextDiv.xpath("p")
		product_additional_details_dict['description'] = productNameElement[0].text.strip()
	except IndexError:
		logging.error('XPath expression failed')

	return product_additional_details_dict

def main():
	json_string = get_ripe_fruits_json()
	print json_string


if __name__ == '__main__':
	main()