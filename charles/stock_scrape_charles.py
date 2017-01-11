#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Module scrapes and analyzes stock data"""

import re
import datetime as datetime
from random import randint
import time
import math
import csv
import os
from selenium import webdriver

## GLOBAL CONSTANTS
NASDAQ = "NASDAQ"
NYSE = "NYSE"
TSE = "TSE"
RESULT_MULTIPLIER = "K"

TO_DEL_COLUMN_HEADER = [
    "Stock Symbol",
    "Exchange",
    "Stock Name",
    "Last Price",
    "Last Price Date",
    "Current PE Ratio",
    "Avg ROE",
    "Avg ROE Error",
    "Avg ROTC",
    "Avg ROTC Error",
    "Avg ROTA",
    "Avg ROTA Error",
    "EPS CAGR",
    "EPS CAGR Error",
    "BPS CAGR",
    "BPS CAGR Error",
    "CAGR Used",
    "Future PE Ratio (Calc)"
    "Ratio Used for Prediction",
    "Predicted Price today",
    "MOS Year",
    "MOS Something",
    "MOS Sticker Price",
    "MOS Price",
    "Value Ratio"
    "Score Returns ROE/TC/TA",
    "Score Returns Fluctuation",
    "Score Growth EPS/BPS CAGR",
    "Score Growth Fluctuation",
    "Score Value",
    "Score Total",
    "Alt Returns ROE/TC/TA",
    "Alt Returns Fluctuation",
    "Alt Growth EPS/BPS CAGR",
    "Alt Growth Fluctuation",
    "Alt Value",
    "Alt Total",
    "Bank Returns ROE/TC/TA",
    "Bank Returns Fluctuation",
    "Bank Growth EPS/BPS CAGR",
    "Bank Growth Fluctuation",
    "Bank Value",
    "Bank Total"
]

def return_base_url(stock_symbol, exchange=None):
    """Return string of the URL to visit given a stock symbol and stock exchange
    Stock exchange can be blank
    """
    ## URL CONSTANTS
    const_base_url = 'https://www.google.com/finance?q='
    const_nasdaq_url_prefix = 'NASDAQ%3A'
    const_nyse_url_prefix = 'NYSE%3A'
    const_tse_url_prefix = 'TSE%3A'
    if not exchange:
        return const_base_url + stock_symbol
    else:
        if exchange == TSE:
            return const_base_url + const_tse_url_prefix + stock_symbol
        elif exchange == NYSE:
            return const_base_url + const_nyse_url_prefix + stock_symbol
        elif exchange == NASDAQ:
            return const_base_url + const_nasdaq_url_prefix + stock_symbol
        else:
            return const_base_url + stock_symbol
def return_finance_url(stock_symbol, exchange):
    """Returns the path to the financials page from the main stock listing page,
    e.g. on Google Finance"""
    const_financial_url_path = '&fstype=ii'
    return return_base_url(stock_symbol, exchange) + const_financial_url_path
def initialize_browser():
    """Initialize browser, also includes using an adblocker"""
    # const_adblock_xpi_path = 'res/adblock_plus-2.8.2-an+fx+sm+tb.xpi'
    # load Firefox with adblock plus enabled
    # ABP has a problem with FirstRun, so I chose uBlock Origin instead

    # I dont think this is 100 percent fixed
    const_adblock_xpi_path = 'res/uBlock0.firefox.xpi'  # load Firefox with uBlock Origin enabled
    ffprofile = webdriver.FirefoxProfile()
    ffprofile.add_extension(const_adblock_xpi_path)
    browser = webdriver.Firefox(firefox_profile=ffprofile)
    return browser
def browser_load_url(browser, url_string):
    """load browser from url_string"""
    browser.get(url_string)
    browser_wait()
def browser_quit(browser):
    """Quits the browser"""
    browser.quit()
def browser_wait(approx_time=None):
    """Randomizes an arbitrary wait time (in sec)"""
    if (not approx_time) or approx_time < 3:
        time.sleep(2 + randint(0, 2))
    else:
        time.sleep(approx_time + randint(0, round(0.5 * approx_time)))
def browser_xpath_click(browser, xpath_string):
    """Performs a browser click with a wait command"""
    browser.find_element_by_xpath(xpath_string).click()
    browser_wait()


def grab_summary_data(browser, stock_symbol):
    """Retrieves basic information from Finance Website, eg
    stock name, symbol, current PE ratio, last price
    """
    const_summary_xpaths_dict = {'stock_name': """/html/body/div[@class='fjfe-bodywrapper']
        /div[@id='fjfe-real-body']/div[@id='fjfe-click-wrapper']/div[@id='appbar']
        /div[@class='elastic']/div[@class='appbar-center']
        /div[@class='appbar-snippet-primary']/span""",
                                 'stock_symbol': """/html/body/div[@class='fjfe-bodywrapper']
        /div[@id='fjfe-real-body']/div[@id='fjfe-click-wrapper']/div[@id='appbar']
        /div[@class='elastic']/div[@class='appbar-center']
        /div[@class='appbar-snippet-secondary']/span""",
                                 'current_pe': """/html/body/div[@class='fjfe-bodywrapper']
        /div[@id='fjfe-real-body']/div[@id='fjfe-click-wrapper']/div[@class='elastic']
        /div[@id='app']/div[@id='gf-viewc']/div[@class='fjfe-content']/div[@class='g-wrap']
        /div[@class='g-section g-tpl-right-1']/div[@class='g-unit']/div[@id='market-data-div']
        /div[@class='snap-panel-and-plusone']/div[@class='snap-panel']/table[@class='snap-data']
        [1]/tbody/tr[6]/td[@class='val']""",
                                 'employees': """/html/body/div[@class='fjfe-bodywrapper']
        /div[@id='fjfe-real-body']/div[@id='fjfe-click-wrapper']/div[@class='elastic']
        /div[@id='app']/div[@id='gf-viewc']/div[@class='fjfe-content']/div[@class='g-wrap']
        /div[@class='g-section g-tpl-right-1 sfe-break-top-5']/div[@class='g-unit g-first']
        /div[@class='g-c']/div[@class='sfe-section'][1]/table[@class='quotes rgt nwp']/tbody/tr[6]
        /td[@class='period'][1]""",
                                 'market_cap': """/html/body/div[@class='fjfe-bodywrapper']
        /div[@id='fjfe-real-body']/div[@id='fjfe-click-wrapper']/div[@class='elastic']
        /div[@id='app']/div[@id='gf-viewc']/div[@class='fjfe-content']/div[@class='g-wrap']
        /div[@class='g-section g-tpl-right-1']/div[@class='g-unit']/div[@id='market-data-div']
        /div[@class='snap-panel-and-plusone']/div[@class='snap-panel']/table[@class='snap-data'][1]
        /tbody/tr[5]/td[@class='val']"""}
    result_dict = dict()
    try:
        result_dict['Stock Symbol'] = browser.find_element_by_xpath\
            (const_summary_xpaths_dict['stock_symbol']).text.strip('()').split(':')[1]
    except:
        result_dict['Stock Symbol'] = 'N/A'
    try:
        result_dict['Exchange'] = browser.find_element_by_xpath\
            (const_summary_xpaths_dict['stock_symbol']).text.strip('()').split(':')[0]
    except:
        result_dict['Exchange'] = 'N/A'
    try:
        result_dict['Stock Name'] = browser.find_element_by_xpath\
            (const_summary_xpaths_dict['stock_name']).text
    except:
        result_dict['Stock Name'] = 'N/A'
    try:
        market_cap_as_float = convert_readable_num_to_float(browser.find_element_by_xpath\
            (const_summary_xpaths_dict['market_cap']).text, RESULT_MULTIPLIER)
        result_dict['Market Cap'] = market_cap_as_float
    except:
        result_dict['Market Cap'] = 'N/A'
    try:
        employees_as_string = browser.find_element_by_xpath\
            (const_summary_xpaths_dict['employees']).text
        result_dict['Employees'] = int(convert_readable_num_to_float(employees_as_string))
    except:
        result_dict['Employees'] = 'N/A'
    try:
        result_dict['Current PE Ratio'] = browser.find_element_by_xpath\
            (const_summary_xpaths_dict['current_pe']).text.strip()
    except:
        result_dict['Current PE Ratio'] = 'N/A'

    return result_dict
def grab_income_statement_data(browser):
    """Extract data from income statement page of Google Finance, need to pass in browser object """
    const_multipler_xpath = """/html/body/div[@class='fjfe-bodywrapper']/div[@id='fjfe-real-body']
        /div[@id='fjfe-click-wrapper']/div[@class='elastic']/div[@id='app']/div[@id='gf-viewc']
        /div[@class='fjfe-content']/div[@id='incannualdiv']/table[@id='fs-table']/thead/tr
        /th[@class='lm lft nwp']"""
    const_income_statements_xpath = {'total_revenue_this_year': """/html/body
        /div[@class='fjfe-bodywrapper']/div[@id='fjfe-real-body']/div[@id='fjfe-click-wrapper']
        /div[@class='elastic']/div[@id='app']/div[@id='gf-viewc']/div[@class='fjfe-content']
        /div[@id='incannualdiv']/table[@id='fs-table']/tbody/tr[@class='hilite'][1]
        /td[@class='r bld'][1]""",
                                     'cost_of_revenue': """/html/body/div[@class='fjfe-bodywrapper']
        /div[@id='fjfe-real-body']/div[@id='fjfe-click-wrapper']/div[@class='elastic']
        /div[@id='app']/div[@id='gf-viewc']/div[@class='fjfe-content']/div[@id='incannualdiv']
        /table[@id='fs-table']/tbody/tr[4]/td[@class='r'][1]""",
                                     'gross_profit' : """/html/body/div[@class='fjfe-bodywrapper']
        /div[@id='fjfe-real-body']/div[@id='fjfe-click-wrapper']/div[@class='elastic']
        /div[@id='app']/div[@id='gf-viewc']/div[@class='fjfe-content']/div[@id='incannualdiv']
        /table[@id='fs-table']/tbody/tr[@class='hilite'][2]/td[@class='r bld'][1]""",
                                     'sell_gen_admin_exp': """/html/body
        /div[@class='fjfe-bodywrapper']/div[@id='fjfe-real-body']/div[@id='fjfe-click-wrapper']
        /div[@class='elastic']/div[@id='app']/div[@id='gf-viewc']/div[@class='fjfe-content']
        /div[@id='incannualdiv']/table[@id='fs-table']/tbody/tr[6]/td[@class='r'][1]""",
                                     'r_and_d': """/html/body/div[@class='fjfe-bodywrapper']
        /div[@id='fjfe-real-body']/div[@id='fjfe-click-wrapper']/div[@class='elastic']
        /div[@id='app']/div[@id='gf-viewc']/div[@class='fjfe-content']/div[@id='incannualdiv']
        /table[@id='fs-table']/tbody/tr[7]/td[@class='r'][1]""",
                                     'net_income_this_year': """/html/body
        /div[@class='fjfe-bodywrapper']/div[@id='fjfe-real-body']/div[@id='fjfe-click-wrapper']
        /div[@class='elastic']/div[@id='app']/div[@id='gf-viewc']/div[@class='fjfe-content']
        /div[@id='incannualdiv']/table[@id='fs-table']/tbody/tr[@class='hilite'][8]
        /td[@class='r bld'][1]""",
                                     'total_revenue_last_year': """/html/body
        /div[@class='fjfe-bodywrapper']/div[@id='fjfe-real-body']/div[@id='fjfe-click-wrapper']
        /div[@class='elastic']/div[@id='app']/div[@id='gf-viewc']/div[@class='fjfe-content']
        /div[@id='incannualdiv']/table[@id='fs-table']/tbody/tr[@class='hilite'][1]
        /td[@class='r bld'][2]""",
                                     'net_income_last_year': """/html/body
        /div[@class='fjfe-bodywrapper']/div[@id='fjfe-real-body']/div[@id='fjfe-click-wrapper']
        /div[@class='elastic']/div[@id='app']/div[@id='gf-viewc']/div[@class='fjfe-content']
        /div[@id='incannualdiv']/table[@id='fs-table']/tbody/tr[@class='hilite'][8]
        /td[@class='r bld'][2]""",
                                     'date_this_year': """/html/body/div[@class='fjfe-bodywrapper']
        /div[@id='fjfe-real-body']/div[@id='fjfe-click-wrapper']/div[@class='elastic']
        /div[@id='app']/div[@id='gf-viewc']/div[@class='fjfe-content']/div[@id='incannualdiv']
        /table[@id='fs-table']/thead/tr/th[@class='rgt'][1]""",
                                     'date_last_year': """/html/body/div[@class='fjfe-bodywrapper']
        /div[@id='fjfe-real-body']/div[@id='fjfe-click-wrapper']/div[@class='elastic']
        /div[@id='app']/div[@id='gf-viewc']/div[@class='fjfe-content']/div[@id='incannualdiv']
        /table[@id='fs-table']/thead/tr/th[@class='rgt'][2]"""}
    result_dict = dict()

    multiplier = grab_multiplier(browser,
                                 const_multipler_xpath) / si_suffix_to_float(RESULT_MULTIPLIER)

    try:
        result_dict['Total Revenue Current Year'] = multiplier * \
            convert_readable_num_to_float(browser.find_element_by_xpath\
            (const_income_statements_xpath['total_revenue_this_year']).text)
    except:
        result_dict['Total Revenue Current Year'] = 'N/A'
    try:
        result_dict['Cost of Revenue Total'] = multiplier * \
            convert_readable_num_to_float(browser.find_element_by_xpath\
            (const_income_statements_xpath['cost_of_revenue']).text)
    except:
        result_dict['Cost of Revenue Total'] = 'N/A'
    try:
        result_dict['Gross Profit'] = multiplier * \
            convert_readable_num_to_float(browser.find_element_by_xpath\
            (const_income_statements_xpath['gross_profit']).text)
    except:
        result_dict['Gross Profit'] = 'N/A'
    try:
        result_dict['Selling General Admin Expenses'] = multiplier * \
            convert_readable_num_to_float(browser.find_element_by_xpath\
            (const_income_statements_xpath['sell_gen_admin_exp']).text)
    except:
        result_dict['Selling General Admin Expenses'] = 'N/A'
    try:
        result_dict['Research and Development'] = multiplier * \
            convert_readable_num_to_float(browser.find_element_by_xpath\
            (const_income_statements_xpath['r_and_d']).text)
    except:
        result_dict['Research and Development'] = 'N/A'
    try:
        result_dict['Net Income Current Year'] = multiplier * \
            convert_readable_num_to_float(browser.find_element_by_xpath\
            (const_income_statements_xpath['net_income_this_year']).text)
    except:
        result_dict['Net Income Current Year'] = 'N/A'
    try:
        result_dict['Total Revenue Last Year'] = multiplier * \
            convert_readable_num_to_float(browser.find_element_by_xpath\
            (const_income_statements_xpath['total_revenue_last_year']).text)
    except:
        result_dict['Total Revenue Last Year'] = 'N/A'
    try:
        result_dict['Net Income Last Year'] = multiplier * \
            convert_readable_num_to_float(browser.find_element_by_xpath\
            (const_income_statements_xpath['net_income_last_year']).text)
    except:
        result_dict['Net Income Last Year'] = 'N/A'
    
    try:
        date_str = browser.find_element_by_xpath\
            (const_income_statements_xpath['date_this_year']).text
        match = re.search('[0-2][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]', date_str)
        result_dict['Current Year'] = match.group(0)
    except:
        result_dict['Current Year'] = 'N/A'

    try:
        date_str = browser.find_element_by_xpath\
            (const_income_statements_xpath['date_last_year']).text
        match = re.search('[0-2][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]', date_str)
        result_dict['Previous Year'] = match.group(0)
    except:
        result_dict['Previous Year'] = 'N/A'

    return result_dict

def grab_balance_sheet_data(browser):
    """ TBA """
    const_multiplier_xpath = """/html/body/div[@class='fjfe-bodywrapper']
        /div[@id='fjfe-real-body']/div[@id='fjfe-click-wrapper']/div[@class='elastic']
        /div[@id='app']/div[@id='gf-viewc']/div[@class='fjfe-content']/div[@id='balannualdiv']
        /table[@id='fs-table']/thead/tr/th[@class='lm lft nwp']"""
    const_balance_sheet_xpaths_dict = {'cash_short_term_invest': """/html/body
        /div[@class='fjfe-bodywrapper']/div[@id='fjfe-real-body']/div[@id='fjfe-click-wrapper']
        /div[@class='elastic']/div[@id='app']/div[@id='gf-viewc']/div[@class='fjfe-content']
        /div[@id='balannualdiv']/table[@id='fs-table']/tbody/tr[3]/td[@class='r'][1]""",
                                       'total_curr_assets': """/html/body
        /div[@class='fjfe-bodywrapper']/div[@id='fjfe-real-body']/div[@id='fjfe-click-wrapper']
        /div[@class='elastic']/div[@id='app']/div[@id='gf-viewc']/div[@class='fjfe-content']
        /div[@id='balannualdiv']/table[@id='fs-table']/tbody/tr[@class='hilite'][1]
        /td[@class='r bld'][1]""",
                                       'total_assets': """/html/body/div[@class='fjfe-bodywrapper']
        /div[@id='fjfe-real-body']/div[@id='fjfe-click-wrapper']/div[@class='elastic']
        /div[@id='app']/div[@id='gf-viewc']/div[@class='fjfe-content']/div[@id='balannualdiv']
        /table[@id='fs-table']/tbody/tr[@class='hilite'][2]/td[@class='r bld'][1]""",
                                       'total_curr_liab': """/html/body
        /div[@class='fjfe-bodywrapper']/div[@id='fjfe-real-body']/div[@id='fjfe-click-wrapper']
        /div[@class='elastic']/div[@id='app']/div[@id='gf-viewc']/div[@class='fjfe-content']
        /div[@id='balannualdiv']/table[@id='fs-table']/tbody/tr[@class='hilite'][3]
        /td[@class='r bld'][1]""",
                                       'total_debt': """/html/body/div[@class='fjfe-bodywrapper']
        /div[@id='fjfe-real-body']/div[@id='fjfe-click-wrapper']/div[@class='elastic']
        /div[@id='app']/div[@id='gf-viewc']/div[@class='fjfe-content']/div[@id='balannualdiv']
        /table[@id='fs-table']/tbody/tr[@class='hilite'][5]/td[@class='r bld'][1]""",
                                       'retained_earn': """/html/body/div[@class='fjfe-bodywrapper']
        /div[@id='fjfe-real-body']/div[@id='fjfe-click-wrapper']/div[@class='elastic']
        /div[@id='app']/div[@id='gf-viewc']/div[@class='fjfe-content']/div[@id='balannualdiv']
        /table[@id='fs-table']/tbody/tr[36]/td[@class='r'][1]""",
                                       'total_liab_s_equity': """/html/body
        /div[@class='fjfe-bodywrapper']/div[@id='fjfe-real-body']/div[@id='fjfe-click-wrapper']
        /div[@class='elastic']/div[@id='app']/div[@id='gf-viewc']/div[@class='fjfe-content']
        /div[@id='balannualdiv']/table[@id='fs-table']/tbody/tr[@class='hilite'][8]
        /td[@class='r bld'][1]"""}
    result_dict = dict()
    multiplier = grab_multiplier(browser,
                                 const_multiplier_xpath) / si_suffix_to_float(RESULT_MULTIPLIER)

    try:
        result_dict['Cash and Short Term Investments'] = multiplier * \
            convert_readable_num_to_float(browser.find_element_by_xpath\
            (const_balance_sheet_xpaths_dict['cash_short_term_invest']).text)
    except:
        result_dict['Cash and Short Term Investments'] = 'N/A'
    try:
        result_dict['Total Current Assets'] = multiplier * \
            convert_readable_num_to_float(browser.find_element_by_xpath\
            (const_balance_sheet_xpaths_dict['total_curr_assets']).text)
    except:
        result_dict['Total Current Assets'] = 'N/A'
    try:
        result_dict['Total Assets'] = multiplier * \
            convert_readable_num_to_float(browser.find_element_by_xpath\
            (const_balance_sheet_xpaths_dict['total_assets']).text)
    except:
        result_dict['Total Assets'] = 'N/A'
    try:
        result_dict['Total Current Liabilities'] = multiplier * \
            convert_readable_num_to_float(browser.find_element_by_xpath\
            (const_balance_sheet_xpaths_dict['total_curr_liab']).text)
    except:
        result_dict['Total Current Liabilities'] = 'N/A'
    try:
        result_dict['Total Debt'] = multiplier * \
            convert_readable_num_to_float(browser.find_element_by_xpath\
            (const_balance_sheet_xpaths_dict['total_debt']).text)
    except:
        result_dict['Total Debt'] = 'N/A'
    try:
        result_dict['Retained Earnings'] = multiplier * \
            convert_readable_num_to_float(browser.find_element_by_xpath\
            (const_balance_sheet_xpaths_dict['retained_earn']).text)
    except:
        result_dict['Retained Earnings'] = 'N/A'
    try:
        result_dict['Total Liabilities and Shareholders Equity'] = multiplier * \
            convert_readable_num_to_float(browser.find_element_by_xpath\
            (const_balance_sheet_xpaths_dict['total_liab_s_equity']).text)
    except:
        result_dict['Total Liabilities and Shareholders Equity'] = 'N/A'

    return result_dict
def convert_readable_num_to_float(num_as_string, desired_base_unit=None):
    """ TBA """
    stripped_string = num_as_string.replace(',', '')
    if stripped_string == '-':
        stripped_string = '0'
    if desired_base_unit:
        desired_multiplier = si_suffix_to_float(desired_base_unit)
    else:
        desired_multiplier = 1.0

    current_multiplier = si_suffix_to_float(stripped_string[-1])
    if desired_multiplier == 1.0:
        current_number = float(stripped_string)*current_multiplier
    else:
        current_number = float(stripped_string[:-1])*current_multiplier

    return current_number/desired_multiplier

def si_suffix_to_float(suffix_string):
    """TBA"""
    si_suffix_to_float_dict = {'K':1000.0, 'M':1000000.0,
                               'B':1000000000.0, 'T':1000000000000.0
                              }
    if suffix_string in si_suffix_to_float_dict:
        return si_suffix_to_float_dict[suffix_string]
    else:
        return 1.0

def grab_financials_row_data(browser, xpath_string):
    """Returns a row from finance website"""
    raw_output_list = browser.find_elements_by_xpath(xpath_string)
    output_list = list()

    for item in raw_output_list:
        output_list.append(item.text)

    return output_list
def grab_multiplier(browser, xpath_string):
    """Returns multiplication factor for financials info, e.g. usually Millions"""
    raw_string = browser.find_element_by_xpath(xpath_string).text
    if 'million' in raw_string.lower():
        return 1000000.0
    elif 'thousand' in raw_string.lower():
        return 1000.0
    else:
        return 1.0
def scrape(stock_symbol):
    """Visits website to scrape data on stock_symbol in exchange."""
    ## SELENIUM PATH CONSTANTS
    const_page_xpaths_dict = {'income_statements' : """/html/body/div[@class='fjfe-bodywrapper']
        /div[@id='fjfe-real-body']/div[@id='fjfe-click-wrapper']/div[@class='elastic']
        /div[@id='app']/div[@id='gf-viewc']/div[@class='fjfe-content']/div[@id='fs-type-tabs']
        /div[@id=':0']/a[@class='t']/b[@class='t']/b[@class='t']""",
                              'balance_sheet' : """/html/body/div[@class='fjfe-bodywrapper']
        /div[@id='fjfe-real-body']/div[@id='fjfe-click-wrapper']/div[@class='elastic']
        /div[@id='app']/div[@id='gf-viewc']/div[@class='fjfe-content']/div[@id='fs-type-tabs']
        /div[@id=':1']""",
                              'annual_data' : """/html/body/div[@class='fjfe-bodywrapper']
        /div[@id='fjfe-real-body']/div[@id='fjfe-click-wrapper']/div[@class='elastic']
        /div[@id='app']/div[@id='gf-viewc']/div[@class='fjfe-content']
        /div[@class='gf-table-control-plain']/div[@class='g-section g-tpl-67-33 g-split']
        /div[@class='g-unit g-first']/a[@id='annual']""",
                              'annual_data_alt' : """/html/body/div[@class='fjfe-bodywrapper']
        /div[@id='fjfe-real-body']/div[@id='fjfe-click-wrapper']/div[@class='elastic']
        /div[@id='app']/div[@id='gf-viewc']/div[@class='fjfe-content']
        /div[@class='gf-table-control-plain']/div[@class='gf-control']/a[@id='annual']"""}

    browser = initialize_browser()
    browser_load_url(browser, return_base_url(stock_symbol, ''))

    stock_result_dict = dict()
    stock_result_dict.update(grab_summary_data(browser, stock_symbol))

    browser_load_url(browser, return_finance_url(stock_symbol, stock_result_dict['Exchange']))

    try:
        browser_xpath_click(browser, const_page_xpaths_dict['income_statements'])
    except:
        print "Could not load Income Statement"
    try:
        browser_xpath_click(browser, const_page_xpaths_dict['annual_data'])
    except:
        browser_xpath_click(browser, const_page_xpaths_dict['annual_data_alt'])
        print "Did not work, clicking on alternate Annual Data"

    stock_result_dict.update(grab_income_statement_data(browser))
    try:
        browser_xpath_click(browser, const_page_xpaths_dict['balance_sheet'])
    except:
        print "Could not load Balance Sheet"
    stock_result_dict.update(grab_balance_sheet_data(browser))
    stock_result_dict['Other'] = stock_result_dict['Gross Profit'] - \
                                    stock_result_dict['Selling General Admin Expenses'] - \
                                    stock_result_dict['Research and Development'] - \
                                    stock_result_dict['Net Income Current Year']

    stock_result_dict['Other Assets'] = stock_result_dict['Total Current Assets'] - \
                                            stock_result_dict['Cash and Short Term Investments']
    stock_result_dict['Fixed Assets'] = stock_result_dict['Total Assets'] - \
                                            stock_result_dict['Total Current Assets']
    stock_result_dict['Share Equity'] = stock_result_dict['Retained Earnings'] - \
                                            stock_result_dict['Total Debt']
    stock_result_dict['Long Term Liabilities'] = stock_result_dict['Total Liabilities'] - \
                                            stock_result_dict['Total Current Liabilities']

    
    for key, elem in stock_result_dict.items():
        print key, elem
    browser_quit(browser)
    return stock_result_dict

def scrape_and_write_to_file(stock_symbol, results_filename, results_dir_name):
    """Main function to scrape and analyze, split up into scrape and analyze steps"""
    scrape(stock_symbol)
    print "Saving to: ", results_filename

    if not os.path.exists('{}'.format(results_dir_name)):
        os.makedirs(results_dir_name)
    results_fullpath = '{}/{}'.format(results_dir_name, results_filename)
    
    result_order_list=['Stock Name','s','','','','','']
    #with open(results_fullpath, 'w+') as results_file:
        
                
    





def process_file(work_filename, data_dir_name, logs_dir_name, results_dir_name):
    """TBA"""
    print "File: ", work_filename
    if not os.path.exists('{}'.format(logs_dir_name)):
        os.makedirs(logs_dir_name)

    log_fullpath = '{}/log_{}.txt'.format(logs_dir_name, work_filename)
    work_fullpath = '{}/{}'.format(data_dir_name, work_filename)
    results_filename= 'result_{}'.format(work_filename)
    if os.path.exists(log_fullpath):
        with open(log_fullpath, 'r') as log_file:
            try:
                print " resuming work"
                row_to_work_on = int(log_file.readline())
            except ValueError:
                row_to_work_on = 1
    else:
        print " starting new work"
        row_to_work_on = 1
    with open(work_fullpath, 'rU') as work_file:
        csv_reader = csv.reader(work_file, delimiter='\t', quotechar='|')
        row_count = sum(1 for row in csv_reader)

    if row_to_work_on >= 0:
        with open(work_fullpath, 'rU') as work_file:
            csv_reader = csv.reader(work_file, delimiter='\t', quotechar="'")
            csv_reader.next() #skip header
            if row_to_work_on < row_count:
                for i in xrange(row_to_work_on-1): # skip everything right before
                    print i
                    print "  skipping {}".format(csv_reader.next()[0])
                    csv_reader.next()

                for row in csv_reader:
                    print "  working on", row[0]
                    scrape_and_write_to_file(row[0], results_filename, results_dir_name)
                    row_to_work_on += 1
                    with open(log_fullpath, 'w') as log_file:
                        log_file.writelines('{}'.format(row_to_work_on))
            else:
                row_to_work_on = -1
                print "Completed File"
                with open(log_fullpath, 'w') as log_file:
                    log_file.writelines('{}'.format(row_to_work_on))
    else:
        print "File already completed"

def main():
    """Main function to call scraper"""
    stocks_tse_string = ''
    stocks_tse_string = ''
    stocks_tse_list = stocks_tse_string.split()
    stocks_nas_string = 'AAPL ATEN' # debug using the following stocks) RL CVX LL SAM EL NWL COR ALB
    #stocks_nas_string = 'RL CVX LL SAM EL NWL COR ALB'
    stocks_nas_list = stocks_nas_string.split()
    stocks_nys_string = ''
    #stocks_nys_string = 'XOM'
    stocks_nys_list = stocks_nys_string.split()

    ca_errors_string = 'Could not analyze these CA stocks: '
    us_errors_string = 'Could not analyze these US stocks: '
    for item in stocks_tse_list:
        try:
            scrape_and_write_to_file(item)
        except:
            ca_errors_string += item + ' '
        print ''

    for item in stocks_nas_list:
        #try:
        #    scrape_and_write_to_file(item)
        #except:
        #    us_errors_string += item + ' '
        scrape_and_write_to_file(item)
        print ''

    for item in stocks_nys_list:
        try:
            scrape_and_write_to_file(item)
        except:
            us_errors_string += item + ' '
        print ''

    print ca_errors_string
    print us_errors_string

def main2():
    """For testing only"""
    process_file('hello.csv', 'data', 'logs', 'results')



main2()
