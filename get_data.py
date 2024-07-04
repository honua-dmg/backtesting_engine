from selenium import webdriver
from selenium.webdriver.common.by import By
from tkinter import Tk
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup as bs
import requests

import os
failed = []


def get_scanclause(url:str)->str:


    """
    Args:
        url: url of link
    Returns:
        string containing scan clause
    Description:
        uses selenium and tkinter to scrape the scan clause from the link


        steps:
        1. initialise a driver
        2. get url via driver
        3. find the copy button (next to the 'stock passes ... in ... segment')
        4. click the button to copy scan clause to clipboard
        5. access clipboard via tkinter
        6. copy clause
        7. destroy tkinter screen to avoid build up
    """


    # 1
    driver = webdriver.Edge()              
    # 2        
    driver.get(url)              
    #3                
    element = driver.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[2]/div/div/div/div[2]/div/div[2]/div[1]/div/div/i')
    #4
    element.click()
    #5
    a = Tk()
    #6
    clipboard = a.clipboard_get()
    #7
    a.destroy()
    return clipboard




def clause_parser(clause):


    """
    Args:
        scan_clause : the scan clause of the given link
                    (contains data about the conditions imposed for the backtest process)


    Returns:
        final_clause: updated scan clause with only day parameters
   
   steps:
        1. split clause by spaces
        2. check for kewords in frames or framesly
            a. if in framesly, replace with Daily
            b. if in frames, replace with day or days depending on preceeding number (if number = 1, `day`, or else `days`)
        3. return joined clause
    """
    #1
    split_clause = clause.split(' ')
    frames = ['minute','hour','week','weeks','month','months','quarter','year','years']
    framesly = ['Weekly','Monthly','Quaterly','Yearly']
    for i in range(len(split_clause)):
        #2a
        if split_clause[i] in framesly:
            split_clause[i] = 'Daily'
        #2b
        elif split_clause[i] in frames:
            if split_clause[i-1] == '1':
                split_clause[i] = 'day'
            else:
                split_clause[i] = 'days'
    #3
    return ' '.join(split_clause)




def results(url:str):
    """
    Args:
        url: the url of the backtest link
        scan_clause: the scan clauseo f the given data link
        path: a path to save the dataframe in csv format to
       
    Returns:
        csv file of backtest results


    Description:
        sends a post request with the scan clause to recieve the backtest results
        parses json results received into a pandas dataframe


        steps:
       
        1. open a requests session
        2. get csrf token via a get request to the url
        3. send a post request with the csrf token and scan clause as payload to get data
        4. parsing the data
        5. if a path parameter is specified, the parsed data (in a dataframe), is converted to a csv file and stored at the specified path.


    """
    scan_clause = clause_parser(get_scanclause(url))
    # 1
    with requests.session() as s:
        condition = {"scan_clause": scan_clause}
        #2
        r_data = s.get(url)
        soup = bs(r_data.content,"lxml")                            # converting source code into a soup object
        meta = soup.find("meta",{"name":"csrf-token"})['content']   # serching for the csrf-token meta tag; specifically getting it's content
        print(meta)
        header = {'x-csrf-token':meta}
        # 3
        data = s.post("https://chartink.com/backtest/process",headers=header,data=condition).json()




    # parsing the data into a prettier format:
    #4
    date = data['metaData'][0]['tradeTimes']
    stonks = data['aggregatedStockList']
    finale = []
    stonks_in_date = []


    for j in range(0,len(stonks[0]),3):
        stonks_in_date.append(stonks[0][j])
    finale.append({"date":date[0] ,'stocks' :stonks_in_date})
    for i in range(1,len(date)-1):
        stonks_in_date = []
        for j in range(0,len(stonks[i]),3):
            stonks_in_date.append(stonks[i][j])
        finale.append({"date":date[i] ,'stocks' :stonks_in_date})
    return pd.DataFrame(finale)




def save_files(urls,start=0,stop=None):
    if stop == None:
        stop = len(urls)




    with open('./data/failed.csv','a+') as failed:
        if os.path.getsize('./data/failed.csv') ==0:
            failed.write('url,failure\n')


    with open('./data/masterfile.csv', 'a+') as f:
        if os.path.getsize('./data/masterfile.csv') ==0:
            f.write('url,loc\n')


        try:
            existing_urls = pd.read_csv('./data/masterfile.csv')['url'].to_list()
            print(len(existing_urls))
        except Exception:
            pass
        for i in range(len(urls)):
            file_name = urls[i].split('/')[-1]
            if urls[i] in existing_urls:
                continue
            if 'fundamental' in ' '.join(file_name.split('-')):
                print(f'{file_name} with the url: {urls[i]} failed due to it being a fundamental test')
                with open('./data/failed.csv','a+') as failed:
                    failed.write(f'{urls[i]},fundamental\n')
                print('*'*80)                    
            try:
                data = results(urls[i])
                file_path = './data/'+file_name +'.csv'
                f.write(f'{urls[i]},{file_name}.csv\n')
                data.to_csv(file_path)
                print(f'{file_name} saved successfully')
                print('*'*80)
            except Exception as e:
                print(f'{file_name} with the url: {urls[i]} failed due to {e}')
                with open('./data/failed.csv','a+') as failed:
                    failed.write(f'{urls[i]},{e}\n')
                print('*'*80)











