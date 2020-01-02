import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque
from threading import Thread

from get_stats import DeviceUsage, TegrastatsProcess


class UsageGraph(object):

    def __init__(self, index, type, process=None, usage=None):
        self.type = type
        self.process = process
        self.usage = usage
        self.ax = plt.subplot2grid((5, 1), (index*2, 0), rowspan=1, colspan=1)
        self.y_list = deque([0] * 240)
        self.x_list = deque(np.linspace(60, 0, num=240))
        self.line, = self.ax.plot([], [])
        self.fill_lines = 0
        self.title = self.ax.text(0.01, 0.9, '', transform=self.ax.transAxes)

    def init_graph(self):
        self.ax.set_xlim(60, 0)
        self.ax.set_ylim(-5, self.usage.max_range + 5)
        self.ax.set_title(f'{self.type} History')
        self.ax.set_ylabel(f'{self.type} Usage')
        self.ax.set_xlabel('Seconds')
        self.ax.grid(color='gray', linestyle='dotted', linewidth=1)

        self.line.set_data([], [])
        self.fill_lines = self.ax.fill_between(self.line.get_xdata(), 50, 0)
        self.title.set_text('')

        return [self.line] + [self.fill_lines] + [self.title]

    def update_graph(self, frame):
        usage = self.process.get(type=self.type)
        self.usage.put(usage['use'])
        self.y_list.popleft()
        self.y_list.append(self.usage.current_value)
        self.line.set_data(self.x_list, self.y_list)
        self.fill_lines.remove()
        self.fill_lines = self.ax.fill_between(self.x_list, 0, self.y_list, facecolor='cyan', alpha=0.50)
        self.title.set_text(f'Min: {self.usage.min_value:.1f} | Max: {self.usage.max_value:.1f} | Avg: {self.usage.avg_value:.1f}')

        return [self.line] + [self.fill_lines] + [self.title]


class VisualizationStats(Thread):

    def __init__(self, is_diff=False):
        Thread.__init__(self)
        self.fig = plt.figure(figsize=(6, 9))
        plt.subplots_adjust(top=0.9, bottom=0.1)

        self.process = TegrastatsProcess()

        # init process and usage
        self.process.open()
        ram_usage = {}
        cpu_usage = {}
        gpu_usage = {}
        while len(ram_usage) == 0 or len(cpu_usage) == 0 or len(gpu_usage) == 0:
            ram_usage, cpu_usage, gpu_usage = self.process.get()
        self.cpu_usage = DeviceUsage(max_range=cpu_usage['max'], is_diff=is_diff)
        self.gpu_usage = DeviceUsage(max_range=gpu_usage['max'], is_diff=is_diff)
        self.ram_usage = DeviceUsage(max_range=ram_usage['max'], is_diff=is_diff)
        self.cpu_usage.set_init_usage(cpu_usage['use'])
        self.gpu_usage.set_init_usage(gpu_usage['use'])
        self.ram_usage.set_init_usage(ram_usage['use'])

        self.cpu_graph = UsageGraph(0, 'CPU', self.process, self.cpu_usage)
        self.gpu_graph = UsageGraph(1, 'GPU', self.process, self.gpu_usage)
        self.ram_graph = UsageGraph(2, 'RAM', self.process, self.ram_usage)

    def run(self):
        animation = FuncAnimation(self.fig, self.cpu_graph.update_graph, frames=None,
                                  init_func=self.cpu_graph.init_graph, interval=250, blit=True)
        animation = FuncAnimation(self.fig, self.gpu_graph.update_graph, frames=None,
                                  init_func=self.gpu_graph.init_graph, interval=250, blit=True)
        animation = FuncAnimation(self.fig, self.ram_graph.update_graph, frames=None,
                                  init_func=self.ram_graph.init_graph, interval=250, blit=True)
        plt.show()

    def open(self):
        try:
            self.start()
            return True
        except:
            return False

