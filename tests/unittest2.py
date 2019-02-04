import unittest
import sys
from eosfactory.eosf import *

verbosity([Verbosity.INFO, Verbosity.OUT])

verbosity([Verbosity.INFO, Verbosity.OUT, Verbosity.DEBUG])

CONTRACT_WORKSPACE = sys.path[0] + "/../"
TOKEN_CONTRACT_WORKSPACE = sys.path[0] + "/../infinicoin/"

# utility method to get INF from given amount
def to_inf(amount):
    return str(amount) + ".0000 INF"

# hold balances and states

# bobs's account and deposit balance
bob_acc_balance = 0
bob_dep_balance = 0

# alices's account and deposit balance
alice_acc_balance = 0
alice_dep_balance = 0

infinicoinio_balance = 0
infiniverse_balance = 0
max_supply = 1000000000

# Utility method to print values
def print_status():
    print("#######################################################################")

    print("alice deposit balance " + to_inf(alice_dep_balance))
    print("alice account balance " + to_inf(alice_acc_balance))

    print("bob deposit balance " + to_inf(bob_dep_balance))
    print("bob account balance " + to_inf(bob_acc_balance))

    print("infinicoinio account balance " + to_inf(infinicoinio_balance))
    print("infiniverse account balance " + to_inf(infiniverse_balance))

    print("#######################################################################")

class Test(unittest.TestCase):

    # def __init__(self):
    #     # bob's account and deposit balance
    #     self.bob_acc_balance = 0
    #     self.bob_dep_balance = 0

    #     # alices's account and deposit balance
    #     self.alice_acc_balance = 0
    #     self.alice_dep_balance = 0

    #     self.infinicoinio_balance = 0
    #     self.max_supply = 1000000000

    def run(self, result=None):
        super().run(result)

    @classmethod
    def setUpClass(cls):
        global bob_acc_balance
        global bob_dep_balance

        global alice_acc_balance
        global alice_dep_balance

        global infinicoinio_balance
        global infiniverse_balance
        global max_supply

        SCENARIO('''
        Test the registered land functionality of infiniverse contract
        ''')

        COMMENT('''
        Create test accounts, deploy contracts and do token transfers
        ''')

        reset()
        create_master_account("eosio")

        # test accounts and accounts where the smart contracts will be hosted
        create_account("alice", eosio, account_name="alice")
        create_account("bob", eosio, account_name="bob")
        create_account("infiniverse", eosio, account_name="infiniverse")
        create_account("infinicoinio", eosio, account_name="infinicoinio")

        # build and deploy token and infiniteverse contracts
        token_contract = Contract(infinicoinio, TOKEN_CONTRACT_WORKSPACE)
        token_contract.build(force=True)
        token_contract.deploy()

        contract = Contract(infiniverse, CONTRACT_WORKSPACE)
        contract.build(force=True)
        contract.deploy()

        # Assumption : Making infinicoinio account as the same as the issuer
        token_contract.push_action(
            "create",
            {
                "issuer": infinicoinio,
                "maximum_supply": to_inf(max_supply)
            },
            [infinicoinio]
        )

        # set eosio.code permission to the infiniverse contract
        infiniverse.set_account_permission(
            Permission.ACTIVE,
            {
                "threshold": 1,
                "keys": [
                    {
                        "key": infiniverse.active(),
                        "weight": 1
                    }
                ],
                "accounts":
                [
                    {
                        "permission":
                            {
                                "actor": infiniverse,
                                "permission": "eosio.code"
                            },
                        "weight": 1
                    }
                ]
            },
            Permission.OWNER,
            (infiniverse, Permission.OWNER)
        )

        # transfer some funds to alice's and bob's account
        token_contract.push_action(
            "issue",
            {
                "to": alice,
                "quantity": to_inf(1000),
                "memo": "Issued 1000 INF to alice"
            },
            [infinicoinio]
        )
        alice_acc_balance += 1000

        token_contract.push_action(
            "issue",
            {
                "to": bob,
                "quantity": to_inf(1000),
                "memo": "Issued 1000 INF to bob"
            },
            [infinicoinio]
        )
        bob_acc_balance += 1000

        # open a deposit for alice and bob
        contract.push_action(
            "opendeposit",
            {
                "owner": alice
            },
            [alice]
        )

        contract.push_action(
            "opendeposit",
            {
                "owner": bob
            },
            [bob]
        )

        # deposit some funds for alice and bob
        token_contract.push_action(
            "transfer",
            {
                "from": alice,
                "to": infiniverse,
                "quantity": to_inf(900),
                "memo": "deposited 900 INF to infiniverse account"
            },
            [alice]
        )

        # update balances
        alice_acc_balance -= 900
        alice_dep_balance += 900
        infiniverse_balance += 900

        token_contract.push_action(
            "transfer",
            {
                "from": bob,
                "to": infiniverse,
                "quantity": to_inf(900),
                "memo": "deposited 900 INF to infiniverse account"
            },
            [bob]
        )

        # update balances
        bob_acc_balance -= 900
        bob_dep_balance += 900
        infiniverse_balance += 900

        # debug
        print_status()

    def setUp(self):
        pass

    def test_01_registerLand(self):
        global bob_acc_balance
        global bob_dep_balance

        global alice_acc_balance
        global alice_dep_balance

        global infinicoinio_balance
        global infiniverse_balance
        global max_supply

        COMMENT('''
        Register a land for alice
        ''')
        infiniverse.push_action(
            "registerland",
            {
                "owner": alice,
                "lat_north_edge": 30.00001,
                "long_east_edge": 40.00001,
                "lat_south_edge": 30,
                "long_west_edge": 40
            },
            [alice]
        )

        # update balances
        # given land dimensions costs 1.0000 INF
        alice_dep_balance -= 1
        infiniverse_balance -= 1
        infinicoinio_balance += 1

        # get table data
        lands = infiniverse.table("land", infiniverse)
        issuer_account = infinicoinio.table("accounts", infinicoinio)
        deposits = infiniverse.table("deposit", infiniverse)

        COMMENT('''
        Check accounts and balances
        ''')
        self.assertEqual(
            lands.json["rows"][0]["owner"], "alice",
            "owner is not alice"
        )

        self.assertEqual(
            deposits.json["rows"][0]["owner"], "alice",
            "owner is not alice"
        )

        self.assertEqual(
            deposits.json["rows"][0]["balance"], to_inf(
                alice_dep_balance),
            "alice deposit balance incorrect"
        )

        self.assertEqual(
            issuer_account.json["rows"][0]["balance"], to_inf(
                infinicoinio_balance),
            "issuer (inficoinio) balance incorrect"
        )

        # debug
        print_status()

    def test_02_moveland(self):
        global bob_acc_balance
        global bob_dep_balance

        global alice_acc_balance
        global alice_dep_balance

        global infinicoinio_balance
        global infiniverse_balance
        global max_supply

        COMMENT('''
        Move the land to new location
        ''')
        infiniverse.push_action(
            "moveland",
            {
                "land_id": 0,
                "lat_north_edge": 40.00001183,
                "long_east_edge": 50.00001183,
                "lat_south_edge": 40,
                "long_west_edge": 50
            },
            [alice]
        )

        # get table data
        lands = infiniverse.table("land", infiniverse)
        deposits = infiniverse.table("deposit", infiniverse)

        COMMENT('''
        Check accounts and balances
        ''')
        self.assertEqual(
            lands.json["rows"][0]["id"], 0,
            "land id is different"
        )

        self.assertEqual(
            lands.json["rows"][0]["owner"], "alice",
            "owner is not alice"
        )

        self.assertEqual(
            deposits.json["rows"][0]["owner"], "alice",
            "alice account does not exists in deposit"
        )

        self.assertEqual(
            deposits.json["rows"][0]["balance"], to_inf(
                alice_dep_balance),
            "alice deposit balance is not same"
        )

        # debug
        print_status()

    def test_03_setlandprice(self):
        global bob_acc_balance
        global bob_dep_balance

        global alice_acc_balance
        global alice_dep_balance

        global infinicoinio_balance
        global infiniverse_balance
        global max_supply

        COMMENT('''
            Set land price (puts up the land for the sale)
            ''')

        target_price = to_inf(1000000000)
        land_id = 0

        infiniverse.push_action(  # potential bug here
            "setlandprice",
            {
                "land_id": land_id,
                "price": target_price
            },
            [alice]
        )

        # get tables data
        lands = infiniverse.table("land", infiniverse)
        landprices = infiniverse.table("landprice", infiniverse)

        COMMENT('''
            Check land id and balance
            ''')
        self.assertEqual(
            lands.json["rows"][0]["id"], land_id,
            "land id does not match in lands table"
        )

        self.assertEqual(
            landprices.json["rows"][0]["land_id"], land_id,
            "land_id does not match in landprices table"
        )

        self.assertEqual(
            landprices.json["rows"][0]["price"], target_price,
            "set land price does not match price in table landprices"
        )

        # debug
        print_status()

    def test_04_cancelsale(self):
        global bob_acc_balance
        global bob_dep_balance

        global alice_acc_balance
        global alice_dep_balance

        global infinicoinio_balance
        global infiniverse_balance
        global max_supply

        COMMENT('''
        Cancel sale for the land
        ''')

        land_id = 0
        infiniverse.push_action(
            "cancelsale",
            {
                "land_id": land_id
            },
            [alice]
        )

        # get tables data
        lands = infiniverse.table("land", infiniverse)
        landprices = infiniverse.table("landprice", infiniverse)

        COMMENT('''
            Check land id and balance
            ''')
        self.assertEqual(
            lands.json["rows"][0]["id"], land_id,
            "land id does not match in lands table"
        )

        self.assertEqual(
            len(landprices.json["rows"]), 0,
            "land price still exists in the land prices table"
        )

        # debug
        print_status()

    def test_05_buyland(self):
        global bob_acc_balance
        global bob_dep_balance

        global alice_acc_balance
        global alice_dep_balance

        global infinicoinio_balance
        global infiniverse_balance
        global max_supply

        COMMENT('''
        Put the alice's land for sale again
        ''')

        land_id = 0
        price = 20

        infiniverse.push_action(
            "setlandprice",
            {
                "land_id": land_id,
                "price": to_inf(price)
            },
            [alice]
        )

        COMMENT('''
        Buy alice's land from bob's account 
        ''')
        infiniverse.push_action(
            "buyland",
            {
                "buyer": "bob",
                "land_id": land_id,
                "price": to_inf(price)
            },
            [bob]
        )

        # update balances
        bob_dep_balance -= price
        alice_acc_balance += price
        infiniverse_balance -= price

        # debug
        print_status()

        # get tables data
        alice_account = infinicoinio.table("accounts", alice)
        infiniverse_account = infinicoinio.table("accounts", infiniverse)
        deposits = infiniverse.table("deposit", infiniverse)
        lands = infiniverse.table("land", infiniverse)
        landprices = infiniverse.table("landprice", infiniverse)

        COMMENT('''
        Checking lands, landprices, deposits and account balances
        ''')
        self.assertEqual(
            alice_account.json["rows"][0]["balance"], to_inf(
                alice_acc_balance),
            "alice did not recieve land selling money"
        )

        self.assertEqual(
            infiniverse_account.json["rows"][0]["balance"], to_inf(
                infiniverse_balance),
            "land selling money not deducted from infiniverse smart contract's account"
        )

        self.assertEqual(
            lands.json["rows"][0]["owner"], "bob",
            "lands ownership not transferred to bob"
        )

        self.assertEqual(
            len(landprices.json["rows"]), 0,
            "land was not removed from sale in landprices table"
        )

    def tearDown(self):
        pass

    @classmethod
    def tearDownClass(cls):
        stop()


if __name__ == "__main__":
    unittest.main()
