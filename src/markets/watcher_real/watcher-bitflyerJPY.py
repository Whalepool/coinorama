#!/usr/bin/python
#
# Coinorama/coinref: watch and store raw Bitfinex USD market info
#
# This file is part of Coinorama <http://coinorama.net>
#
# Copyright (C) 2013-2016 Nicolas BENOIT
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#


import time
import traceback
import httplib
import coinwatcher
import json

# Watcher class
class BitflyerJPYWatcher (coinwatcher.CoinWatcher) :
    def __init__ ( self, shortname, with_coinrefd, logger ):
        coinwatcher.CoinWatcher.__init__ ( self, shortname, with_coinrefd, logger )
        self.mostRecentTransaction = ( time.time() - 1 )
        self.mostRecentTransactionID = 0
        self.mostRecentPrice = 0
	self.JPY_USD_rate = 0.0084
	self.JPY_USD_stamp = 0

    def buildData ( self, book, trades, lag ):
        ed = coinwatcher.ExchangeData ( )

        mostRecentID = self.mostRecentTransactionID
        mostRecentDate = 0
        mostRecentPrice = self.mostRecentPrice
        try:
            for t in trades:
                tid = int ( t['id'] )
                tvol = float ( t['size'] )
                if ( tid > self.mostRecentTransactionID ):
                    ed.volume += tvol
                    ed.nb_trades += 1
                if ( tid > mostRecentID ):
                    mostRecentID = tid
                    mostRecentPrice = float ( t['price'] )
        except Exception:
            self.logger.write ( 'error: buildData() failed with trades\n' + str(traceback.format_exc()) )
            return None

        try:
            for b in book['bids']:
                bprice = float ( b['price'] )
                bvol = float ( b['size'] )
                ed.bids.append ( [ bprice, bvol ] )
                ed.total_bid += bprice * bvol
            ed.bids.sort ( reverse=True )

            for a in book['asks']:
                aprice = float ( a['price'] )
                avol = float ( a['size'] )
                ed.asks.append ( [ aprice, avol ] )
                ed.total_ask += avol
            ed.asks.sort ( )
        except Exception:
            self.logger.write ( 'error: buildData() failed with book\n' + str(traceback.format_exc()) )
            return None

        try:
            if ( mostRecentID != 0 ):
                self.mostRecentPrice = mostRecentPrice
            if ( self.mostRecentPrice == 0 ):
                self.mostRecentPrice = ed.bprice
            if ( mostRecentID != 0 ):
                self.mostRecentTransactionID = mostRecentID
            ed.rate = self.mostRecentPrice
            ed.lag = lag
            ed.ask_value = aprice
            ed.bid_value = bprice
            ed.USD_conv_rate = self.JPY_USD_rate
        except Exception:
            self.logger.write ( 'error: buildData() failed with ticker\n' + str(traceback.format_exc()) )
            return None

        return ed

    def fetchData ( self ):
	if ( (time.time()-self.JPY_USD_stamp) > 3600.0 ): # get USD/JPY rate every hour
            try:
                connection = httplib.HTTPConnection ( 'download.finance.yahoo.com', timeout=5 )
                connection.request ( 'GET', '/d/quotes.csv?s=JPYUSD=X&f=sl1&e=.csv' )
                r = connection.getresponse ( )
                if ( r.status == 200 ):
                    rate_txt = r.read ( )
                    rate = float ( rate_txt.split(',')[1] )
                    if ( rate > 0 ):
                        self.JPY_USD_rate = rate
                        self.JPY_USD_stamp = time.time ( )
                        #self.logger.write ( 'rate: %f ' % self.JPY_USD_rate )
                else:
                    self.logger.write ( 'error JPY_USD status %d' % r.status )
                connection.close ( )
            except Exception:
                self.logger.write ( 'error: unable to get JPY/USD\n' + str(traceback.format_exc()) )
                pass
        trades = '/v1/getexecutions?product_code=BTC_JPY'
        ed = coinwatcher.CoinWatcher.fetchData ( self, httplib.HTTPSConnection, 'api.bitflyer.jp', '/v1/getboard?product_code=BTC_JPY', trades )
        return ed



#
#
# main program
#

if __name__ == "__main__":
    coinwatcher.main ( 'BitflyerJPY', 'bitflyerJPY', BitflyerJPYWatcher )
