# import robot.consts.data
# from robot import hunter, keeper
import robot.calibration.motor_identification as mot

# if __name__ == "__main__":
#     if robot.consts.data.SELF_IS_HUNTER:
#         rob = hunter.Hunt()
#         rob.hunt()
#     else:
#         rob = keeper.Keeper()
#         rob.keep()

mot.main()