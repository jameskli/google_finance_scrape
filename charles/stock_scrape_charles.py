#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Module scrapes data from Google Finance"""

import re
import datetime as datetime
from random import randint
import time
import csv
import os
import sys
from selenium import webdriver

## GLOBAL CONSTANTS
NASDAQ = "NASDAQ"
NYSE = "NYSE"
TSE = "TSE"
RESULT_MULTIPLIER = "K"

def return_base_url(stock_symbol, exchange=None):
    """Return string of the URL to visit given a stock symbol and stock exchange
    Stock exchange can be blank
    """
    ## URL CONSTANTS
    const_base_url = 'https://www.google.com/finance?q='

    if not exchange:
        return const_base_url + stock_symbol
    else:
        return const_base_url + exchange + '%3A'+stock_symbol

def return_finance_url(stock_symbol, exchange):
    """Returns the path to the financials page from the main stock listing page,
    e.g. on Google Finance"""
    const_financial_url_path = '&fstype=ii'
    return return_base_url(stock_symbol, exchange) + const_financial_url_path
def initialize_browser():
    """Initialize browser, also includes using an adblocker, but I dont think it quite works"""
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
    """Retrieves basic information from a stock's Summary page , eg
    stock name, symbol, current PE ratio, market cap, employees
    """
    const_sum_xpath_base = """/html/body/div[@class='fjfe-bodywrapper']
        /div[@id='fjfe-real-body']/div[@id='fjfe-click-wrapper']"""
    const_summary_xpaths_dict = {'stock_name' : """{}/div[@id='appbar']/div[@class='elastic']
                                    /div[@class='appbar-center']
                                    /div[@class='appbar-snippet-primary']
                                    /span""".format(const_sum_xpath_base),
                                 'stock_symbol' : """{}/div[@id='appbar']/div[@class='elastic']
                                    /div[@class='appbar-center']
                                    /div[@class='appbar-snippet-secondary']
                                    /span""".format(const_sum_xpath_base),
                                 'current_pe' : """{}/div[@class='elastic']/div[@id='app']
                                    /div[@id='gf-viewc']/div[@class='fjfe-content']
                                    /div[@class='g-wrap']/div[@class='g-section g-tpl-right-1']
                                    /div[@class='g-unit']/div[@id='market-data-div']
                                    /div[@class='snap-panel-and-plusone']/div[@class='snap-panel']
                                    /table[@class='snap-data'][1]/tbody/tr[6]
                                    /td[@class='val']""".format(const_sum_xpath_base),
                                 'employees' : """{}/div[@class='elastic']/div[@id='app']
                                    /div[@id='gf-viewc']/div[@class='fjfe-content']
                                    /div[@class='g-wrap']
                                    /div[@class='g-section g-tpl-right-1 sfe-break-top-5']
                                    /div[@class='g-unit g-first']/div[@class='g-c']
                                    /div[@class='sfe-section'][1]/table[@class='quotes rgt nwp']
                                    /tbody/tr[6]
                                    /td[@class='period'][1]""".format(const_sum_xpath_base),
                                 'market_cap' : """{}/div[@class='elastic']/div[@id='app']
                                    /div[@id='gf-viewc']/div[@class='fjfe-content']
                                    /div[@class='g-wrap']/div[@class='g-section g-tpl-right-1']
                                    /div[@class='g-unit']/div[@id='market-data-div']
                                    /div[@class='snap-panel-and-plusone']/div[@class='snap-panel']
                                    /table[@class='snap-data'][1]/tbody/tr[5]
                                    /td[@class='val']""".format(const_sum_xpath_base)
                                }

    result_dict = dict()
    try:
        retrieved_stock_symbol = browser.find_element_by_xpath\
            (const_summary_xpaths_dict['stock_symbol']).text.strip('()').split(':')[1]
        result_dict['Stock Symbol'] = retrieved_stock_symbol
    except:
        result_dict['Stock Symbol'] = 'N/A'

    if result_dict['Stock Symbol'] != stock_symbol:
        print "    Warning 1, {} is not in NASDAQ, retry with NYSE".format(stock_symbol)
        try:
            browser_load_url(browser, return_base_url(stock_symbol, NYSE))
            retrieved_stock_symbol = browser.find_element_by_xpath\
                (const_summary_xpaths_dict['stock_symbol']).text.strip('()').split(':')[1]
            result_dict['Stock Symbol'] = retrieved_stock_symbol
        except:
            result_dict['Stock Symbol'] = 'N/A'

    if result_dict['Stock Symbol'] != stock_symbol:
        print "    Warning 2, {} not in NYSE, retry with empty.".format(stock_symbol)
        try:
            browser_load_url(browser, return_base_url(stock_symbol))
            retrieved_stock_symbol = browser.find_element_by_xpath\
                (const_summary_xpaths_dict['stock_symbol']).text.strip('()').split(':')[1]
            result_dict['Stock Symbol'] = retrieved_stock_symbol
        except:
            result_dict['Stock Symbol'] = 'N/A'
    if result_dict['Stock Symbol'] != stock_symbol:
        print "    Still could not find {}, giving up".format(stock_symbol)
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

    # different columns end with different Xpaths
    const_bal_xpath_y1 = "'][1]"
    const_bal_xpath_ylast = " rm']"
    const_bal_xpath_y2 = "'][2]"

    const_inc_xpath_year = """/html/body/div[@class='fjfe-bodywrapper']/div[@id='fjfe-real-body']
        /div[@id='fjfe-click-wrapper']/div[@class='elastic']/div[@id='app']/div[@id='gf-viewc']
        /div[@class='fjfe-content']/div[@id='incannualdiv']/table[@id='fs-table']/thead/tr/th"""
    
    # num years to handle which columns refer to this year vs previous year etc.
    num_years = len(browser.find_elements_by_xpath(const_inc_xpath_year)) - 1

    if num_years == 1:
        print "      Warning, only 1 year of data available."
        y1_suffix = const_bal_xpath_ylast
        y2_suffix = const_bal_xpath_ylast
    elif num_years == 2:
        print "      Warning, only 2 years of data available."
        y1_suffix = const_bal_xpath_y1
        y2_suffix = const_bal_xpath_ylast
    else:
        y1_suffix = const_bal_xpath_y1
        y2_suffix = const_bal_xpath_y2

    const_inc_xpath_base = """/html/body/div[@class='fjfe-bodywrapper']/div[@id='fjfe-real-body']
        /div[@id='fjfe-click-wrapper']/div[@class='elastic']/div[@id='app']/div[@id='gf-viewc']
        /div[@class='fjfe-content']/div[@id='incannualdiv']/table[@id='fs-table']"""

    const_multipler_xpath = """{}/thead/tr/th[@class='lm lft nwp']""".format(const_inc_xpath_base)

    const_income_statements_xpath = {'total_revenue_this_year' : """{}/tbody/tr[@class='hilite'][1]
                                            /td[@class='r bld{}""".format(const_inc_xpath_base,
                                                                          y1_suffix),
                                     'cost_of_revenue': """{}/tbody/tr[4]
                                            /td[@class='r{}""".format(const_inc_xpath_base,
                                                                      y1_suffix),
                                     'gross_profit' : """{}/tbody/tr[@class='hilite'][2]
                                            /td[@class='r bld{}""".format(const_inc_xpath_base,
                                                                          y1_suffix),
                                     'sell_gen_admin_exp' : """{}/tbody/tr[6]
                                            /td[@class='r{}""".format(const_inc_xpath_base,
                                                                      y1_suffix),
                                     'r_and_d': """{}/tbody/tr[7]
                                            /td[@class='r{}""".format(const_inc_xpath_base,
                                                                      y1_suffix),
                                     'net_income_this_year' : """{}/tbody/tr[@class='hilite'][8]
                                            /td[@class='r bld{}""".format(const_inc_xpath_base,
                                                                          y1_suffix),
                                     'total_revenue_last_year' : """{}/tbody/tr[@class='hilite'][1]
                                            /td[@class='r bld{}""".format(const_inc_xpath_base,
                                                                          y2_suffix),
                                     'net_income_last_year' : """{}/tbody/tr[@class='hilite'][8]
                                            /td[@class='r bld{}""".format(const_inc_xpath_base,
                                                                          y2_suffix),
                                     'date_this_year' : """{}/thead/tr
                                            /th[@class='rgt{}""".format(const_inc_xpath_base,
                                                                        y1_suffix),
                                     'date_last_year' : """{}/thead/tr
                                            /th[@class='rgt{}""".format(const_inc_xpath_base,
                                                                        y2_suffix)
                                    }
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
        if num_years == 1:
            result_dict['Total Revenue Last Year'] = 'N/A'
        else:
            result_dict['Total Revenue Last Year'] = multiplier * \
                convert_readable_num_to_float(browser.find_element_by_xpath\
                (const_income_statements_xpath['total_revenue_last_year']).text)
    except:
        result_dict['Total Revenue Last Year'] = 'N/A'
    try:
        if num_years == 1:
            result_dict['Net Income Last Year'] = 'N/A'
        else:
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
        if num_years == 1:
            result_dict['Previous Year'] = 'N/A'
        else:
            date_str = browser.find_element_by_xpath\
                (const_income_statements_xpath['date_last_year']).text
            match = re.search('[0-2][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]', date_str)
            result_dict['Previous Year'] = match.group(0)
    except:
        result_dict['Previous Year'] = 'N/A'

    return result_dict

def grab_balance_sheet_data(browser):
    """ Extract data from Annual Balance Sheet page of a Stock """

    const_bal_xpath_y1 = "'][1]"
    const_bal_xpath_ylast = " rm']"

    const_bal_xpath_year = """/html/body/div[@class='fjfe-bodywrapper']/div[@id='fjfe-real-body']
        /div[@id='fjfe-click-wrapper']/div[@class='elastic']/div[@id='app']/div[@id='gf-viewc']
        /div[@class='fjfe-content']/div[@id='balannualdiv']/table[@id='fs-table']/thead/tr/th"""

    # num_years to handle which column refers to this year vs previous year etc.
    num_years = len(browser.find_elements_by_xpath(const_bal_xpath_year)) - 1

    if num_years > 2:
        y1_suffix = const_bal_xpath_y1
    else:
        y1_suffix = const_bal_xpath_ylast

    const_bal_xpath_base = """/html/body/div[@class='fjfe-bodywrapper']/div[@id='fjfe-real-body']
        /div[@id='fjfe-click-wrapper']/div[@class='elastic']/div[@id='app']/div[@id='gf-viewc']
        /div[@class='fjfe-content']/div[@id='balannualdiv']/table[@id='fs-table']"""

    const_multiplier_xpath = """{}/thead/tr/th[@class='lm lft nwp']""".format(const_bal_xpath_base)
    const_balance_sheet_xpaths_dict = {'cash_short_term_invest' : """{}/tbody/tr[3]
                                            /td[@class='r{}""".format(const_bal_xpath_base,
                                                                      y1_suffix),
                                       'total_curr_assets' : """{}/tbody/tr[@class='hilite'][1]
                                            /td[@class='r bld{}""".format(const_bal_xpath_base,
                                                                          y1_suffix),
                                       'total_assets': """{}/tbody/tr[@class='hilite'][2]
                                            /td[@class='r bld{}""".format(const_bal_xpath_base,
                                                                          y1_suffix),
                                       'total_curr_liab' : """{}/tbody/tr[@class='hilite'][3]
                                            /td[@class='r bld{}""".format(const_bal_xpath_base,
                                                                          y1_suffix),
                                       'total_debt' : """{}/tbody/tr[@class='hilite'][5]
                                            /td[@class='r bld{}""".format(const_bal_xpath_base,
                                                                          y1_suffix),
                                       'retained_earn' : """{}/tbody/tr[36]
                                            /td[@class='r{}""".format(const_bal_xpath_base,
                                                                      y1_suffix),
                                       'total_liab_s_equity' : """{}/tbody/tr[@class='hilite'][8]
                                            /td[@class='r bld{}""".format(const_bal_xpath_base,
                                                                          y1_suffix)
                                      }
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
    """ converts dollar numbers as str into floats with a multiplication factor,
    eg 1,000,000 expressed in thousands ('K') becomes 1000.0 """

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

def grab_multiplier(browser, xpath_string):
    """Read the multiplication factor for financials info, e.g. usually Millions, returns float"""
    raw_string = browser.find_element_by_xpath(xpath_string).text
    if 'million' in raw_string.lower():
        return 1000000.0
    elif 'thousand' in raw_string.lower():
        return 1000.0
    else:
        return 1.0
def clean_up_stock_symbol(input_stock_symbol):
    """Handles stock symbols with whitespace, but also, those that use hats ^
    to distinguish stock_classes eg DD^B for B class DD shares, should be DD-B"""
    return input_stock_symbol.strip().replace('^', '-')
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
    const_page_not_found_evidence = """/html/body/div[@class='fjfe-bodywrapper']
    /div[@id='fjfe-real-body']/div[@id='fjfe-click-wrapper']/div[@class='elastic']
    /div[@id='app']/div[@id='gf-viewc']/div[@class='fjfe-content']/div[3]"""
    browser = initialize_browser()
    browser_load_url(browser, return_base_url(stock_symbol, NASDAQ)) # assume NASDAQ

    stock_result_dict = dict()
    stock_result_dict.update(grab_summary_data(browser, stock_symbol))
    loaded_financial_data = True
    loaded_income_statement = True
    loaded_balance_sheet = True
    try:
        browser_load_url(browser, return_finance_url(stock_symbol, stock_result_dict['Exchange']))
    except:
        print "Could not load Financial Data"
        loaded_financial_data = False
        loaded_income_statement = False
        loaded_balance_sheet = False
    try:
        browser_xpath_click(browser, const_page_xpaths_dict['income_statements'])
    except:
        print "Could not load Income Statement"
        loaded_income_statement = False
    try:
        if loaded_income_statement:
            browser_xpath_click(browser, const_page_xpaths_dict['annual_data'])
    except:
        if loaded_income_statement:
            browser_xpath_click(browser, const_page_xpaths_dict['annual_data_alt'])
            print "Did not work, clicking on alternate Annual Data"
    if loaded_income_statement:
        stock_result_dict.update(grab_income_statement_data(browser))
    try:
        browser_xpath_click(browser, const_page_xpaths_dict['balance_sheet'])
    except:
        print "Could not load Balance Sheet"
        loaded_balance_sheet = False
    if loaded_balance_sheet:
        stock_result_dict.update(grab_balance_sheet_data(browser))

    if loaded_income_statement:
        stock_result_dict['Other'] = stock_result_dict['Gross Profit'] - \
                                     stock_result_dict['Selling General Admin Expenses'] - \
                                     stock_result_dict['Research and Development'] - \
                                     stock_result_dict['Net Income Current Year']
    else:
        stock_result_dict['Other'] = 'N/A'

    if loaded_balance_sheet:
        stock_result_dict['Other Assets'] = stock_result_dict['Total Current Assets'] - \
                                            stock_result_dict['Cash and Short Term Investments']
        stock_result_dict['Fixed Assets'] = stock_result_dict['Total Assets'] - \
                                            stock_result_dict['Total Current Assets']
        stock_result_dict['Share Equity'] = stock_result_dict['Retained Earnings'] - \
                                            stock_result_dict['Total Debt']
        stock_result_dict['Long Term Liabilities'] = stock_result_dict['Total Debt'] - \
                                            stock_result_dict['Total Current Liabilities']
    else:
        stock_result_dict['Other Assets'] = 'N/A'
        stock_result_dict['Fixed Assets'] = 'N/A'
        stock_result_dict['Share Equity'] = 'N/A'
        stock_result_dict['Long Term Liabilities'] = 'N/A'

    browser_quit(browser)
    return stock_result_dict

def scrape_and_write_to_file(stock_symbol, results_filename, results_dir_name):
    """Main function to scrape and analyze, split up into scrape and analyze steps"""

    result_order_list = ['Stock Symbol', 'Exchange', 'Stock Name', 'Current Year', 'Previous Year',
                         'Total Revenue Current Year', 'Cost of Revenue Total', 'Gross Profit',
                         'Selling General Admin Expenses', 'Research and Development', 'Other',
                         'Net Income Current Year', 'Total Revenue Last Year',
                         'Net Income Last Year', 'Cash and Short Term Investments', 'Other Assets',
                         'Total Current Assets', 'Fixed Assets', 'Total Assets',
                         'Total Current Liabilities', 'Long Term Liabilities', 'Total Debt',
                         'Share Equity', 'Retained Earnings',
                         'Total Liabilities and Shareholders Equity', 'Employees', 'Market Cap',
                         'Current PE Ratio']
    stock_results_dict = {item: 'N/A' for item in result_order_list}

    stock_results_dict.update(scrape(clean_up_stock_symbol(stock_symbol)))

    if not os.path.exists('{}'.format(results_dir_name)):
        os.makedirs(results_dir_name)
    results_fullpath = '{}/{}'.format(results_dir_name, results_filename)

    if not os.path.exists(results_fullpath):
        print "Saving in", results_fullpath
        with open(results_fullpath, 'w') as results_file:
            csv_writer = csv.writer(results_file, quoting=csv.QUOTE_ALL)
            csv_writer.writerow(result_order_list)

    with open(results_fullpath, 'a+') as results_file:
        csv_writer = csv.writer(results_file, quoting=csv.QUOTE_ALL)
        csv_writer.writerow([stock_results_dict[item] for item in result_order_list])

def process_dir(data_dir_name, logs_dir_name, results_dir_name):
    """Goes through data needs, the directory names for data, where to put results, where to log 
    output"""

    print "Begin batch processing"

    if not os.path.exists('{}'.format(logs_dir_name)):
        os.makedirs(logs_dir_name)

    if not os.path.exists('{}'.format(results_dir_name)):
        os.makedirs(results_dir_name)

    master_log_fullpath = '{}/log_master.txt'.format(logs_dir_name)

    file_list = [f for f in os.listdir(data_dir_name) if f.endswith(".csv") and\
                 os.path.isfile(os.path.join(data_dir_name, f))]

    with open(master_log_fullpath, 'w') as master_log:
        master_log.writelines('{} Begin batch processing\n'.format(datetime.datetime.now()))
    sys.stdout.flush()
    for item in file_list:
        try:
            process_file(item, data_dir_name, logs_dir_name, results_dir_name)
            with open(master_log_fullpath, 'a+') as master_log:
                master_log.writelines('{} finished: {}\n'.format(datetime.datetime.now(), item))
        except IOError:
            with open(master_log_fullpath, 'a+') as master_log:
                master_log.writelines('{} could not process: {}\n'.\
                    format(datetime.datetime.now(), item))
        sys.stdout.flush() # forces an output to std
    print "Batch processing ended"
    with open(master_log_fullpath, 'a+') as master_log:
        master_log.writelines('{} Batch processing ended\n'.format(datetime.datetime.now()))
    sys.stdout.flush()
def process_file(work_filename, data_dir_name, logs_dir_name, results_dir_name):
    """works on work_filename, requires where to grab data, write results and logs to"""
    
    print "File: ", work_filename
    if not os.path.exists('{}'.format(logs_dir_name)):
        os.makedirs(logs_dir_name)

    log_fullpath = '{}/log_{}.txt'.format(logs_dir_name, work_filename)
    work_fullpath = '{}/{}'.format(data_dir_name, work_filename)
    results_filename = 'result_{}'.format(work_filename)
    if os.path.exists(log_fullpath):
        with open(log_fullpath, 'r') as log_file:
            try:
                print " Resuming work"
                row_to_work_on = int(log_file.readline())
            except ValueError:
                row_to_work_on = 1
    else:
        print " Creating", log_fullpath
        row_to_work_on = 1
    with open(work_fullpath, 'rU') as work_file:
        csv_reader = csv.reader(work_file, delimiter=',', quotechar='"')
        #csv_reader = csv.reader(work_file, delimiter='\t', quotechar="'")
        # I need to figure out so as not to keep swapping betwee tab and comma delimited
        row_count = sum(1 for row in csv_reader)

    if row_to_work_on >= 0:
        with open(work_fullpath, 'rU') as work_file:
            csv_reader = csv.reader(work_file, delimiter=',', quotechar='"')
            #csv_reader = csv.reader(work_file, delimiter='\t', quotechar="'")
            # I need to figure out so as not to keep swapping betwee tab and comma delimited
            csv_reader.next() #skip header
            if row_to_work_on < row_count:
                for i in xrange(row_to_work_on - 1): # skip everything right before
                    print "  skipping {}".format(csv_reader.next()[0])

                for row in csv_reader:
                    print "  {}. {}".format(row_to_work_on, row[0])
                    scrape_and_write_to_file(row[0], results_filename, results_dir_name)
                    row_to_work_on += 1
                    with open(log_fullpath, 'w') as log_file:
                        log_file.writelines('{}'.format(row_to_work_on))
                    sys.stdout.flush()
            else:
                row_to_work_on = -1
                print "Completed File"
                with open(log_fullpath, 'w') as log_file:
                    log_file.writelines('{}'.format(row_to_work_on))
    else:
        print "File already completed"

def main():
    """Main function to call scraper"""
    process_dir('data', 'logs', 'results')

main()
