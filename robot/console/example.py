import time

counter = 1
while counter < 100:
    print(f"sample line {counter}", flush=True)
    counter += 1
    time.sleep(0.1)
