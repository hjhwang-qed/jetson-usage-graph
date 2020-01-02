import re
import subprocess as sp
from threading import Thread


class DeviceUsage(object):

    def __init__(self, len=40, max_range=100, is_diff=False):
        self.len = len
        self.is_diff = is_diff
        self.min_range = 0
        self.max_range = max_range
        self.init_usage = 0
        self.min_value = max_range
        self.max_value = 0
        self.avg_value = 0
        self.current_value = 0
        self.current_usages = list()

    def set_init_usage(self, usage):
        if self.is_diff:
            self.init_usage = usage

    def put(self, usage):
        self.current_value = max(usage - self.init_usage, 0)
        self.current_usages.append(self.current_value)
        if len(self.current_usages) > self.len:
            self.current_usages = self.current_usages[-self.len:]

        if self.min_value > self.current_value:
            self.min_value = self.current_value
        if self.max_value < self.current_value:
            self.max_value = self.current_value

        self.avg_value = sum(self.current_usages)/len(self.current_usages)


class TegrastatsParser(object):

    def __init__(self):
        self.ram_re = re.compile(r'RAM ([0-9]+)\/([0-9]+)[KMG]B')
        self.cpus_re = re.compile(r'CPU \[(\S+)\]')
        self.cpu_re = re.compile(r'([0-9]+)%')
        self.gpu_re = re.compile(r'GR3D_FREQ ([0-9]+)%')

    def get_stats(self, text):
        return self._get_ram(text), self._get_cpus(text), self._get_gpu(text)

    def _get_ram(self, text):
        match = self.ram_re.search(text)
        if match:
            return {'use': int(match.group(1)), 'max': int(match.group(2))}
        else:
            return None

    def _get_cpus(self, text):
        num_cpu = 0.0
        cpu_usage = 0

        match = self.cpus_re.search(text)
        if match:
            cpus_list = match.group(1).split(',')
            for cpu_str in cpus_list:
                if cpu_str != 'off':
                    match = self.cpu_re.search(cpu_str)
                    if match:
                        num_cpu += 1.0
                        cpu_usage += int(match.group(1))
        if num_cpu > 0:
            return {'use': cpu_usage/num_cpu, 'max': 100}
        else:
            return None

    def _get_gpu(self, text):
        match = self.gpu_re.search(text)
        if match:
            return {'use': int(match.group(1)), 'max': 100}
        else:
            return None


class TegrastatsProcess(Thread):

    def __init__(self, path='/usr/bin/tegrastats', interval=100):
        Thread.__init__(self)
        self.parser = TegrastatsParser()
        self.path = path
        self.interval = interval
        self.tegrastats = None
        self.ram_usage = {}
        self.cpu_usage = {}
        self.gpu_usage = {}

    def run(self):
        try:
            while self.tegrastats.poll() is None:
                out = self.tegrastats.stdout
                if out is not None:
                    line = out.readline()
                    tegrastats_data = line.decode("utf-8")
                    self.ram_usage, self.cpu_usage, self.gpu_usage = self.parser.get_stats(tegrastats_data)
        except:
            print("Exit")

    def open(self):
        try:
            self.tegrastats = sp.Popen([self.path, '--interval', str(self.interval)], stdout=sp.PIPE)
            self.daemon = True
            self.start()
            return True
        except:
            return False

    def close(self):
        if self.tegrastats is not None:
            self.tegrastats.kill()
            return True
        else:
            return False

    def get(self, type=None):
        if type == 'CPU':
            return self.cpu_usage
        elif type == 'GPU':
            return self.gpu_usage
        elif type == 'RAM':
            return self.ram_usage
        else:
            return self.ram_usage, self.cpu_usage, self.gpu_usage

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
