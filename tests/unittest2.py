import unittest, sys
from eosfactory.eosf import *

verbosity([Verbosity.INFO, Verbosity.OUT])

verbosity([Verbosity.INFO, Verbosity.OUT, Verbosity.DEBUG])

CONTRACT_WORKSPACE = sys.path[0] + "/../"
TOKEN_CONTRACT_WORKSPACE = sys.path[0] + "/../infinicoin/"


class Test(unittest.TestCase):

    def run(self, result=None):
        super().run(result)

    @classmethod
    def setUpClass(cls):
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
        create_account("infiniverse", eosio, account_name="infiniverse")
        create_account("infinicoinio", eosio, account_name="infinicoinio")
        create_account("hacker", eosio, account_name="hacker")

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
                "maximum_supply": "1000000000.0000 INF"
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

        # transfer some funds to alice account
        token_contract.push_action(
            "issue",
            {
                "to": alice,
                "quantity": "1000.0000 INF",
                "memo": "Issued 1000 INF to alice"
            },
            [infinicoinio]
        )

        # open a deposit for alice
        contract.push_action(
            "opendeposit",
            {
                "owner": alice
            },
            [alice]
        )

        # deposit some funds 
        token_contract.push_action(
            "transfer",
            {
                "from": alice,
                "to": infiniverse,
                "quantity": "900.0000 INF",
                "memo": "deposited 900 INF to infiniverse account"
            },
            [alice]
        )


    def setUp(self):
        pass

    def test_01_registerLand(self):
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

        # get table data            
        lands = infiniverse.table("land", infiniverse)
        inf_account = infinicoinio.table("accounts", infiniverse)
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
            deposits.json["rows"][0]["balance"], "899.0000 INF",
            "alice deposit balance incorrect"
        )

        self.assertEqual(
            issuer_account.json["rows"][0]["balance"], "1.0000 INF",
            "issuer (inficoinio) balance incorrect"
        )


    def tearDown(self):
        pass

    @classmethod
    def tearDownClass(cls):
        stop()

if __name__ == "__main__":
    unittest.main()
