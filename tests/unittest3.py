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
        SCENARIO('''
        Test the poly persist and update functionality of infiniverse contract
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

    def test_01_persistpoly(self):
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

        COMMENT('''
        Persist the polygon on the land
        ''')
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

        # get table data
        persistent = infiniverse.table("persistent", infiniverse)
        poly = infiniverse.table("poly", infiniverse)

        COMMENT('''
        Check the poly and persistent tables
        ''')
        self.assertEqual(
            poly.json["rows"][0]["user"], "alice",
            "alice is not the owner of polygon"
        )

        self.assertEqual(
            poly.json["rows"][0]["poly_id"], poly_id,
            "poly_id does not match"
        )

        self.assertEqual(
            persistent.json["rows"][0]["asset_id"], poly.json["rows"][0]["id"],
            "asset_id in table persist does not match with id in table poly"
        )

        self.assertEqual(
            persistent.json["rows"][0]["land_id"], land_id,
            "land id does not match"
        )

    def test_02_updatepersis(self):
        persistent_id = 0
        land_id = 0

        # position vectors
        pos_x = 0.5
        pos_y = 0
        pos_z = 0.2

        # orientation vectors
        ori_x = 0
        ori_y = 0
        ori_z = 90 # degrees

        # scale vectors
        sca_x = 0.3
        sca_y = 0.25
        sca_z = 0.3

        COMMENT('''
        Update the poition, orientation and scale vectors of the persisted polygon
        ''')
        infiniverse.push_action(
            "updatepersis",
            {
                "persistent_id": persistent_id,
                "land_id": land_id,
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

        # get table data
        persistent = infiniverse.table("persistent", infiniverse)
        poly = infiniverse.table("poly", infiniverse)

        self.assertEqual(
            persistent.json["rows"][0]["id"], 0,
            "persistent id does not match"
        )

        # # assert position vectors
        # self.assertEqual(
        #     persistent.json["rows"][0]["position"]["x"], pos_x,
        #     "poistion x_coordinate does not match"
        # )

        # self.assertEqual(
        #     persistent.json["rows"][0]["position"]["y"], pos_y,
        #     "poistion y_coordinate does not match"
        # )

        # self.assertEqual(
        #     persistent.json["rows"][0]["position"]["z"], pos_z,
        #     "poistion z_coordinate does not match"
        # )

        # # assert orientation vectors
        # self.assertEqual(
        #     persistent.json["rows"][0]["orientation"]["x"], ori_x,
        #     "orientation x_coordinate does not match"
        # )

        # self.assertEqual(
        #     persistent.json["rows"][0]["orientation"]["y"], ori_y,
        #     "orientation y_coordinate does not match"
        # )

        # self.assertEqual(
        #     persistent.json["rows"][0]["orientation"]["z"], ori_z,
        #     "orientation z_coordinate does not match"
        # )

        # # assert scale vectors
        # self.assertEqual(
        #     persistent.json["rows"][0]["scale"]["x"], sca_x,
        #     "scale x_coordinate does not match"
        # )

        # self.assertEqual(
        #     persistent.json["rows"][0]["scale"]["y"], sca_y,
        #     "scale y_coordinate does not match"
        # )

        # self.assertEqual(
        #     persistent.json["rows"][0]["scale"]["z"], sca_z,
        #     "scale z_coordinate does not match"
        # )

    def test_03_deletepersis(self):
        persistent_id = 0

        COMMENT('''
        Delete persistent polygon
        ''')
        infiniverse.push_action(
            "deletepersis",
            {
                "persistent_id": persistent_id
            },
            [alice]
        )

        # get table data
        persistent = infiniverse.table("persistent", infiniverse)
        poly = infiniverse.table("poly", infiniverse)

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @classmethod
    def tearDownClass(cls):
        stop()


if __name__ == "__main__":
    unittest.main()
