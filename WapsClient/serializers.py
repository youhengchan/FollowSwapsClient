from rest_framework import serializers
from .models import Wallet,DonorAddr
from rest_framework.exceptions import ValidationError
import web3
from .utils import *
from .uniswap import Uniswap


class DonorSerializer(serializers.ModelSerializer):

    fixed_value_trade=serializers.IntegerField(default=0)
    percent_value_trade=serializers.FloatField(default=0)
    gas_multiplier=serializers.FloatField(default=1)
    slippage=serializers.FloatField(default=0)
    id=serializers.IntegerField(read_only=True)
#     donors=serializers.StringRelatedField(many=True,read_only=True)
#     assets=serializers.StringRelatedField(many=True,read_only=True)
#     max_gas=serializers.IntegerField(read_only=True,default=0)
    follow_max=serializers.IntegerField(default=10**25)
    follow_min=serializers.IntegerField(default=0)
    retry_count=serializers.IntegerField(default=0,)
    errs=serializers.DictField(read_only=True,default={})
#     active=serializers.BooleanField(read_only=True)
#     telegram_channel_id=serializers.CharField()


    class Meta:
        model = DonorAddr
        exclude=[]

class WalletSerializer(serializers.ModelSerializer):
    active=serializers.BooleanField(read_only=True)
    mainnet=serializers.BooleanField()

    eth_balance=serializers.IntegerField(read_only=True)
    weth_balance=serializers.IntegerField(read_only=True)
    waps_balance=serializers.IntegerField(read_only=True)
    max_gas=serializers.IntegerField()
    telegram_channel_id=serializers.IntegerField()
    key_hash=serializers.CharField(max_length=128,write_only=True)

    skip_tokens=serializers.StringRelatedField(many=True,read_only=True)
    donors=DonorSerializer(many=True,read_only=True)

    class Meta:
        model = Wallet
        exclude=['key']





    def validate(self, data):

        mainnet=data['mainnet']



        if mainnet:
            provider_url = "https://mainnet.infura.io/v3/4022f5cb94f04bb0a0eaf4954ebf26ee"
        else:
            provider_url = "https://rinkeby.infura.io/v3/4022f5cb94f04bb0a0eaf4954ebf26ee"

        my_w3 = web3.Web3(web3.Web3.HTTPProvider(provider_url, request_kwargs={"timeout": 60}))
        follower = Uniswap(data['addr'], 'key', provider=my_w3, mainnet=mainnet)

        eth_balance,weth_balance,waps_balance=get_balances_eth_weth_waps(data['addr'],'key',mainnet,follower=follower)

        data['weth_balance']=weth_balance
        data['eth_balance']=eth_balance
        data['waps_balance']=waps_balance



        if Wallet.objects.filter(addr=data['addr']).exists():
            donors = Wallet.objects.get(addr=data['addr']).donors
            if donors.count()>3:
                raise ValidationError('you cant follow more than 3 wallets, server will not allow to follow more anyway')


        #todo проверка на создание или изменени
        tlg_check =telegram_bot_sendtext(f'wallet {data["addr"]}  was updated',int(data['telegram_channel_id']))
        if not tlg_check['ok']:
            raise ValidationError('incorrect telegram channel id, or u have to add our bot @FollowSwapsBot to your channel as admin ',)
        return data



