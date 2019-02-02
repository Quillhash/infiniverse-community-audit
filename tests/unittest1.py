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
        Test the deposit functionality of infiniverse contract
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


    def setUp(self):
        pass

    def test_01_openDeposit(self):
        COMMENT('''
            Opening a deposit account for alice
        ''')
        infiniverse.push_action(
            "opendeposit",
            {
                "owner": alice
            },
            [alice]
        )

        # check the deposits table
        deposits = infiniverse.table("deposit", infiniverse)

        COMMENT('''
            Checking if account name is alice and has 0.0000 INF tokens
        ''')
        self.assertEqual(
            deposits.json["rows"][0]["owner"], "alice",
            "Depositor is not alice"
        )

        self.assertEqual(
            deposits.json["rows"][0]["balance"], "0.0000 INF",
            "alice have non zero balance"
        )

    def test_02_handleDeposit(self):
        COMMENT('''
            Deposit funds to the infiniverse via token contract
        ''')
        infinicoinio.push_action(
            "transfer",
            {
                "from": alice,
                "to": infiniverse,
                "quantity": "100.0000 INF",
                "memo": "Depositing 100 INF to infiniverse contract"
            },
            [alice]
        )

        # get tables data
        alice_account = infinicoinio.table("accounts", alice)
        inf_account = infinicoinio.table("accounts", infiniverse)
        deposits = infiniverse.table("deposit", infiniverse)

        COMMENT('''
            Check accounts table in token contract and deposits in infiniverse contract
        ''')
        self.assertEqual(
            alice_account.json["rows"][0]["balance"], "900.0000 INF",
            "Balances for alice before and after depositing are inconsistent"
        )

        self.assertEqual(
            inf_account.json["rows"][0]["balance"], "100.0000 INF",
            "Balances for infiniverse before and after depositing are inconsistent"
        )

        self.assertEqual(
            deposits.json["rows"][0]["owner"], "alice",
            "alice account in deposists was not found"
        )

        self.assertEqual(
            deposits.json["rows"][0]["balance"], "100.0000 INF",
            "aclice does not have 100 INF in deposits account"
        )

    def test_03_closeDeposit(self):
        COMMENT('''
            Close the deposit account of alice
        ''')
        infiniverse.push_action(
            "closedeposit",
            {
                "owner": alice
            },
            [infiniverse]
        )

        # get tables data
        alice_account = infinicoinio.table("accounts", alice)
        inf_account = infinicoinio.table("accounts", infiniverse)
        deposits = infiniverse.table("deposit", infiniverse)

        COMMENT('''
        Check accounts and balances
        ''')
        self.assertEqual(
            alice_account.json["rows"][0]["balance"], "1000.0000 INF",
            "Refund not provided to Alice"
        )

        self.assertEqual(
            inf_account.json["rows"][0]["balance"], "0.0000 INF",
            "Refund not deducted from infiniverse account"
        )

        self.assertEqual(
            len(deposits.json["rows"]), 0,
            "Alice account was not removed from the deposits"
        )

    def tearDown(self):
        pass

    @classmethod
    def tearDownClass(cls):
        stop()

if __name__ == "__main__":
    unittest.main()
