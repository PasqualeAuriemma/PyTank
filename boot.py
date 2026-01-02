# This file is executed on every boot (including wake-boot from deepsleep)
import esp
import gc

# Disable OS debug output to keep the console clean
esp.osdebug(None)

# Run garbage collection to reclaim memory
gc.collect()

print("Boot complete. Memory free:", gc.mem_free())