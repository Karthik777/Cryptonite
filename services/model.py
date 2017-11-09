class TransactionType:
    buy = 0
    sell = 1


class CryptoBuyInfo:
    def __init__(self):
        self.totalCurrencyAmount = 0.0
        self.totalNativeAmount = 0.0
        self.totalFees = 0.0
        self.buyList = []
        self.totalTaxDue = 0.0

    def append(self, tx):
        self.totalCurrencyAmount += tx.amount
        self.totalNativeAmount += tx.native_amount
        self.totalFees += tx.fees
        self.totalTaxDue += tx.tax
        self.buyList.append(tx)


class HoldingSplit:
    def __init__(self, amountSpent, availableCurrencyAmount, currentNativeValue, currency, tax, transactions):
        self.availableCurrencyAmount = availableCurrencyAmount
        self.currentNativeValue = currentNativeValue
        self.currency = currency
        self.amountSpent = amountSpent
        self.tax = tax
        self.transactions = transactions

class TaxReport:
    def __init__(self, totalNativeAmountSpent, totalNativeAmountValue, currentNetValue, taxDue, totalProfitIfConverted,
                 holdingSplits):
        self.totalNativeAmountSpent = round(totalNativeAmountSpent, 2)
        self.totalNativeAmountValue = round(totalNativeAmountValue)
        self.holdingSplits = holdingSplits
        self.taxDue = round(taxDue)
        self.totalProfitIfConverted = round(totalProfitIfConverted)
        self.currentNetValue = round(currentNetValue)

class Transaction:
    def __init__(self, id, native_amount, amount, date, coinCurrency, fees, currentRate, transactionType=TransactionType().buy,
                 native_currency='AUD'):
        self.transactionType = transactionType
        self.id = id
        self.currency = native_currency
        self.coinCurrency = coinCurrency
        self.native_amount = native_amount
        self.amount = amount
        self.date = date
        self.fees = fees
        self.tax = self.CalculateGains(amount * currentRate - native_amount)

    def CalculateGains(self, totalEarnings):
        return totalEarnings*.30
