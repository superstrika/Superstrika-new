import robot.consts.data
from robot import hunter, keeper

if __name__ == "__main__":
    if robot.consts.data.SELF_IS_HUNTER:
        rob = hunter.Hunt()
        rob.hunt()
    else:
        rob = keeper.Keeper()
        rob.keep()