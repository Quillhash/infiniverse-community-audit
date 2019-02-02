import sys
from eosfactory.eosf import *

verbosity([Verbosity.INFO, Verbosity.OUT, Verbosity.DEBUG])

CONTRACT_WORKSPACE = sys.path[0] + "/../"
TOKEN_CONTRACT_WORKSPACE = sys.path[0] + "/../../infinicoin/"


def test():
    SCENARIO('''
    Test the opening deposit functionality of infiniverse contract
    ''')
    reset()
    create_master_account("eosio")

    ########################################################################################################
    COMMENT('''
    Create test accounts:
    ''')

    # test accounts and accounts where the smart contracts will be hosted
    create_account("alice", eosio, account_name="alice")
    create_account("infiniverse", eosio, account_name="infiniverse")
    create_account("infinicoinio", eosio, account_name="infinicoinio")
    create_account("hacker", eosio, account_name="hacker")

    ########################################################################################################
    COMMENT('''
    Build and deploy token contract:
    ''')

    token_contract = Contract(infinicoinio, TOKEN_CONTRACT_WORKSPACE)
    token_contract.build(force=True)
    token_contract.deploy()

    ########################################################################################################
    COMMENT('''
    Build and deploy infiniverse contract:
    ''')

    contract = Contract(infiniverse, CONTRACT_WORKSPACE)
    contract.build(force=True)
    contract.deploy()

    ########################################################################################################
    COMMENT('''
    Create INF tokens 
    ''')

    # Assumption : Making infinicoinio account as the same as the issuer
    token_contract.push_action(
        "create",
        {
            "issuer": infinicoinio,
            "maximum_supply": "1000000000.0000 INF"
        },
        [infinicoinio]
    )

    ########################################################################################################
    COMMENT('''
    Set eosio.code permission to the infiniverse contract
    ''')

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

    ########################################################################################################
    COMMENT('''
    Issue INF coins to alice 
    ''')

    token_contract.push_action(
        "issue",
        {
            "to": alice,
            "quantity": "1000.0000 INF",
            "memo": "Issued 1000 INF to alice"
        },
        [infinicoinio]
    )

    ########################################################################################################
    COMMENT('''
    Table for infinicoinio contract
    ''')

    token_contract.table("accounts", alice)

    ########################################################################################################
    # COMMENT('''
    # Try to transfer money without opening a deposit
    # ''')

    # token_contract.push_action(
    #     "transfer",
    #     {
    #         "from": alice,
    #         "to": infiniverse,
    #         "quantity": "100.0000 INF",
    #         "memo": "Deposit 100 INF to infiniverse contract"
    #     },
    #     [alice]
    # )

    ########################################################################################################
    # COMMENT('''
    # Check table of the infiniverse contract 
    # ''')

    # infiniverse.table("deposit", infiniverse)

    ########################################################################################################
    COMMENT('''
    Open a deposit for alice in infiniverse
    ''')

    contract.push_action(
        "opendeposit",
        {
            "owner": alice
        },
        [alice]
    )

    ########################################################################################################
    COMMENT('''
    Deposits table of infiniverse contract
    ''')

    contract.table("deposit", infiniverse)

    ########################################################################################################
    COMMENT('''
    Transfer INF tokens from alice to smart contract
    ''')

    token_contract.push_action(
        "transfer",
        {
            "from": alice,
            "to": infiniverse,
            "quantity": "100.0000 INF",
            "memo": "Depositing 100 INF to infiniverse contract"
        },
        [alice]
    )

    ########################################################################################################
    COMMENT('''
    Deposits table of infiniverse contract
    ''')

    contract.table("deposit", infiniverse)

    ########################################################################################################
    COMMENT('''
    Table for infinicoinio contract
    ''')

    token_contract.table("accounts", alice)
    
    stop()


if __name__ == "__main__":
    test()
