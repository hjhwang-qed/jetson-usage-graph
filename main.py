import argparse

from visualize import VisualizationStats


def main(args):
    v = VisualizationStats(args.view_diff)
    v.open()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Tegrastats Graph')
    parser.add_argument("--view_diff", action='store_true')
    args = parser.parse_args()
    main(args)
