# -*- coding: utf-8 -*-
"""
Created on Sun Jun  7 15:33:34 2020

@author: ARPIT
"""

import xlsxwriter
import os
import smtplib 
from email.mime.multipart import MIMEMultipart 
from email.mime.text import MIMEText 
from email.mime.base import MIMEBase 
from email import encoders 

#to calculate data quality criteria
def calculate_and_report(tot_time,report):
    no_of_markets = len(report)
    dp_expected_permarket = (tot_time)
    dp_expected_total = (tot_time)*no_of_markets
    dp_obtained_total = 0
    for x in report:
         dp_obtained_total += report[x]
    
    percent_dp_total = (float)(100*((float)(dp_obtained_total)/(float)(dp_expected_total)))
    # this can happen due to asyn nature of websockets and moreover we are sending mail for real time data
    overall_stats = {"Markets": no_of_markets,
                     "Datapoints expected": dp_expected_total,
                     "Datapoints expected permarket": dp_expected_permarket,
                     "Datapoints obtained in total": dp_obtained_total,
                     "% of datapoints available": percent_dp_total}
    permarket={}
    for x in report:
         y = (float)(100*((float)(report[x])/(float)(dp_expected_permarket)))
         permarket.update({x: y})
   
    #we create an excel file for our report      
    workbook = xlsxwriter.Workbook('Stats.xlsx')
    Overall_Statistics = workbook.add_worksheet()
    Permarket_Statistics = workbook.add_worksheet()
        
    row1 = 0
    col1 = 0
    
    #We iterate over the data and write it out row by row
    for x in overall_stats:
        Overall_Statistics.write(row1, col1, x)
        Overall_Statistics.write(row1, col1 + 1, overall_stats[x])
        row1 += 1
    
    row2 = 0
    col2 = 0
    Permarket_Statistics.write(row2,  col2, "Symbol")
    Permarket_Statistics.write(row2, col2+1, "% of Obtained datapoints")
    row2+=1
    
    for x in permarket:
        Permarket_Statistics.write(row2, col2, x)
        Permarket_Statistics.write(row2, col2 + 1, permarket[x])
        row2 += 1
    
    
    workbook.close()

    #setting up the email process
    fromaddr = os.getenv("SENDER_ID")
    toaddr = os.getenv("RECEIVER_ID")
    pswd = os.getenv("MAIL_PSWD")
    
    #instance of MIMEMultipart 
    msg = MIMEMultipart() 
      
    #for storing the senders email address   
    msg['From'] = fromaddr 
      
    #for storing the receivers email address  
    msg['To'] = toaddr 
      
    #for storing the subject  
    msg['Subject'] = "Binance Market Report"
      
    #to store the body of the mail 
    body = "Please find attached the periodic reports (Sheet1 - Overall, Sheet2 - Individual Market)"
      
    #to attach the body with the msg instance 
    msg.attach(MIMEText(body, 'plain')) 
      
    #to open the file to be sent  
    filename = "Stats.xlsx"
    attachment = open(filename, "rb") 
      
    #instance of MIMEBase and named as p 
    p = MIMEBase('application', 'octet-stream') 
      
    #to change the payload into encoded form 
    p.set_payload((attachment).read()) 
      
    #encode into base64 
    encoders.encode_base64(p) 
       
    p.add_header('Content-Disposition', "attachment; filename= %s" % filename) 
      
    #to attach the instance 'p' to instance 'msg' 
    msg.attach(p) 
      
    #to create SMTP session 
    s = smtplib.SMTP('smtp.gmail.com', 587) 
      
    #to start TLS for security 
    s.starttls() 
      
    #Authentication 
    s.login(fromaddr, pswd) 
      
    #to convert the Multipart msg into a string 
    text = msg.as_string() 
      
    #for sending the mail 
    s.sendmail(fromaddr, toaddr, text) 
      
    #for terminating the session 
    s.quit() 
    
