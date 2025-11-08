import lgpio
import time

class HX711:
    def __init__(self, dout_pin, pd_sck_pin, gain=128):
        self.PD_SCK = pd_sck_pin
        self.DOUT = dout_pin

        self.h = lgpio.gpiochip_open(0)  # Mở GPIO chip 0
        lgpio.gpio_claim_output(self.h, self.PD_SCK)
        lgpio.gpio_claim_input(self.h, self.DOUT)

        self.GAIN = 0
        self.OFFSET = 0
        self.SCALE = 1

        self.set_gain(gain)

    def set_gain(self, gain):
        if gain == 128:
            self.GAIN = 1
        elif gain == 64:
            self.GAIN = 3
        elif gain == 32:
            self.GAIN = 2
        lgpio.gpio_write(self.h, self.PD_SCK, 0)
        self.read_raw()

    def is_ready(self):
        return lgpio.gpio_read(self.h, self.DOUT) == 0

    def read_raw(self):
        while not self.is_ready():
            pass  # Đợi DOUT xuống LOW (có dữ liệu sẵn)

        count = 0
        for _ in range(24):
            lgpio.gpio_write(self.h, self.PD_SCK, 1)
            count = count << 1
            lgpio.gpio_write(self.h, self.PD_SCK, 0)
            if lgpio.gpio_read(self.h, self.DOUT):
                count += 1

        for _ in range(self.GAIN):
            lgpio.gpio_write(self.h, self.PD_SCK, 1)
            lgpio.gpio_write(self.h, self.PD_SCK, 0)

        if count & 0x800000:
            count |= ~0xffffff
        return count

    def read_average(self, times=10):
        sum = 0
        for _ in range(times):
            sum += self.read_raw()
        return sum / times

    def tare(self, times=15):
        print("Taring... Remove weight")
        time.sleep(2)
        self.OFFSET = self.read_average(times)
        print(f"Tare complete. OFFSET = {self.OFFSET}")

    def get_weight(self, times=5):
        value = self.read_average(times) - self.OFFSET
        return value / self.SCALE

    def set_scale(self, scale):
        self.SCALE = scale

    def cleanup(self):
        lgpio.gpiochip_close(self.h)
