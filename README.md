# Capturing-Crypto-Currency-Data-in-Real-Time-form-Binance-
Exchange Markets are highly volatile and many times there is a need to capture the data in real-time for analysis and trading purposes. Same goes for Crypto-graphic currency exchanges such as [Binance](https://www.binance.com/en). 
I have here tried to create a process that does the job of capturing 1 minute real-time tick data of all the markets listed on Binance, obtaining the required datapoints and storing them in a database in a required comprehensive format. In addition to it, I have involved a process to create and mail the data-quality report (to some recepient). Finally, I have briefly described the procedure to deploy this python process on [Amazon AWS](https://aws.amazon.com/) EC2.


## Installation
- Setup Python environment on your system. I have used [Python Version 3.8.3](https://www.python.org/downloads/) along wih [Anaconda Navigator](https://www.anaconda.com/products/individual). I have used Spyder as an IDE.
- Once the setup is up and running, we need to register on Binance to get the [API keys](https://www.binance.com/en/support/articles/360002502072#:~:text=After%20logging%20into%20the%20Binance,to%20bind%20the%20secondary%20authentication.) for establishing connection.
- Now we need to ensure certain packages are installed in Python. Below is a combined list of all the packages necessary for this project. Their usage will be clear in the subsequent steps.
  - python-binance
  - pymongo (Because I am using MongoDB as database)
  - python-dotenv
  - smtplib
  - requests
  - json
  
  Use the following command in your terminal 
  
  `python -m pip install <package name>`
  
## Database Setup
- I have used [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)(free version) for storing the datapoints.
- Create your account and then a new cluster.
- Add a database user and the name used along with the password will be required in the URL to connect to the Mongo Client via your python code
- Ensure that under Network Access Tab, your system's IP is listed. Or else use 0.0.0.0/0 for access from anywhere

## The Process
Now we can divide the whole process into sub-processes.
1. Capturing and storing real-time 1m tick data from binance for all markets.
2. Resampling the data into 5,15,30 and 60 minute intervals for comprehensive analysis.
3. Mailing the data-capture report.

First establish the binance client using API keys. I recommend using a separate file to store the keys and import the file in your code.
```
from binance.client import Client

PUBLIC = KEY_BINANCE.Binance_API_Key
SECRET = KEY_BINANCE.Binance_Secret_Key

#Instantiating a Client 
client = Client(api_key=PUBLIC, api_secret=SECRET)
```

Now for the first part, we need a mechanism to access Binance Market in a way so that data is obtained in real-time. For this purpose, I have preferred using websockets. (Refer to [Binance Documentation](https://python-binance.readthedocs.io/en/latest/websockets.html) for setup details)
And to ensure data for all markets is recieved, we need to setup parallel websocket streams for each market. Python-Binance has a method for doing so.
```
from binance.websockets import BinanceSocketManager

bm = BinanceSocketManager(client)
def process_message(msg):
    print("stream: {} data: {}".format(msg['stream'], msg['data']))

# pass a list of stream names
connection_key = bm.start_multiplex_socket(['bnbbtc@kline_1m', 'neobtc@kline_1m'], process_m_message)
bm.start()
```

In place of ['bnbbtc@kline_1m', 'neobtc@kline_1m'], we have to pass all the market symbols listed on Binance.
```
connection_key = bm.start_multiplex_socket(GetSym.get_symbol_streams(), process_message)
```
The get_symbol_streams() is a helper method to obtain streams of all symbols in the format 'symbol'@kline_'interval'
The process_message is a callback function wherein the msg is recieved and we can apply the methods to format and resample the code as required.
Refer to the code for details of implementation.

Also we need to establish database connection to push the datapoints in it.
Following snippet does the job.
```
URL2 = os.getenv("MONGO_DB_URL")
try: 
    conne = MongoClient(URL2) 
    print("Connected successfully!!!") 
except pymongo.errors.ConnectionFailure as err:
    print(err)
db = conne.database 
```
(I have created a .env file to store the URL and other sensitive info that must not be mentioned explicitly in raw code, format mentioned at the end)

When all this is done, we would be able to recieve our data as a dictionary in msg.

Now comes the second part. 
The obtained msg dictionary consists of several parameters (as specified by [Kline Message Format](https://python-binance.readthedocs.io/en/latest/binance.html#binance.websockets.BinanceSocketManager.start_kline_socket)). We need to extract the required parameters for our purpose.
I here require the following parameters:
- Timestamp
- Market Symbol
- Open
- High
- Low
- Close
- Volume

To obtain timestamp in readable format-
```
timestamp = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
```

Also, an important job here is to regulate per minute flow of data into the database for each market symbol. The websocket stream may  provide multiple kline data for same timestamp. We can choose the first or last appearance of kline data for a particular timestamp. 
I have utilized my system's current date-time to check with per-minute dataflow.

Once regulated, data can be inserted in the database. 

However, I have further written process to resample the datapoints into specified intervals. For example, for a 5 min interval resampling, we would require to evaluate an equivalent entry based on the recent 5 entries of a symbol. For this new entry,
- Timestamp will be same as the start of 5 min interval (i.e. the timestamp of the least recent entry among the last 5 entries.)
- Symbol will be same.
- Open will be the open price at start of 5 min interval.(i.e. least recent entry's open price)
- High will be the highest price in the 5 min interval (i.e. max of 'High' among the last 5 entries)
- Low will be the lowest price in the 5 min interval (i.e. min of 'Low' among the last 5 entries)
- Close will the close price at end of 5 min interval(i.e. most recent entry's close price)
- Volume will be the total volume traded in 5 min interval(i.e. sum of volumes of last 5 entries)

I have defined a separate module to evaluate the resampled entry.

Accordingly, we can do for every 15,30 and 60 minute interval. Once done, we can push it in database. I have created separate collections for each 5,15,30 and 60 minute interval in my database.

Finally, the report part. After a certain fixed interval, I need to get a report of data quality measured in terms of -
- Number of markets captured
- Number of datapoints captured
- % of datapoints available
- % of datapoints available per market

For this, I am maintaining a dictionary to keep count of entries stored per market-symbol and then I can evaluate other parameters.
The mailing mechanism is based on SMTP. The report will be sent as an attatchment.
Refer the module for implementation of the mail process.

## AWS Deployment

I have deployed my entire project on Amazon AWS EC2.
Following are the brief steps to do so: (I would recommend going through [Tutorials](https://aws.amazon.com/getting-started/tutorials/deploy-code-vm/) to understand the process.)
1. Create an AWS account and setup an EC2 instance. 
2. Choose the AMI you want depending on the OS. I have preferred Ubuntu. (Moreover if you go for free options, then they are limited)
3. Run the instance on EC2 dashboard. (You will require PuTTY setup to deal with the keys.)
4. An important step here for ensuring mail mechanism works is to configure the security groups. You need to create a custom security group with outbound permissions enabled for SMTP and SMTPS.
5. Thereafter, you need to upload your project files on the Ubuntu IP you chose
```
pscp -i <key_name>.ppk <filename(with extension)> ubuntu@<IP>:/home/ubuntu
```
(Enter the key name, filename and IP alotted)
6. Once done, you can switch to your running instance using
```
ssh -i <key_name> ubuntu@<IP>
```
**(Note that the commands may vary from system to system depending on the OS and AMI)**

And with this, you have deployed your crypto-currency data capture project on AWS.

## Extras

- .env file format:
```
RECEIVER_ID=receiver@gmail.com
SENDER_ID=sender@gmail.com
MAIL_PSWD=********
MONGO_DB_URL=......URL.....
```
Suppose following data is to be stored in .env file. Write in above format and save the file as .env (no name, only .env extension) in the same directory as your python code. In the code, you have to use - 
```
import os
from dotenv import load_dotenv
load_dotenv()

#for example
mongoURL = os.getenv("MONGO_DB_URL")
```




