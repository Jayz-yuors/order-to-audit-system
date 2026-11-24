from decimal import Decimal
def test_yield_and_oil_variance():
 assert (Decimal(188)-200)/200*100 == -6
 assert (Decimal('10.5')-10)/10*100 == 5
def test_invoice():
 taxable=Decimal(150)*50; tax=taxable*Decimal('0.05')
 assert taxable==7500 and tax==375 and taxable+tax==7875
 assert taxable+tax-4000==3875
def test_stock():
 assert 100+60-40==120
 assert 30-Decimal('10.5')==Decimal('19.5')
 assert 500-188-6==306
 assert 50+188-150==88
