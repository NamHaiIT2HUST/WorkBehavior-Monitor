import time
import csv
from hx711 import HX711

hx = HX711(dout_pin=5, pd_sck_pin=6)  # Kết nối DT -> GPIO5, SCK -> GPIO6
hx.set_scale(1000.0)  # Giá trị SCALE, sẽ calibrate sau
hx.tare()

with open('logs/loadcell_data.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Timestamp', 'Weight (grams)'])

    print("Logging... Ctrl+C to stop")
    try:
        while True:
            weight = hx.get_weight(10)
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"{timestamp} -- {weight:.2f} grams")

            writer.writerow([timestamp, f"{weight:.2f}"])
            file.flush()
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        hx.cleanup()
