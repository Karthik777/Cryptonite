from coinbase.wallet.client import Client
import requests , json
from services.model import Transaction, CryptoBuyInfo, TaxReport, HoldingSplit
from dateutil import parser
import pickle
import csv
from flask import request
import datetime
import os


API_KEY = ''
API_SECRET = ''
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
ETH_DATA_PATH = os.path.join(APP_ROOT, 'eth-aud-max.csv')
BPI_DATA_PATH = os.path.join(APP_ROOT, 'btc-aud-max.csv')
HISTORIC_DATA_PATH = os.path.join(APP_ROOT, 'historicData.pickle')
BUYLIST_DATA_PATH = os.path.join(APP_ROOT, 'buyList.pickle')

class HistoricData:
    def __init__(self):
        self.data = None
        self.initialiseData()
        # self.litData = None
        # self.defaultStartDate = '2016-09-01'
        # self.defaultEndDate = '2017-09-01'
        # self.baseBPIURI = 'https://api.coindesk.com/v1/bpi/historical/close.json'
        # self.queryparams = '?start={0}&end={1}'
        # self.baseBPIparams = self.queryparams.format(self.defaultStartDate,self.defaultEndDate)

    def initialiseData(self):
        with open(HISTORIC_DATA_PATH,'rb') as hD:
            self.data = pickle.load(hD)
        if self.data is None:
            self.data = {'ETH': {}, 'BTC': {}}
            self.loadData(ETH_DATA_PATH, 'ETH')
            self.loadData(BPI_DATA_PATH, 'BTC')
            with open(HISTORIC_DATA_PATH, 'wb') as h:
                pickle.dump(self.data,h)

    def loadData(self, filePath, type):
        with open(filePath) as csvfile:
            readCSV = csv.reader(csvfile, delimiter=',')
            for row in readCSV:
                if readCSV.line_num == 1:
                    pass
                else:
                    date = parser.parse(row[0])
                    self.data[type][date.ctime()] = float(row[1])

class CoinBaseClient:

    def __init__(self):
        self.client = None
        self.user = None
        self.accounts = None
        self.buyList = []
        self.sellList = []
        self.transactionList = []
        # self.Connect()
        self.InitialiseData()

    def Connect(self):
        self.client = Client(API_KEY, API_SECRET)

    def InitialiseData(self):
        with open(BUYLIST_DATA_PATH,'rb') as bP:
            self.buyList = pickle.load(bP)

        # self.getBuys()
        # self.getTransactions()
        # self.getCurrentUser()

    def getCurrentUser(self):
        if self.user is None:
            self.user = self.client.get_current_user()
        return self.user

    def getBuys(self):
        with open(BUYLIST_DATA_PATH,'rb') as bP:
            self.buyList = pickle.load(bP)
        if self.buyList is None or len(self.buyList) == 0:
            for account in self.getAccounts():
                buys = self.client.get_buys(account.id)['data']
                crypto = CryptoBuyInfo()
                for buy in buys:
                    tx = Transaction(str(buy.id), float(buy.subtotal.amount), float(buy.amount.amount),
                                     parser.parse(buy.payout_at), buy.amount.currency, float(buy.fees[0].amount.amount),
                                     self.getPrice(buy.amount.currency, 'AUD'))
                    crypto.append(tx)

                self.buyList.append(crypto)
            with open(BUYLIST_DATA_PATH,'wb') as b:
                pickle.dump(self.buyList,b)

    def getTransactions(self):
        if len(self.transactionList) == 0:
            for account in self.getAccounts():
                 self.transactionList.append(self.client.get_transactions(account.id)['data'])
        # return self.transactionList

    def getSells(self):
        return self.client.get_sells(self.user.id)

    def getAccounts(self):
        if self.accounts is None:
            self.accounts = self.client.get_accounts()['data']
        return self.accounts

    def getPrice(self,currency, nativeCurrency):
        currencyPair = str(currency + '-' + nativeCurrency)
        response = requests.get('https://api.coinbase.com/v2/prices/' + currencyPair + '/sell')
        return float(json.loads(response.content)['data']['amount'])

class CryptoTaxManager:
    def __init__(self):
        self.coinBaseClient = CoinBaseClient()
        self.historicData = HistoricData()
        self.priceChart = self.historicData.data
        self.buyList = self.coinBaseClient.buyList
        # with open('buyList.pickle','rb') as bP:
        #     self.buyList = pickle.load(bP)
        # if self.buyList is None:
        #     self.coinBaseClient = CoinBaseClient()
        #     self.buyList = self.coinBaseClient.buyList
        # with open('historicData.pickle','rb') as hD:
        #     self.priceChart = pickle.load(hD)
        # if self.priceChart is None:
        #     hd = HistoricData()
        #     self.priceChart = hd.data


class CapitalGainsCalculator:
    def __init__(self):
        self.gainsPercentage = .30
        self.cryptoTaxManager = CryptoTaxManager()
        self.stockTaxReport = None
        self.LoadStockReport()

    def CalculateGains(self, totalEarnings):
        return totalEarnings*self.gainsPercentage

    def LoadStockReport(self):
        self.stockTaxReport = self.CalculateReport(self.cryptoTaxManager.buyList)

    def CalculateReport(self, currentHoldings):
        totalValueInNativeCurrency = 0.0
        totalSpentInNativeCurrency = 0.0
        totalDue = 0.0
        holdingSplits = []
        for holding in currentHoldings:
            # TODO: Implement Coinbase current price functionality
            # currentRateOfCurrency = self.cryptoTaxManager.priceChart[holding.buyList[0].coinCurrency][date]
            currentRateOfCurrency = self.cryptoTaxManager.coinBaseClient.getPrice(holding.buyList[0].coinCurrency, 'AUD')
            holdingSplit = HoldingSplit(holding.totalNativeAmount + holding.totalFees,
                                        holding.totalCurrencyAmount, holding.totalCurrencyAmount * currentRateOfCurrency,
                                        holding.buyList[0].coinCurrency, holding.totalTaxDue, holding.buyList)

            totalSpentInNativeCurrency += holdingSplit.amountSpent
            totalValueInNativeCurrency += holdingSplit.currentNativeValue
            totalDue += holdingSplit.tax
            holdingSplits.append(holdingSplit)
        currentNetVale = totalValueInNativeCurrency - totalSpentInNativeCurrency

        
        profit = currentNetVale - totalDue
        return TaxReport(totalSpentInNativeCurrency, totalValueInNativeCurrency,currentNetVale, totalDue, profit, holdingSplits)

# if __name__ == '__main__':
#      cg = CapitalGainsCalculator()
#      taxReport = cg.CalculateReport(cg.cryptoTaxManager.buyList)