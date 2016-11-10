
##Sainsbury's Webpage Scraper

This application connects to http://hiring-tests.s3-website-eu-west-1.amazonaws.com/2015_Developer_Scrape/5_products.html and prints a JSON string to stdout with details of the listed products. It relies on XPath (https://en.wikipedia.org/wiki/XPath) to locate elements on the webpage and hence any changes to the webpage's layout may break the application. For each product it retrieves the title, description, unit price and size of the product's individual webpage (which can be reached through the link above).

**Example usage**
	$ python sainsburys_webpage_scraper.py
	{
	    "results": [
	        {
	            "description": "Apricots", 
	            "size": "38kb", 
	            "title": "Sainsbury's Apricot Ripe & Ready x5", 
	            "unit_price": "3.50"
	        }, 
	        {
	            "description": "Avocados", 
	            "size": "38kb", 
	            "title": "Sainsbury's Avocado Ripe & Ready XL Loose 300g", 
	            "unit_price": "1.50"
	        }, 
	        {
	            "description": "Avocados", 
	            "size": "43kb", 
	            "title": "Sainsbury's Avocado, Ripe & Ready x2", 
	            "unit_price": "1.80"
	        }, 
	        {
	            "description": "Avocados", 
	            "size": "38kb", 
	            "title": "Sainsbury's Avocados, Ripe & Ready x4", 
	            "unit_price": "3.20"
	        }, 
	        {
	            "description": "Conference", 
	            "size": "38kb", 
	            "title": "Sainsbury's Conference Pears, Ripe & Ready x4 (minimum)", 
	            "unit_price": "1.50"
	        }, 
	        {
	            "description": "Gold Kiwi", 
	            "size": "38kb", 
	            "title": "Sainsbury's Golden Kiwi x4", 
	            "unit_price": "1.80"
	        }, 
	        {
	            "description": "Kiwi", 
	            "size": "38kb", 
	            "title": "Sainsbury's Kiwi Fruit, Ripe & Ready x4", 
	            "unit_price": "1.80"
	        }
	    ], 
	    "total": "15.10"
	}
	$ 

**Dependencies & Installation**
	- **OS**
		This application is OS independent, as long as a Python interpreter is installed.
	- **Python**
		This application works with Python2.7+ and will not work with Python3+ due to various differences between the two, e.g. string representation and standard library/external APIs.
	- **Python Packages**
		After installing Python, verify that it is installed correctly and added to your PATH variable. An easy check to do is:
			$ python --version
			Python 2.7.12

		Next, install the following packages:
			* lxml (http://lxml.de/)
			* requests (http://docs.python-requests.org/en/master/)

		The best way to install packages is by first installing pip (https://pypi.python.org/pypi/pip). On Linux for e.g. installing Python packages with pip is as simple as:
			$ sudo pip install lxml
			$ sudo pip install requests

		Note that the lxml package relies on certain libraries to be installed on the OS; see http://lxml.de/installation.html for more details.

**Running**
	To run the application, simply type:
		$ python sainsburys_webpage_scraper.py
	in your console and the JSON string will be printed.

	To run the associated tests, make sure that "test_sainsburys_webpage_scraper.py" is in the same directory as "sainsburys_webpage_scraper.py" and then type:
		$ python test_sainsburys_webpage_scraper.py
	You will see something similar to this:
		$ python test_sainsburys_webpage_scraper.py
		............
		----------------------------------------------------------------------
		Ran 12 tests in 2.046s

		OK
		$

**Troubleshooting**
	If the output looks like this:
		{
			"results": [],
			"total": "0"
		}
	and there are no error messages, that means that either:
		1) There are no products listed on the webpage, nothing to worry about.
		2) There are products listed but their details could not be retrieved. In this case there will definitely be error/warning messages displayed before the output.

	**Errors/Warning messages:**
		These would be in the format: 
			[{ERROR | WARNING} {FILENAME}: {LINE_NUMBER} - {FUNCTION_NAME}] MESSAGE
		
		- **XPath expression failed**
			[ERROR    sainsburys_webpage_scraper.py: 194 - get_product_link_element ] XPath expression failed

			This error means that the XPath expression used to reach a certain element withing the tree did not yield any results. This most definitely means a change was made to the layout of the website or to the identifiers of certain elements. If that is the case then the webpage needs to be studied and changes need to be made to sainsburys_webpage_scraper.py
			The first thing to do is to go to the line number (e.g. 194 above) and make changes to the string passed into the .xpath() method immediately above the line where the error message is pointing to. 

		- **Could not build product_details_dict for product number {x}, skipping**
			[WARNING  sainsburys_webpage_scraper.py:  70 - get_ripe_fruits_json] Could not get product_dict for product number 1, skipping

			This warning message means that details for a certain product were not retrieved successfully and so that product will not be included in the final JSON string. This error is most definitely preceded by a "XPath expression failed" error.

		- **Connecting to {x} failed with {y}**
			[ERROR    sainsburys_webpage_scraper.py:  46 - get_ripe_fruits_json     ] Connecting to "http://hiring-tests.s3-website-eu-west-1.amazonaws.com/2015_Developer_Scrape/5_products.html" failed with: HTTPConnectionPool(host='hiring-tests.s3-website-eu-west-1.amazonaws.com', port=80): Max retries exceeded with url: /2015_Developer_Scrape/5_products.html (Caused by NewConnectionError('<requests.packages.urllib3.connection.HTTPConnection object at 0x7fceeb66d750>: Failed to establish a new connection: [Errno 115] Operation now in progress',))

			This error message means that an HTTP request failed for some reason. The most common reason for this is timeout. Try increasing the value (seconds) of the TIMEOUT variable at the top of sainsburys_webpage_scraper.py (TIMEOUT = 5). If that doesn't work then try entering the link in your browser. If that still doesn;t work that means the link is broken.

			Note: The main URL is defined at the top of sainsburys_webpage_scraper.py (RIPE_FRUITS_URL = ...). If connection failed for this URL then the resulting JSON string will be empty as the main page is crucial. If connection failed for one of the embedded links (there will be one link per product) then the product will be skipped (and warning message issued as mentioned in previous point).

		Other errors that may be displayed would mostly be a result of the errors above, in particular the "XPath expression failed" error.











