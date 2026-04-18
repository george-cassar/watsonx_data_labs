"""
LXML Library Test Application
==============================
A simple test application to verify the lxml library installation and functionality.

This application performs the following operations:
1. Tests lxml XML parsing capabilities
2. Tests lxml HTML parsing capabilities
3. Tests XPath queries
4. Displays formatted results with proper error handling

Best Practices Implemented:
- Global configuration constants for easy maintenance
- Proper error handling and logging with timestamps
- Comprehensive test coverage of lxml features
- Graceful error handling with detailed messages
- Exit codes for automation (0=success, 1=failure)

Library Tested:
- lxml: Fast and feature-rich XML/HTML processing library

Usage:
    Run directly as a standalone Python script:
    python lxml_test.py
    
    Or submit via watsonx.data with accompanying JSON payload
"""

from lxml import etree
from lxml import html
import traceback
from datetime import datetime
import sys

# ============================================================================
# CONFIGURATION - Global Constants
# ============================================================================

# Sample XML for testing
SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<catalog>
    <product id="1">
        <name>Laptop</name>
        <category>Electronics</category>
        <price currency="USD">999.99</price>
        <stock>50</stock>
    </product>
    <product id="2">
        <name>Smartphone</name>
        <category>Electronics</category>
        <price currency="USD">699.99</price>
        <stock>100</stock>
    </product>
    <product id="3">
        <name>Desk Chair</name>
        <category>Furniture</category>
        <price currency="USD">299.99</price>
        <stock>25</stock>
    </product>
</catalog>
"""

# Sample HTML for testing
SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>watsonx.data Test Page</title>
</head>
<body>
    <h1>Welcome to watsonx.data</h1>
    <div class="content">
        <p class="intro">This is a test of lxml HTML parsing capabilities.</p>
        <ul id="features">
            <li>Feature 1: Data lakehouse architecture</li>
            <li>Feature 2: Open table formats (Iceberg, Hudi, Delta)</li>
            <li>Feature 3: Multiple query engines (Presto, Spark)</li>
        </ul>
    </div>
    <div class="footer">
        <p>Powered by IBM watsonx.data</p>
    </div>
</body>
</html>
"""

def log(msg: str, level: str = "INFO"):
    """
    Log message with timestamp to stdout.
    
    Provides consistent logging format with ISO timestamps for
    troubleshooting and auditing.
    
    Args:
        msg: Message to log
        level: Log level - "INFO", "WARN", or "ERROR" (default: "INFO")
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f"[{timestamp}] [{level}] {msg}"
    print(formatted_msg)

def test_xml_parsing():
    """
    Test lxml XML parsing capabilities.
    
    Demonstrates:
    1. Parsing XML from string
    2. Accessing elements and attributes
    3. Iterating through elements
    4. Extracting text content
    
    Returns:
        bool: True if test passed, False otherwise
    """
    try:
        log("=" * 80)
        log("Test 1: XML Parsing with lxml.etree")
        log("=" * 80)
        
        # Parse XML
        log("Parsing XML document...")
        root = etree.fromstring(SAMPLE_XML.encode('utf-8'))
        
        log(f"✓ Root element: <{root.tag}>")
        log(f"✓ Number of products: {len(root)}")
        
        # Iterate through products
        log("\nProduct Details:")
        log("-" * 80)
        
        for product in root.findall('product'):
            product_id = product.get('id')
            name = product.find('name').text
            category = product.find('category').text
            price = product.find('price').text
            currency = product.find('price').get('currency')
            stock = product.find('stock').text
            
            log(f"\nProduct ID: {product_id}")
            log(f"  Name: {name}")
            log(f"  Category: {category}")
            log(f"  Price: {currency} {price}")
            log(f"  Stock: {stock} units")
        
        log("\n" + "=" * 80)
        log("✓ XML parsing test PASSED")
        log("=" * 80)
        
        return True
        
    except Exception as e:
        log(f"ERROR: XML parsing test failed: {str(e)}", "ERROR")
        log(traceback.format_exc(), "ERROR")
        return False

def test_xpath_queries():
    """
    Test lxml XPath query capabilities.
    
    Demonstrates:
    1. XPath element selection
    2. XPath attribute selection
    3. XPath filtering with predicates
    4. XPath text extraction
    
    Returns:
        bool: True if test passed, False otherwise
    """
    try:
        log("\n" + "=" * 80)
        log("Test 2: XPath Queries with lxml")
        log("=" * 80)
        
        # Parse XML
        root = etree.fromstring(SAMPLE_XML.encode('utf-8'))
        
        # Test 1: Select all product names
        log("\nXPath Query 1: //product/name/text()")
        names = root.xpath('//product/name/text()')
        log(f"✓ Found {len(names)} product names:")
        for name in names:
            log(f"  - {name}")
        
        # Test 2: Select products in Electronics category
        log("\nXPath Query 2: //product[category='Electronics']/name/text()")
        electronics = root.xpath("//product[category='Electronics']/name/text()")
        log(f"✓ Found {len(electronics)} electronics products:")
        for name in electronics:
            log(f"  - {name}")
        
        # Test 3: Select products with price > 500
        log("\nXPath Query 3: //product[price>500]/name/text()")
        expensive = root.xpath("//product[price>500]/name/text()")
        log(f"✓ Found {len(expensive)} products over $500:")
        for name in expensive:
            log(f"  - {name}")
        
        # Test 4: Get all product IDs
        log("\nXPath Query 4: //product/@id")
        ids = root.xpath('//product/@id')
        log(f"✓ Found {len(ids)} product IDs: {', '.join(ids)}")
        
        # Test 5: Calculate total stock
        log("\nXPath Query 5: sum(//product/stock)")
        total_stock = root.xpath('sum(//product/stock)')
        log(f"✓ Total stock across all products: {int(total_stock)} units")
        
        log("\n" + "=" * 80)
        log("✓ XPath queries test PASSED")
        log("=" * 80)
        
        return True
        
    except Exception as e:
        log(f"ERROR: XPath queries test failed: {str(e)}", "ERROR")
        log(traceback.format_exc(), "ERROR")
        return False

def test_html_parsing():
    """
    Test lxml HTML parsing capabilities.
    
    Demonstrates:
    1. Parsing HTML from string
    2. Accessing elements by tag
    3. Accessing elements by class
    4. Accessing elements by ID
    5. XPath queries on HTML
    
    Returns:
        bool: True if test passed, False otherwise
    """
    try:
        log("\n" + "=" * 80)
        log("Test 3: HTML Parsing with lxml.html")
        log("=" * 80)
        
        # Parse HTML
        log("Parsing HTML document...")
        doc = html.fromstring(SAMPLE_HTML)
        
        # Extract title
        title = doc.xpath('//title/text()')[0]
        log(f"\n✓ Page Title: {title}")
        
        # Extract heading
        h1 = doc.xpath('//h1/text()')[0]
        log(f"✓ Main Heading: {h1}")
        
        # Extract intro paragraph by class
        intro = doc.xpath('//p[@class="intro"]/text()')[0]
        log(f"✓ Intro Text: {intro}")
        
        # Extract list items
        log("\n✓ Features List:")
        features = doc.xpath('//ul[@id="features"]/li/text()')
        for idx, feature in enumerate(features, 1):
            log(f"  {idx}. {feature}")
        
        # Extract footer
        footer = doc.xpath('//div[@class="footer"]/p/text()')[0]
        log(f"\n✓ Footer: {footer}")
        
        # Count elements
        log("\n✓ Element Counts:")
        div_count = len(doc.xpath('//div'))
        p_count = len(doc.xpath('//p'))
        li_count = len(doc.xpath('//li'))
        log(f"  - <div> elements: {div_count}")
        log(f"  - <p> elements: {p_count}")
        log(f"  - <li> elements: {li_count}")
        
        log("\n" + "=" * 80)
        log("✓ HTML parsing test PASSED")
        log("=" * 80)
        
        return True
        
    except Exception as e:
        log(f"ERROR: HTML parsing test failed: {str(e)}", "ERROR")
        log(traceback.format_exc(), "ERROR")
        return False

def test_xml_creation():
    """
    Test lxml XML creation capabilities.
    
    Demonstrates:
    1. Creating XML elements programmatically
    2. Setting attributes
    3. Adding child elements
    4. Converting to string
    
    Returns:
        bool: True if test passed, False otherwise
    """
    try:
        log("\n" + "=" * 80)
        log("Test 4: XML Creation with lxml")
        log("=" * 80)
        
        # Create root element
        log("Creating XML document programmatically...")
        root = etree.Element("customers")
        
        # Add customer 1
        customer1 = etree.SubElement(root, "customer", id="1")
        name1 = etree.SubElement(customer1, "name")
        name1.text = "John Doe"
        email1 = etree.SubElement(customer1, "email")
        email1.text = "john.doe@example.com"
        
        # Add customer 2
        customer2 = etree.SubElement(root, "customer", id="2")
        name2 = etree.SubElement(customer2, "name")
        name2.text = "Jane Smith"
        email2 = etree.SubElement(customer2, "email")
        email2.text = "jane.smith@example.com"
        
        # Convert to string
        xml_string = etree.tostring(root, pretty_print=True, encoding='unicode')
        
        log("\n✓ Created XML document:")
        log("-" * 80)
        log(xml_string)
        log("-" * 80)
        
        # Verify structure
        log(f"✓ Root element: <{root.tag}>")
        log(f"✓ Number of customers: {len(root)}")
        log(f"✓ Customer IDs: {', '.join([c.get('id') for c in root])}")
        
        log("\n" + "=" * 80)
        log("✓ XML creation test PASSED")
        log("=" * 80)
        
        return True
        
    except Exception as e:
        log(f"ERROR: XML creation test failed: {str(e)}", "ERROR")
        log(traceback.format_exc(), "ERROR")
        return False

def display_library_info():
    """
    Display version information for lxml library.
    
    Shows the version of lxml to help with troubleshooting
    and ensuring the correct version is installed.
    """
    log("\n" + "=" * 80)
    log("Library Version Information")
    log("=" * 80)
    
    try:
        log(f"lxml.etree: {etree.LXML_VERSION}")
        log(f"libxml2: {etree.LIBXML_VERSION}")
        log(f"libxslt: {etree.LIBXSLT_VERSION}")
    except Exception as e:
        log(f"lxml: ERROR - {str(e)}", "ERROR")
    
    log("=" * 80)

def main():
    """
    Main execution function with comprehensive testing.
    
    Executes all lxml tests in sequence:
    1. Display library version information
    2. Test XML parsing
    3. Test XPath queries
    4. Test HTML parsing
    5. Test XML creation
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        log("=" * 80)
        log("LXML Library Test Application")
        log("=" * 80)
        log(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Display library versions
        display_library_info()
        
        # Run tests
        results = []
        
        # Test 1: XML parsing
        results.append(("XML Parsing", test_xml_parsing()))
        
        # Test 2: XPath queries
        results.append(("XPath Queries", test_xpath_queries()))
        
        # Test 3: HTML parsing
        results.append(("HTML Parsing", test_html_parsing()))
        
        # Test 4: XML creation
        results.append(("XML Creation", test_xml_creation()))
        
        # Summary
        log("\n" + "=" * 80)
        log("TEST SUMMARY")
        log("=" * 80)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✓ PASSED" if result else "✗ FAILED"
            log(f"{test_name}: {status}")
        
        log("-" * 80)
        log(f"Total: {passed}/{total} tests passed")
        log("=" * 80)
        
        if passed == total:
            log("\n✓ All tests PASSED - lxml library is working correctly!")
            log(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return 0
        else:
            log(f"\n✗ {total - passed} test(s) FAILED", "ERROR")
            log(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return 1
        
    except Exception as e:
        log(f"\n✗ Fatal error: {str(e)}", "ERROR")
        log(traceback.format_exc(), "ERROR")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

