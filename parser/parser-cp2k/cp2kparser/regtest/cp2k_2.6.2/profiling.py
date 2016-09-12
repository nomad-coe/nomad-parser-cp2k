import cProfile
import pstats
from run_tests import get_results


def profile_energy_force():
    """Used to profile the CPU usage in parsing RUN_TYPE ENERGY_FORCE.
    """
    profile = cProfile.Profile()
    profile.run('get_results("energy_force", "section_run")')
    stats = pstats.Stats(profile)
    stats.strip_dirs()
    stats.sort_stats("cumulative")
    stats.print_stats(30)

if __name__ == "__main__":
    profile_energy_force()
