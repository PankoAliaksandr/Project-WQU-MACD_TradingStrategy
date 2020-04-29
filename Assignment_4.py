# Import libraries
import datetime
import pandas as pd
from pandas_datareader import data as pdr
import matplotlib.pyplot as plt
import numpy as np


# Class implementation
class TradingStrategy:

    # Constructor
    def __init__(self, index1, index2, start_date, end_date):
        self.__index1 = index1
        self.__index2 = index2
        self.__start_date = start_date
        self.__end_date = end_date
        self.__index1_data = pd.DataFrame()
        self.__index2_data = pd.DataFrame()
        self.__ratio_data = pd.DataFrame(columns=['Ratio', 'EMA10'])
        self.__returns_data = pd.DataFrame(columns=['Start', 'End',
                                                    'Operation', 'Return'])
        self.__support = None
        self.__resistance = None
        self.__returns = list()
        self.__cum_returns = list()

        self.__download_data()

    def __download_data(self):
        self.__index1_data = pdr.get_data_yahoo(self.__index1,
                                                self.__start_date,
                                                self.__end_date)
        self.__index2_data = pdr.get_data_yahoo(self.__index2,
                                                self.__start_date,
                                                self.__end_date)
        self.__ratio_data['Ratio'] = self.__index1_data['Adj Close'] /\
            self.__index2_data['Adj Close']

        self.__calculate_DEMA()

    # Getters
    def get_index1_data(self):
        return self.__index1_data

    def get_index2_data(self):
        return self.__index2_data

    def get_ratio_data(self):
        return self.__ratio_data

    def get_returns(self):
        return self.__returns_data

    # Calculations
    def __calculate_boundaries(self):
        price_ratio_mean = np.mean(self.__ratio_data['Ratio'])
        price_ratio_std = np.std(self.__ratio_data['Ratio'])
        self.__support = price_ratio_mean - price_ratio_std
        self.__resistance = price_ratio_mean + price_ratio_std

    def __calculate_DEMA(self):
        self.__ratio_data['EMA10'] = self.__ratio_data['Ratio'].ewm(
                ignore_na=False, span=10, adjust=False).mean()

    def __add_return(self, start_date, end_date, operation,
                     operation_return):

        k = len(self.__returns_data)

        self.__returns_data.loc[k] = [start_date, end_date,
                                      operation, operation_return]

    def __calculate_return(self, start, end, operation):

        start_index1_price = self.__index1_data['Adj Close'][
                self.__index1_data.index == start].values[0]
        start_index2_price = self.__index2_data['Adj Close'][
                self.__index1_data.index == start].values[0]
        end_index1_price = self.__index1_data['Adj Close'][
                self.__index1_data.index == end].values[0]
        end_index2_price = self.__index2_data['Adj Close'][
                self.__index1_data.index == end].values[0]

        if (operation == 'short'):
            # index 1 sell, index 2 buy
            operation_return_s = (start_index1_price - end_index1_price) / \
                end_index1_price
            operation_return_l = (end_index2_price - start_index2_price) / \
                start_index2_price

        if (operation == 'long'):
            # index 1 buy, index 2 sell
            operation_return_l = (end_index1_price - start_index1_price) / \
                start_index1_price
            operation_return_s = (start_index2_price - end_index2_price) / \
                end_index2_price

        operation_return = operation_return_s + operation_return_l
        return operation_return

    def __calculate_cum_returns(self):
        cum_return = (self.__returns_data['Return'] + 1).prod() - 1
        return cum_return

    def __calculate_cum_returns1(self):
        self.__cum_returns.append(1)
        cum_sum = 1
        for i in range(len(self.__returns_data)):
            cum_sum = cum_sum*(1+self.__returns_data['Return'][i])
            self.__cum_returns.append(cum_sum)

    def __test_strategy(self):

        open_position = False
        operation = None
        start_position_date = None

        for i in range(1, len(self.__ratio_data)):

            if i == len(self.__ratio_data):

                # last day: Close the position
                end_position_date = self.__ratio_data.index[i]
                # Close a position
                open_position = False

                operation_return = self.__calculate_return(start_position_date,
                                                           end_position_date,
                                                           operation)

                self.__add_return(start_position_date, end_position_date,
                                  operation, operation_return)

            if ((self.__ratio_data['EMA10'][i] > self.__support) and
                    (self.__ratio_data['EMA10'][i-1] < self.__support)):

                # Long index 1 short index 2
                if (open_position):
                    # Close position
                    end_position_date = self.__ratio_data.index[i]
                    open_position = False
                    operation_return = self.__calculate_return(
                                            start_position_date,
                                            end_position_date,
                                            operation)

                    self.__add_return(start_position_date, end_position_date,
                                      operation, operation_return)

                start_position_date = self.__ratio_data.index[i]
                open_position = True
                operation = 'long'

            if ((self.__ratio_data['EMA10'][i] < self.__resistance) and
                    (self.__ratio_data['EMA10'][i-1] > self.__resistance)):

                # Sort index 1 lond index 2
                if (open_position):

                    end_position_date = self.__ratio_data.index[i]
                    open_position = False

                    operation_return = self.__calculate_return(
                            start_position_date,
                            end_position_date,
                            operation)

                    self.__add_return(start_position_date, end_position_date,
                                      operation, operation_return)

                # Open new position
                start_position_date = self.__ratio_data.index[i]
                open_position = True
                operation = "short"

    # Visualisation
    def __visualize(self):
        # Plot price ratio
        plt.figure(figsize=(10, 7))
        plt.plot(self.__ratio_data['Ratio'])
        plt.title("Price ratio of DJT over DJI")
        mean = self.__ratio_data['Ratio'].mean()
        std = self.__ratio_data['Ratio'].std()
        plt.axhline(y=mean, color='r', linestyle='-')
        plt.axhline(y=mean+std, color='g', linestyle='-')
        plt.axhline(y=mean-std, color='g', linestyle='-')
        plt.show()

        # Plot cumulative returns
        plt.figure(figsize=(10, 7))
        plt.plot(self.__cum_returns)
        plt.title("Cumulative returns of strategy")
        plt.show()

    def main(self):
        self.__calculate_boundaries()
        self.__test_strategy()
        self.__calculate_cum_returns1()
        print(self.__calculate_cum_returns())
        self.__visualize()
        return self.__cum_returns


index1 = '^DJT'
index2 = '^DJI'
end_date = datetime.date.today()
start_date = datetime.date(end_date.year - 5, end_date.month,
                           end_date.day)

strategy = TradingStrategy(index1, index2, start_date, end_date)
strategy.main()
