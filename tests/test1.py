import unittest
import sys

import time

from eosfactory.eosf import *

verbosity([Verbosity.INFO, Verbosity.OUT])

verbosity([Verbosity.INFO, Verbosity.OUT, Verbosity.DEBUG])

CONTRACT_WORKSPACE = sys.path[0] + "/../"
TOKEN_CONTRACT_WORKSPACE = sys.path[0] + "/../infinicoin/"

# utility method to get INF from given amount


def to_inf(amount):
    return str(amount) + ".0000 INF"


def testDOS():
    SCENARIO('''
        Test DOS resilience by spamming multiple poly
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
            "maximum_supply": to_inf(1000000000)
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

    # transfer some funds to alice's account
    token_contract.push_action(
        "issue",
        {
            "to": alice,
            "quantity": to_inf(1000),
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

    # deposit some funds for alice
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

    # register land for alice
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

    #####################################################################################
    # Try to cause out of RAM by persisting many polys

    land_id = 0
    poly_id = "my_ploygon1"

    # position vectors
    pos_x = 0.5
    pos_y = 0
    pos_z = 0.5

    # orientation vectors
    ori_x = 0
    ori_y = 0
    ori_z = 0

    # scale vectors
    sca_x = 0.3
    sca_y = 0.3
    sca_z = 0.3

    # infinite loop
    count = 0
    flag = True
    while True:
        #poly_id = "11111111111"

        time.sleep(1)

        if flag:
            pos_x = 0.4
            flag = True
        else:
            pos_x = 0.5
            flag = False    


        infiniverse.push_action(
            "persistpoly",
            {
                "land_id": land_id,
                "poly_id": poly_id,
                "position": {
                    "x": pos_x,
                    "y": pos_y,
                    "z": pos_z
                },
                "orientation": {
                    "x": ori_x,
                    "y": ori_y,
                    "z": ori_z
                },
                "scale": {
                    "x": sca_x,
                    "y": sca_y,
                    "z": sca_z
                }
            },
            [alice]
        )

        persist = infiniverse.table('persistent', infiniverse)
        print(len(persist.json["rows"]))

        # alice_account = infinicoinio.table("accounts", alice)


if __name__ == "__main__":
    testDOS()
