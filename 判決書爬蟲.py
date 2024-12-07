import requests
from bs4 import BeautifulSoup 
import re
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.select import Select
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

driver= webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get('https://judgment.judicial.gov.tw/FJUD/Default_AD.aspx')
wait = WebDriverWait(driver, 10)
Court = wait.until(EC.presence_of_element_located((By.ID, "jud_court")))
##練習:臺灣高等法院臺中分院刑事判決112年度再字第1號
##練習:臺灣臺中地方法院112年度金訴字第2053號
##練習:臺灣臺中地方法院111年度金訴字第670號
##練習:臺灣臺中地方法院 112 年度易字第 1063 號刑事判決

#選擇法院
Court =Select(driver.find_element(By.NAME,"jud_court"))
Court_box = driver.find_element(By.NAME,"jud_court")
options = [x for x in Court_box.find_elements(By.TAG_NAME,"option")]
Court.select_by_visible_text('最高法院')


##輸入判決年度/字號/案號
JudgeYear = driver.find_element(By.ID,"jud_year")
JudgeYear.send_keys('112')
JudgeCase = driver.find_element(By.ID,"jud_case")
JudgeCase.send_keys('台上')
JudgeNo = driver.find_element(By.ID,"jud_no")
JudgeNo.send_keys('5286')
Query = driver.find_element(By.ID,"btnQry")
Query.click()
time.sleep(3)
#----------------------------------------------------------------------------------------------------------------------------------#
wait = WebDriverWait(driver, 10)
iframe = wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "iframe-data")))
table = wait.until(EC.presence_of_element_located((By.XPATH, "//table")))
cells = table.find_elements(By.XPATH, ".//td")

Result_links = table.find_elements(By.TAG_NAME,"a")
# print(Result_links)
data = []
##蒐集搜尋判決的查詢資料
for index,cell in enumerate(cells):
    
    ##取得名稱為包含刑事判決的連結
    Result_JudgeCourt = cell.text

    Result_JudgeTime = cells[(index+1)%5].text
    index_link = index//5
    link = Result_links[index_link].get_attribute("href")
    if index % 5==1 and Result_JudgeCourt.find('刑事判決') > -1:
        data.append([Result_JudgeCourt,Result_JudgeTime,link])
data_result = pd.DataFrame(data)
data_result.columns=['判決字號','裁判日期','連結']
# print(data_result)


# #------------------------------------------------------------------------------------------------------------------------------------#
###爬取判決書內容的文章
links = data_result['連結']
# url = 'https://judgment.judicial.gov.tw/FJUD/data.aspx?ty=JD&id=TNHM%2c111%2c%e4%be%b5%e4%b8%8a%e8%a8%b4%2c1652%2c20230307%2c1&ot=in'
for link in links:
    print(link)
    driver.get(link)
    
    locator = (By.CSS_SELECTOR,"div[class='rela-area col-xs-4']")
    WebDriverWait(driver,10).until(
        EC.presence_of_all_elements_located(locator)
        ,"找不到指定的元素"#若找不到定元素就顯示錯誤訊息
        )
    #針對歷史裁判案號爬蟲

    Historys = wait.until(EC.presence_of_element_located((By.ID, 'JudHis')))
    # history_links ##歷屆判決連結
    history_body = Historys.find_element(By.CSS_SELECTOR,'div[class="panel-body"]')
    history_title = Historys.find_element(By.CSS_SELECTOR,'div[class="panel-heading"]')
    print(history_body.find_elements(By.TAG_NAME,"a"))
    history_links = history_body.find_elements(By.TAG_NAME,"a")
    print(history_title.find_element(By.CSS_SELECTOR,'span[class="badge"]').text)
    ##如果有歷屆審判資料則爬取下來
    for history in history_links:
        print(history.text)
        print(history.get_attribute("href"))
        # for judcase_link in history_links:
            # history = requests.get(history_links.get_attribute("href"))
            # history_result = BeautifulSoup(history.text,'lxml').find_all(By.XPATH, ".//td")
            # print(history_result)
            # history_judCase = judcase_link.text##歷屆判決案號
    # else:
    #     history_judCase=''
    #     history_link =''
    # print((history_judCase,history_link))
    ##搜尋判決文標題
    titles = driver.find_elements(By.CSS_SELECTOR,'div[class="notEdit"]')
    t =[]
    for title in titles:
        text = re.sub(r"\s+", "", title.text)
        t.append(text)

    # print(t[t.index('主文')+1])##找主文下一個標題
    response = requests.get(link)
    soup = BeautifulSoup(response.text,'lxml')
    #判決全文內容
    htmlcontent = soup.find('div',{'class':'htmlcontent'})
    
    result =[]
    # 多個字元資料清理
    contents = htmlcontent.find_all('div')

    for content in contents:
        # print(content.getText())
        word = content.getText()
            
        if word.find('\xa0') > -1:
            word = word.replace('\xa0','')
        if word.find('\u3000') > -1:
            word = word.replace('\u3000','')
        if word.find('\uf6b0') > -1:
            word = word.replace('\uf6b0','')
        if word.find('\uf6af') > -1:
            word = word.replace('\uf6af','')
        else:
            ##去掉所有空白
            word = re.sub(r"\s+", "", word)
        result.append(word)
    # print(result)

    crime =[]
    for index,word in enumerate(result) :
        Core_index = result.index('主文')
        ##法院種類
        if (word.find('刑事判決') > -1 and word.find('臺灣') > -1) or word.find('最高法院刑事判決') > -1:
            JudgeCourt=word
            judCase=result[result.index(JudgeCourt)+1:result.index(JudgeCourt)+2][0]
        # print('法院:'+JudgeCourt)
        # print('判決案號:',judCase)
        
        if (word=='主文') :
            Core_content = result[Core_index+1:result.index(t[t.index('主文')+1])]

        if (word.find('起訴案號') > -1 ):
            sueCase=word[word.index('起訴案號')+5:word.find('）')]
        elif word.find('檢察官提起公訴（')>-1:
            sueCase=word[word.index('檢察官提起公訴（')+8:word.find('）')]
        # print('起訴案號:',sueCase)    
        # print('主文:',Core_content)
       
        if (word.find('被告') > -1 or word.find('上訴人') > -1) and len(word)<10:
            defendants = result[result.index(word)-1:result.index('主文')] 
            print(defendants)
            if word.find('被告') > -1:
                defendant=[defendant.replace("被告","") for defendant in defendants if len(defendant)<=5 and defendant!='']
            else:
                defendant=[defendant.replace("上訴人","") for defendant in defendants if len(defendant)<=6 and defendant!='']
        # print('被告:',defendant)
        ##論罪科刑
        
        ##1.使用"核被告"撈取罪名
        if word.find('核被告') > -1 and word.find('係犯') > -1:#
            ##找出在核被告之後的句號位置判斷完整的描述
            crime_start = word
            print(crime_start)
                
            # if word.find("。") >-1 :
            #     crime_end = word
            crime.append(crime_start)
                    
        else:
            crimes=result[Core_index+1:result.index(t[t.index('主文')+1])]
       
            ##若沒有核被告等關鍵字，從主文判斷罪名
            # if Core_content.find('上訴駁回')>-1 or (Core_content.find('附表') > -1 and Core_content.find('編號') > -1): 
            #     number1 = Core_content[Core_content.index('附表')-2:Core_content.index('編號')]##尋找附表號碼
            #     number2 = Core_content[Core_content.index('編號')+2:]
            #     ##針對歷年審判的判決文搜尋
            #     if len(history_judCase)>0:
            #         for index,judCase in enumerate(history_judCase):
            #             if history_judCase.find('地方法院')>-1:
            #                 history_result = requests.get(history_link[index])
            #                 print(history_result)

print(['法院:',JudgeCourt,'判決案號:',judCase,'主文:',Core_content,'被告:',defendant,'起訴案號:',sueCase,'罪名:',crime,'歷屆審判案號:',history_judCase,'歷屆審判連結',history_link])
    
            


